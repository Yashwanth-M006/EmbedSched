"""
report/markdown_report.py

Generates GitHub-Flavored Markdown reports for EmbedSched findings,
memory map summary, and AUTOSAR Schedulability Analysis.
Renders natively in GitHub Actions Step Summary ($GITHUB_STEP_SUMMARY)
and downloadable artifacts.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from models.finding import Finding
from report.terminal_report import compute_score

GRADE_MAP = [
    (90, 'A'),
    (80, 'B'),
    (70, 'C'),
    (60, 'D'),
    (0,  'F'),
]

def generate_markdown_report(
    findings: List[Finding],
    score: Optional[int] = None,
    memory_regions: Optional[Dict[str, Dict[str, Any]]] = None,
    autosar_data: Optional[Dict[str, Any]] = None,
) -> str:
    """Generate a GitHub-Flavored Markdown report."""
    if score is None:
        score = compute_score(findings)

    grade = 'A'
    for threshold, letter in GRADE_MAP:
        if score >= threshold:
            grade = letter
            break

    criticals = [f for f in findings if f.severity == 'CRITICAL']
    warnings  = [f for f in findings if f.severity == 'WARNING']
    infos     = [f for f in findings if f.severity in ('INFO', 'PASS')]

    md = []
    md.append("# 🛡️ EmbedSched Firmware Schedulability & Safety Report\n")
    md.append(f"**Generated:** `{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}`  ")
    md.append(f"**Overall Health Score:** **`{score}/100`** (Grade: **`{grade}`**)  \n")

    # Status badge/summary table
    status_icon = "🟢 Passed" if score >= 80 else ("🟡 Warning" if score >= 60 else "🔴 Critical Issues")
    md.append("## 1. Executive Summary\n")
    md.append("| Metric | Result | Status |")
    md.append("| :--- | :--- | :--- |")
    md.append(f"| **Overall Health Score** | `{score} / 100` | {status_icon} |")
    md.append(f"| **Critical Findings** | `{len(criticals)}` | {'🔴 Needs Immediate Fix' if criticals else '🟢 None'} |")
    md.append(f"| **Warnings** | `{len(warnings)}` | {'🟡 Review Advised' if warnings else '🟢 None'} |")
    md.append(f"| **Informational Notes** | `{len(infos)}` | ℹ️ In place |")
    md.append("\n---\n")

    # Memory map table if available
    if memory_regions:
        md.append("## 2. Memory Map & Hardware Region Summary\n")
        md.append("| Region | Used (Bytes) | Capacity (Bytes) | Utilization |")
        md.append("| :--- | :--- | :--- | :--- |")
        for reg, data in memory_regions.items():
            used = data.get('used', 0)
            cap = data.get('capacity', 0)
            if cap > 0:
                pct = (used / cap) * 100
                bar = "█" * int(pct / 10) + "░" * (10 - int(pct / 10))
                md.append(f"| **{reg}** | `{used:,}` | `{cap:,}` | `{pct:.1f}%` `{bar}` |")
            else:
                md.append(f"| **{reg}** | `{used:,}` | *Unknown* | — |")
        md.append("\n---\n")

    # AUTOSAR Schedulability Analysis if available
    if autosar_data:
        md.append("## 3. AUTOSAR Schedulability & Response Time Analysis\n")
        md.append(f"**Verdict:** {autosar_data.get('verdict', 'N/A')}  \n")
        
        tasks = autosar_data.get('tasks', [])
        if tasks:
            md.append("| Task Name | Core | Priority | Period (µs) | WCET (µs) | Blocking (µs) | WCRT (µs) | Deadline (µs) | Schedulable? |")
            md.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")
            for t in tasks:
                sched = "✅ YES" if t.get('schedulable', True) else "❌ NO"
                md.append(
                    f"| `{t.get('name')}` | {t.get('core', 0)} | {t.get('priority')} | "
                    f"`{t.get('period')}` | `{t.get('wcet')}` | `{t.get('blocking', 0)}` | "
                    f"`{t.get('wcrt')}` | `{t.get('deadline')}` | {sched} |"
                )
            md.append("")

        if 'confidence_note' in autosar_data:
            md.append(f"> **Confidence Level:**\n> {autosar_data['confidence_note']}\n")
        md.append("---\n")

    # Findings section
    md.append("## 4. Audit Findings & Concurrency Hazards\n")
    if not criticals and not warnings and not infos:
        md.append("🎉 *No issues or hazards detected. Firmware conforms to real-time safety constraints.*\n")
    else:
        if criticals:
            md.append("### 🔴 Critical Findings\n")
            for f in criticals:
                tag = f" `[{f.tag}]`" if hasattr(f, 'tag') and f.tag else ""
                md.append(f"#### ⚠️ `{f.rule}`{tag}")
                for line in f.message.splitlines():
                    md.append(f"- {line}")
                if f.fix:
                    md.append(f"\n> **Remediation:** {f.fix}\n")
                md.append("")

        if warnings:
            md.append("### 🟡 Warnings\n")
            for f in warnings:
                tag = f" `[{f.tag}]`" if hasattr(f, 'tag') and f.tag else ""
                md.append(f"#### ⚠️ `{f.rule}`{tag}")
                for line in f.message.splitlines():
                    md.append(f"- {line}")
                if f.fix:
                    md.append(f"\n> **Remediation:** {f.fix}\n")
                md.append("")

        if infos:
            md.append("### ℹ️ Informational / Optimization Notices\n")
            for f in infos:
                md.append(f"- **`{f.rule}`**: {f.message.strip()}")
            md.append("")

    return "\n".join(md)


def write_markdown_report(
    path: str,
    findings: List[Finding],
    score: Optional[int] = None,
    memory_regions: Optional[Dict[str, Dict[str, Any]]] = None,
    autosar_data: Optional[Dict[str, Any]] = None,
) -> None:
    """Write markdown report to file."""
    content = generate_markdown_report(findings, score, memory_regions, autosar_data)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
