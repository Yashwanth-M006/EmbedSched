from dataclasses import dataclass
from typing import Optional

@dataclass
class Finding:
    rule: str
    severity: str    # "CRITICAL", "WARNING", "INFO"
    tag: str         # "[STATIC]", "[CALCULATED]", "[SIMULATED]", "[HEURISTIC]"
    message: str
    fix: Optional[str] = None

    def __str__(self) -> str:
        s = f"[{self.severity}] {self.tag} {self.rule}: {self.message}"
        if self.fix:
            s += f"\n  Suggested Fix: {self.fix}"
        return s
