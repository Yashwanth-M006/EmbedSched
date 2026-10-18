from dataclasses import dataclass
from typing import Optional

@dataclass
class Finding:
    rule: str
    severity: str    # "CRITICAL", "WARNING", "INFO"
    tag: str         # "[STATIC]", "[CALCULATED]", "[SIMULATED]", "[HEURISTIC]"
    message: str
    fix: Optional[str] = None
