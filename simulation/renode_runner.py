import os
import subprocess
import bisect
from collections import defaultdict
from typing import Dict

def run_renode_trace(elf_path: str, platform_repl: str, sim_duration_ms: int = 2000) -> str:
    """
    Launches Renode headless, loads ELF, runs for sim_duration_ms,
    captures execution trace to a temp file and returns the path.
    """
    import pathlib
    import tempfile

    temp_dir = tempfile.gettempdir()
    trace_path = os.path.join(temp_dir, f"renode_exec_trace_{os.getpid()}.txt")
    resc_path = os.path.join(temp_dir, f"renode_sim_{os.getpid()}.resc")

    trace_resc = trace_path.replace("\\", "/")
    elf_abs = str(pathlib.Path(elf_path).resolve()).replace("\\", "/")
    repl_abs = str(pathlib.Path(platform_repl).resolve()).replace("\\", "/")

    resc_script = (
        "mach create\n"
        f"machine LoadPlatformDescription @{repl_abs}\n"
        f"sysbus LoadELF @{elf_abs}\n"
        f"cpu CreateExecutionTracing \"trace\" @{trace_resc} PC\n"
        f"emulation RunFor \"{sim_duration_ms}ms\"\n"
        "quit\n"
    )
    with open(resc_path, "w", encoding='utf-8') as f:
        f.write(resc_script)

    # Windows Renode: --console runs headless. -e "quit" forces exit even on script error.
    result = subprocess.run(
        ["renode", "--console", "--plain", resc_path, "-e", "quit"],
        capture_output=True,
        timeout=120
    )
    if result.returncode not in (0, 1):
        # Log stderr for debugging but don't crash — trace file may still be partial
        print(f"[Renode] exit {result.returncode}: {result.stderr.decode(errors='replace')[:200]}")
    return trace_path

def parse_renode_trace(trace_path: str, symbols: list) -> Dict[str, int]:
    """
    Parses a Renode PC trace file, resolving PC values to function names.
    Returns: {function_name: execution_count}
    """
    code_symbols = sorted([s for s in symbols if '.text' in s.section], key=lambda x: x.address)
    counts = defaultdict(int)
    
    if not os.path.exists(trace_path):
        return counts
        
    addresses = [s.address for s in code_symbols]
    
    with open(trace_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line_clean = line.strip()
            if not line_clean: continue
            
            try:
                pc = int(line_clean, 16)
                idx = bisect.bisect_right(addresses, pc) - 1
                if idx >= 0:
                    sym = code_symbols[idx]
                    if pc < sym.address + sym.size:
                        counts[sym.name] += 1
            except ValueError:
                pass
                
    return counts
