"""
analysis/jitter_analyzer.py — Start-Time and Release Jitter Analysis Engine

Implements formal jitter analysis over discrete-event scheduler simulation results:
  Evaluates execution start-time deviation from ideal periodic release (k * T_i)
  for every activation across the simulated hyperperiod.

Computes:
  - Maximum start-time jitter: J_max = max_k |start(k) - k * T_i|
  - Mean start-time jitter: J_mean = (1/K) * sum_k |start(k) - k * T_i|
  - Relative jitter ratio: rho = J_max / T_i
  - Engineering safety assessment grade: EXCELLENT / GOOD / MODERATE / HIGH
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from models.autosar_task import AutosarTask
from analysis.scheduler_sim import SimulationResult


@dataclass
class TaskJitterMetric:
    """Quantitative jitter metrics for a single AUTOSAR task."""
    task_name: str
    period_us: float
    activations_count: int
    max_jitter_us: float
    mean_jitter_us: float
    jitter_ratio_pct: float
    assessment_grade: str
    assessment_detail: str


@dataclass
class JitterAnalysisReport:
    """Comprehensive jitter evaluation across all tasks in the system."""
    tasks: Dict[str, TaskJitterMetric] = field(default_factory=dict)
    highest_jitter_task: Optional[str] = None
    has_high_jitter: bool = False

    def get(self, task_name: str) -> Optional[TaskJitterMetric]:
        return self.tasks.get(task_name)


def compute_jitter_analysis(
    sim: SimulationResult,
    tasks: List[AutosarTask],
) -> JitterAnalysisReport:
    """
    Computes rigorous start-time jitter metrics for all scheduled periodic tasks.

    Args:
        sim: Discrete-event scheduler simulation result containing activation start times.
        tasks: Full list of AUTOSAR tasks (including periods and WCETs).

    Returns:
        JitterAnalysisReport containing structured metrics and safety assessments.
    """
    report = JitterAnalysisReport()
    task_map: Dict[str, AutosarTask] = {t.name: t for t in tasks}
    start_times_map = getattr(sim, 'task_start_times', None) or getattr(sim, 'start_times', {})

    for task_name, starts in sorted(start_times_map.items()):
        task_obj = task_map.get(task_name)
        if not task_obj or task_obj.period_us <= 0 or not starts:
            continue

        period = task_obj.period_us
        sorted_starts = sorted(starts)

        # Ideal periodic release for activation k is k * period.
        # Under a non-anticipative scheduler, actual_start >= ideal_release.
        jitters: List[float] = []
        for k, actual_start in enumerate(sorted_starts):
            ideal_release = k * period
            drift = max(0.0, actual_start - ideal_release)
            jitters.append(drift)

        if not jitters:
            continue

        max_j = max(jitters)
        mean_j = sum(jitters) / len(jitters)
        ratio_pct = (max_j / period) * 100.0 if period > 0 else 0.0

        # Safety grade classification
        if max_j < period * 0.01:
            grade = "EXCELLENT"
            detail = "EXCELLENT (<1% of period) — negligible phase lag"
        elif max_j < period * 0.05:
            grade = "GOOD"
            detail = "GOOD (<5% of period) — acceptable for standard automotive control"
        elif max_j < period * 0.20:
            grade = "MODERATE"
            detail = "MODERATE (<20% of period) — supervisory or background tasks"
        else:
            grade = "HIGH"
            # Determine if high jitter is an expected consequence of high core utilization
            core_tasks = [
                t for t in tasks
                if getattr(t, 'core_id', 0) == task_obj.core_id and t.period_us > 0
            ]
            core_u = sum(t.wcet_us / t.period_us for t in core_tasks) if core_tasks else 0.0
            all_sched = all(getattr(t, 'schedulable', True) is not False for t in core_tasks)

            if core_u >= 0.75 and all_sched:
                detail = "HIGH (>20% of period — expected at high utilization; monitor control stability)"
            else:
                detail = "HIGH (>20% of period — review priority assignment or preemption threshold)"

        metric = TaskJitterMetric(
            task_name=task_name,
            period_us=period,
            activations_count=len(starts),
            max_jitter_us=round(max_j, 2),
            mean_jitter_us=round(mean_j, 2),
            jitter_ratio_pct=round(ratio_pct, 2),
            assessment_grade=grade,
            assessment_detail=detail,
        )
        report.tasks[task_name] = metric

        if grade == "HIGH":
            report.has_high_jitter = True

    if report.tasks:
        worst_task = max(report.tasks.values(), key=lambda m: m.jitter_ratio_pct)
        report.highest_jitter_task = worst_task.task_name

    return report
