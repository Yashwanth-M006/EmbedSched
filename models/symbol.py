from dataclasses import dataclass

@dataclass
class Symbol:
    name: str
    address: int
    size: int
    section: str
    object_file: str
