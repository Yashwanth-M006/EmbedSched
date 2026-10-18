from typing import List
from models.finding import Finding

def check_no_itcm_chip(
    isr_names: List[str],
    chip: dict
) -> List[Finding]:
    """
    On chips without ITCM (e.g. STM32F407), ISRs always execute from Flash.
    We should NOT recommend ITCM placement — instead inform about ART accelerator.
    """
    findings = []
    chip_regions = chip.get('memory_regions', {})
    has_itcm = 'ITCM' in chip_regions or 'CCM' not in chip_regions  # CCM is M4 equiv
    
    # If no ITCM in memory_regions, chip physically lacks it
    if 'ITCM' not in chip_regions and isr_names:
        analyzer_notes = chip.get('analyzer_notes', {})
        no_itcm_note = analyzer_notes.get('no_itcm', '')
        findings.append(Finding(
            rule="isr_always_in_flash",
            severity="INFO",
            tag="[STATIC]",
            message=(
                f"Chip '{chip.get('name', 'unknown')}' ({chip.get('core', '?')}) has no ITCM.\n"
                "  ISRs ({}) always execute from Flash on this chip.\n"
                "  This is not a bug - it is a hardware constraint.\n"
                "  To minimize ISR latency on this chip:\n"
                "    - Verify ART Accelerator is enabled: FLASH_ACR bit 9 (ARTEN)\n"
                "    - Verify Prefetch Buffer enabled: FLASH_ACR bit 8 (PRFTEN)\n"
                "    - ART eliminates wait states for sequential Flash fetches,\n"
                "      but does NOT eliminate cold-entry jitter on random vector fetch."
            ).format(', '.join(isr_names[:5]) + (' ...' if len(isr_names) > 5 else '')),
            fix="Set FLASH->ACR |= FLASH_ACR_ARTEN | FLASH_ACR_PRFTEN in SystemInit()."
        ))
    
    return findings


def check_stack_in_sram_not_ccm(
    linker_symbols: dict,
    chip: dict,
    chip_regions: dict
) -> List[Finding]:
    """
    On STM32F407: if _estack is in SRAM (0x20000000 range) and CCM exists,
    suggest moving the stack to CCM for DMA isolation.
    """
    findings = []
    estack = linker_symbols.get('_estack', 0)
    if not estack:
        return []
    
    ccm_data = chip_regions.get('CCM', {})
    ccm_origin = ccm_data.get('origin', 0)
    ccm_size = ccm_data.get('size_kb', 0) * 1024
    if not ccm_origin or not ccm_size:
        return []
    
    # Check if estack is NOT in CCM
    in_ccm = ccm_origin <= (estack - 1) < (ccm_origin + ccm_size) if estack > 0 else False
    if in_ccm and estack > 0:
        findings.append(Finding(
            rule="stack_in_ccm_good",
            severity="INFO",
            tag="[STATIC]",
            message=(
                f"Stack placed in CCM (0x{ccm_origin:08x}-0x{ccm_origin+ccm_size:08x}) — correct placement.\n"
                f"  CCM is CPU-only: DMA cannot cause bus contention on stack accesses."
            ),
            fix="No action needed."
        ))
    elif not in_ccm and estack > 0:
        # Is it in SRAM?
        sram_data = chip_regions.get('SRAM1', {})
        sram_origin = sram_data.get('origin', 0)
        sram_top = sram_origin + sram_data.get('size_kb', 0) * 1024
        in_sram = sram_origin <= estack <= sram_top + 0x8000  # generous bound
        
        if in_sram:
            findings.append(Finding(
                rule="stack_in_sram_not_ccm",
                severity="INFO",
                tag="[HEURISTIC]",
                message=(
                    f"Stack top (_estack=0x{estack:08x}) is in SRAM1 (AHB bus, DMA accessible).\n"
                    f"  CCM RAM (0x{ccm_origin:08x}, {ccm_size//1024} KB) is available and is CPU-only:\n"
                    "    - DMA cannot reach CCM -> placing stack there eliminates bus contention\n"
                    "      between stack push/pop and DMA transfers.\n"
                    "    - Zero wait states for stack operations.\n"
                    "    - This is the STM32F407 equivalent of DTCM stack placement on M7."
                ),
                fix="In linker script: _estack = ORIGIN(CCM) + LENGTH(CCM); and map STACK section >CCM."
            ))
    
    return findings
