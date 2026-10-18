from typing import List, Dict
from models.finding import Finding
from models.symbol import Symbol

def check_dma_alignment(symbols: List[Symbol], chip_regions: Dict = None, chip: Dict = None) -> List[Finding]:
    findings = []
    
    if chip_regions is None:
        chip_regions = {}
    if chip is None:
        chip = {}
        
    for sym in symbols:
        name_lower = sym.name.lower()
        if '.dma' in sym.section.lower() or sym.section.lower() == 'dma':
            # Skip if it's an end symbol, size symbol, or an ISR handler
            if name_lower.endswith('_end') or name_lower.endswith('_size') or 'handler' in name_lower or name_lower.endswith('_isr'):
                continue
                
            if sym.address % 32 != 0:
                offset = sym.address % 32
                findings.append(Finding(
                    rule="unaligned_dma_buffer",
                    severity="INFO",
                    tag="[STATIC]",
                    message=f"{sym.name} at 0x{sym.address:x} - {offset}-byte aligned, requires 32-byte.\n  D-cache maintenance will affect adjacent memory.",
                    fix="__attribute__((aligned(32)))"
                ))
            else:
                # Find region
                region_name = "Unknown"
                dma_accessible = "UNKNOWN"
                for r_name, r_data in chip_regions.items():
                    r_origin = r_data.get('origin', 0)
                    r_size = r_data.get('size_kb', 0) * 1024
                    if r_origin <= sym.address < r_origin + r_size:
                        region_name = r_name
                        dma_accessible = "YES" if r_data.get('dma_accessible', False) else "NO"
                        break
                        
                if region_name == 'SRAM2' and chip_regions.get('SRAM2', {}).get('bus_port') == 'AHB_S2':
                    findings.append(Finding(
                        rule="dma_buffers_in_sram2_correct",
                        severity="INFO",
                        tag="[STATIC]",
                        message=(
                            f"{sym.name}: 0x{sym.address:08X} ({region_name}, AHB_S2) - {sym.size} bytes, 32B aligned\n"
                            f"  {sym.name} is correctly placed in SRAM2 (AHB_S2).\n"
                            f"  CPU uses SRAM1 (AHB_S1) - separate bus matrix port -> zero contention."
                        ),
                        fix="No action needed."
                    ))
                else:
                    findings.append(Finding(
                        rule="dma_buffers_correctly_placed",
                        severity="INFO",
                        tag="[STATIC]",
                        message=(
                            f"DMA buffer section {sym.section} / {sym.name}: {region_name} at 0x{sym.address:08X}, {sym.size} bytes.\n"
                            f"  DMA-accessible: {dma_accessible}\n"
                            f"  Alignment: 32-byte aligned \u2014 correct for D-cache maintenance.\n"
                            f"  Note: STM32F407 M4 has no D-cache; alignment is forward-compatible."
                        ),
                        fix="No action needed."
                    ))
                
    return findings
