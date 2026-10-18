"""
report/text_report.py

Plain-text file reporter for Firmware Analyzer findings and safety audits.
Formats findings, severity levels, and remediation steps into clean ASCII/UTF-8
text documents without ANSI terminal escape sequences.
"""

from typing import List, Optional
from models.finding import Finding
from report.terminal_report import compute_score, GRADE_MAP


def format_text_report(findings: List[Finding], score: Optional[int] = None) -> str:
    """Format a list of findings into a clean plain-text string."""
    if score is None:
        score = compute_score(findings)

    grade = 'A'
    for threshold, letter in GRADE_MAP:
        if score >= threshold:
            grade = letter
            break

    lines = []
    lines.append("=" * 70)
    lines.append(" FIRMWARE STATIC ANALYSIS & SAFETY AUDIT REPORT")
    lines.append("=" * 70)
    lines.append(f" OVERALL HEALTH SCORE: {score}/100  (Grade: {grade})")
    lines.append("-" * 70)

    criticals = [f for f in findings if f.severity == 'CRITICAL']
    warnings  = [f for f in findings if f.severity == 'WARNING']
    infos     = [f for f in findings if f.severity in ('INFO', 'PASS')]

    lines.append(f" Summary: {len(criticals)} Critical, {len(warnings)} Warning, {len(infos)} Informational")
    lines.append("=" * 70)

    if criticals:
        lines.append("\n[CRITICAL FINDINGS]")
        for f in criticals:
            lines.append(f"  * [{f.rule}] {f.tag if hasattr(f, 'tag') and f.tag else ''}")
            for l in f.message.splitlines():
                lines.append(f"      {l}")
            if f.fix:
                lines.append(f"      Remediation: {f.fix}")
            lines.append("")

    if warnings:
        lines.append("\n[WARNING FINDINGS]")
        for f in warnings:
            lines.append(f"  * [{f.rule}] {f.tag if hasattr(f, 'tag') and f.tag else ''}")
            for l in f.message.splitlines():
                lines.append(f"      {l}")
            if f.fix:
                lines.append(f"      Remediation: {f.fix}")
            lines.append("")

    if infos:
        lines.append("\n[INFORMATIONAL FINDINGS]")
        for f in infos:
            lines.append(f"  * [{f.rule}]")
            for l in f.message.splitlines():
                lines.append(f"      {l}")
            lines.append("")

    lines.append("=" * 70)
    lines.append(" END OF REPORT")
    lines.append("=" * 70)
    return "\n".join(lines)


def write_text_report(path: str, findings: List[Finding], score: Optional[int] = None) -> None:
    """Write the plain-text audit report to a file."""
    content = format_text_report(findings, score)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
