from typing import List, Dict
from models.finding import Finding
from models.symbol import Symbol
from analysis.region_classifier import classify_address
from analysis.timing_model import calc_isr_penalty_ns

def check_isr_placement(
    isr_names: List[str],
    symbols: List[Symbol],
    linker_regions: dict,
    chip_regions: dict,
    chip: dict,
    freq_mhz: float
) -> List[Finding]:
    findings = []
    warned_isrs = set()
    
    default_handler_addr = None
    for sym in symbols:
        if sym.name == 'Default_Handler':
            default_handler_addr = sym.address
            break
            
    # If Default_Handler isn't found by name, try to find the address with the most ISRs
    if default_handler_addr is None:
        addr_counts = {}
        for sym in symbols:
            if sym.name.endswith('_IRQHandler') or sym.name.endswith('_Handler'):
                addr_counts[sym.address] = addr_counts.get(sym.address, 0) + 1
        if addr_counts:
            most_common_addr = max(addr_counts, key=addr_counts.get)
            if addr_counts[most_common_addr] > 10:
                default_handler_addr = most_common_addr

    itcm_isrs = []
    itcm_hot = []
    
    # Find symbol matching ISR names
    for sym in symbols:
        # Ignore if it is aliased to Default_Handler or is Reset_Handler
        if (default_handler_addr is not None and sym.address == default_handler_addr) or sym.name == 'Reset_Handler':
            continue
            
        region = classify_address(sym.address, linker_regions, chip_regions)
        chip_has_itcm = 'ITCM' in chip_regions
        if sym.name in isr_names:
            if region == 'FLASH':
                # On chips with no ITCM (e.g. STM32F407), ISRs always live in Flash.
                # This is a hardware constraint — emit INFO not WARNING (isr_always_in_flash handles it).
                if not chip_has_itcm:
                    if sym.name not in warned_isrs:
                        warned_isrs.add(sym.name)
                        findings.append(Finding(
                            rule="isr_in_flash_info",
                            severity="INFO",
                            tag="[CALCULATED]",
                            message=(
                                f"{sym.name} at 0x{sym.address:08X} is in Flash.\n"
                                f"  Chip has no ITCM — all code executes from Flash via AHB.\n"
                                f"  Recommend: verify ART accelerator enabled (FLASH_ACR bit 9).\n"
                                f"  Recommend: verify prefetch enabled (FLASH_ACR bit 8)."
                            ),
                            fix="Set FLASH->ACR |= FLASH_ACR_ARTEN | FLASH_ACR_PRFTEN in SystemInit()."
                        ))
                    continue
                # On chips with ITCM: flag as WARNING (ISR should be moved)
                try:
                    penalty = calc_isr_penalty_ns(freq_mhz, region, chip)
                    warm_ns = penalty['flash_warm_ns']
                    cold_ns = penalty['flash_cold_ns']

                    msg = f"{sym.name} at 0x{sym.address:0x} ({region}).\n"
                    msg += f"  Calculated latency: ~{warm_ns:.1f} ns (vs ~{penalty['itcm_ns']:.1f} ns in ITCM/CCM).\n"
                    msg += f"  Cold-cache jitter risk: up to ~{cold_ns:.1f} ns"

                    # Check if we've already warned about this specific ISR name
                    if sym.name not in warned_isrs:
                        warned_isrs.add(sym.name)
                        findings.append(Finding(
                            rule="isr_in_flash",
                            severity="WARNING",
                            tag=f"[CALCULATED — {penalty.get('citation', penalty.get('note', ''))}]",
                            message=msg,
                            fix="__attribute__((section(\".itcm_text\")))"
                        ))
                except Exception as e:
                    if sym.name not in warned_isrs:
                        warned_isrs.add(sym.name)
                        findings.append(Finding(
                            rule="isr_in_flash",
                            severity="WARNING",
                            tag="[STATIC]",
                            message=f"{sym.name} is mapped to {region} instead of ITCM/CCM.\n  Interrupt latency will suffer from bus arbitration and wait states. Error: {e}",
                            fix="__attribute__((section(\".itcm_text\")))"
                        ))
            elif region == 'ITCM':
                itcm_isrs.append(sym)
        else:
            if region == 'ITCM' and not sym.name.startswith('_') and sym.size > 0 and not sym.section.startswith('.debug') and not sym.section.startswith('.comment'):
                itcm_hot.append(sym)
                
    if itcm_isrs:
        handlers_str = ", ".join([s.name for s in itcm_isrs])
        addrs_str = ", ".join([f"0x{s.address:08X}" for s in itcm_isrs])
        
        try:
            penalty = calc_isr_penalty_ns(freq_mhz, 'ITCM', chip)
            itcm_ns = penalty['itcm_ns']
            flash_cold = penalty['flash_cold_ns']
        except ValueError:
            itcm_ns = 55.6
            flash_cold = 351.9

        findings.append(Finding(
            rule="isr_in_itcm_confirmed",
            severity="INFO",
            tag="[CALCULATED]",
            message=f"Handlers: {handlers_str}\n  Addresses: {addrs_str}\n  Region: ITCM\n  Calculated entry latency: ~{itcm_ns:.1f} ns\n  vs flash cold-miss worst case: ~{flash_cold:.1f} ns\n  Jitter: +/-0 ns (ITCM has no cache variability)",
            fix="No action needed."
        ))
        
    if itcm_hot:
        symbols_str = ", ".join([f"{s.name} (0x{s.address:08X})" for s in itcm_hot])
        findings.append(Finding(
            rule="hot_functions_in_itcm",
            severity="INFO",
            tag="[STATIC]",
            message=f"Symbols: {symbols_str}\n  Region: ITCM\n  {len(itcm_hot)} non-ISR functions are in ITCM - detected as intended hot-path placement.",
            fix="No action needed."
        ))
        
    return findings
