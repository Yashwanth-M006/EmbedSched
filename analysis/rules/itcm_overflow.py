from typing import List, Dict
from models.finding import Finding
from models.symbol import Symbol
from analysis.region_classifier import classify_address

def check_itcm_overflow(
    symbols: List[Symbol],
    linker_regions: dict,
    chip_regions: dict
) -> List[Finding]:
    findings = []
    
    capacity = 0
    if 'ITCM' in linker_regions:
        capacity = linker_regions['ITCM'].length
    elif 'ITCM' in chip_regions:
        capacity = chip_regions['ITCM'].get('size_kb', 0) * 1024
        
    if capacity == 0:
        return []
        
    usage = 0
    for sym in symbols:
        region = classify_address(sym.address, linker_regions, chip_regions)
        if region == 'ITCM':
            usage += sym.size
            
    if usage >= capacity * 0.9:
        pct = (usage / capacity) * 100
        severity = "CRITICAL" if usage > capacity else "WARNING"
        findings.append(Finding(
            rule="itcm_overflow_risk",
            severity=severity,
            tag="[STATIC]",
            message=f".itcm_text: {usage:,} / {capacity:,} bytes ({pct:.1f}%).\n  Adding handlers may exceed capacity.",
            fix="Remove unnecessary functions from ITCM or increase region size if hardware allows."
        ))
    elif usage > 0:
        pct = (usage / capacity) * 100
        headroom = capacity - usage
        findings.append(Finding(
            rule="itcm_section_budget",
            severity="INFO",
            tag="[STATIC]",
            message=f".itcm_text: {usage:,} bytes used / {capacity:,} bytes capacity ({pct:.1f}%)\n  ITCM section well within budget. Headroom: {headroom:,} bytes.",
            fix="No action needed."
        ))
        
    return findings
