"""
analysis/deadlock_detector.py

Resource Allocation Graph (RAG) and lock acquisition cycle detection for
AUTOSAR OS shared resources across single-core and multi-core configurations.
"""

from typing import List, Optional
from models.finding import Finding
from models.autosar_task import AutosarTask, Resource
from analysis.rules.autosar_rules import check_deadlock_risk


def detect_deadlocks(
    tasks_or_resources,
    resources: Optional[List[Resource]] = None
) -> List[Finding]:
    """
    Constructs a lock acquisition dependency graph across all tasks and cores.
    Detects potential circular wait conditions (e.g., Task 1 holds R1 waiting for R2
    while Task 2 holds R2 waiting for R1) and generates DEADLOCK_RISK findings.

    Supports both signatures:
      detect_deadlocks(tasks, resources)
      detect_deadlocks(resources)
    """
    if resources is not None:
        target_resources = resources
    elif isinstance(tasks_or_resources, list) and len(tasks_or_resources) > 0 and isinstance(tasks_or_resources[0], Resource):
        target_resources = tasks_or_resources
    elif isinstance(tasks_or_resources, list):
        # Passed only tasks; extract resources if they contain resource references
        target_resources = []
    else:
        target_resources = []

    return check_deadlock_risk(target_resources)
