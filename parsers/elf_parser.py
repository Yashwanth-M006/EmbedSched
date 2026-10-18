import subprocess
import os

def run_objdump_disassembly(elf_path: str) -> str:
    """
    Runs arm-none-eabi-objdump -d on the given ELF file.
    Returns the disassembly text in objdump-style format.
    Fallback priority:
      1. .txt file provided directly (pre-generated disassembly)
      2. arm-none-eabi-objdump on PATH
      3. pyelftools + capstone (pure-Python fallback)
    """
    if elf_path.endswith('.txt') and os.path.exists(elf_path):
        with open(elf_path, 'r', encoding='utf-8') as f:
            return f.read()

    # Try arm-none-eabi-objdump first
    try:
        result = subprocess.run(
            ['arm-none-eabi-objdump', '-d', elf_path],
            capture_output=True, text=True
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout
    except FileNotFoundError:
        pass  # Not on PATH — fall through to pyelftools

    # Fallback: pyelftools + capstone
    return _disassemble_with_capstone(elf_path)


def _disassemble_with_capstone(elf_path: str) -> str:
    try:
        from elftools.elf.elffile import ELFFile
        import capstone

        md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
        md.detail = True
        lines = []

        with open(elf_path, 'rb') as f:
            elf = ELFFile(f)

            # Collect symbol table
            addr_to_name = {}
            symtab = elf.get_section_by_name('.symtab')
            if symtab:
                for sym in symtab.iter_symbols():
                    if sym['st_info']['type'] in ('STT_FUNC', 'STT_NOTYPE') and sym['st_size'] > 0:
                        addr_to_name[sym['st_value'] & ~1] = sym.name

            for section in elf.iter_sections():
                if not (section['sh_flags'] & 0x4):  # SHF_EXECINSTR
                    continue
                data = section.data()
                base = section['sh_addr']
                lines.append(f"\nDisassembly of section {section.name}:\n")

                for addr in sorted(addr_to_name):
                    if not (base <= addr < base + len(data)):
                        continue
                    name = addr_to_name[addr]
                    offset = addr - base
                    next_addrs = sorted(a for a in addr_to_name if a > addr and base <= a < base + len(data))
                    end_off = (next_addrs[0] - base) if next_addrs else len(data)
                    func_bytes = data[offset:end_off]

                    lines.append(f"\n{addr:08x} <{name}>:")
                    for insn in md.disasm(func_bytes, addr):
                        bytes_hex = ' '.join(f'{b:02x}' for b in insn.bytes)
                        line = f" {insn.address:7x}:\t{bytes_hex:<20}\t{insn.mnemonic} {insn.op_str}"
                        if insn.mnemonic.lower() in ('bl', 'blx', 'b'):
                            for op in insn.operands:
                                if hasattr(op, 'imm'):
                                    target = op.imm & ~1
                                    tname = addr_to_name.get(target)
                                    if tname:
                                        line += f" <{tname}>"
                        lines.append(line)

        return '\n'.join(lines)

    except ImportError as e:
        raise RuntimeError(
            f"arm-none-eabi-objdump not found and pyelftools/capstone not installed.\n"
            f"Install with: pip install pyelftools capstone\n"
            f"Or generate disassembly manually: arm-none-eabi-objdump -d firmware.elf > firmware.txt\n"
            f"Original error: {e}"
        )
