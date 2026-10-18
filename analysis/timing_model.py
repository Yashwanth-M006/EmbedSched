from typing import Dict, Any

def lookup_wait_states(freq_mhz: float, chip: dict) -> int:
    for entry in chip.get('flash_wait_states', []):
        if freq_mhz <= entry['freq_max_mhz']:
            return entry['ws']
    raise ValueError(f"Frequency {freq_mhz} MHz exceeds chip maximum")

def calc_isr_penalty_ns(
    freq_mhz: float,
    handler_region: str,
    chip: dict
) -> Dict[str, Any]:
    """
    Returns dict with itcm_ns, flash_cold_ns, flash_warm_ns,
    and source citation string.
    """
    cycle_ns = 1000.0 / freq_mhz
    hw_entry = chip.get('exception_entry_cycles', 12)
    ws = lookup_wait_states(freq_mhz, chip)
    
    cache = chip.get('cache', {})
    if cache.get('present', False):
        line_words = cache.get('line_bytes', 32) // 4
        miss_penalty = line_words * (ws + 1)
    else:
        # Pre-fetch or simple flash accelerator approximation
        miss_penalty = (ws + 1)

    return {
        'itcm_ns':       hw_entry * cycle_ns,
        'flash_warm_ns': (hw_entry + ws + 1) * cycle_ns,
        'flash_cold_ns': (hw_entry + miss_penalty) * cycle_ns,
        'citation':      f"ARMv7-M ARM Section B1.5.6 ({hw_entry} cy entry) + "
                         f"RM Table ({ws} WS at {freq_mhz} MHz)"
    }
