from typing import Dict
from parsers.ld_parser import MemoryRegion

def classify_address(addr: int, linker_regions: Dict[str, MemoryRegion], chip_regions: Dict[str, dict]) -> str:
    """
    Cross-reference a symbol address against linker-script-derived
    region boundaries. Returns region name or 'UNKNOWN'.
    Priority: use linker script regions first (user intent),
    fall back to chip profile if linker script is incomplete.
    """
    # Try linker script regions first
    for name, region in linker_regions.items():
        if region.origin <= addr < (region.origin + region.length):
            return name
            
    # Fallback to chip profile
    for name, region_data in chip_regions.items():
        origin = region_data.get('origin', 0)
        size_kb = region_data.get('size_kb', 0)
        if origin <= addr < (origin + size_kb * 1024):
            return name
            
    return 'UNKNOWN'
