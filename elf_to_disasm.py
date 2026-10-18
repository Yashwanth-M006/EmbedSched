"""
elf_to_disasm.py — Standalone helper that generates an objdump-style text
disassembly from a firmware ELF using pyelftools + capstone.
Output format matches arm-none-eabi-objdump -d so elf_parser.py / call_graph.py
can consume it without modification.
"""
import sys
from elftools.elf.elffile import ELFFile
import capstone

def disassemble_elf(elf_path: str, out_path: str):
    with open(elf_path, 'rb') as f:
        elf = ELFFile(f)

        # Capstone: ARM Thumb-2 (Cortex-M)
        md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
        md.detail = True

        lines = []
        # Collect all symbol addresses for label printing
        symtab = elf.get_section_by_name('.symtab')
        addr_to_name = {}
        if symtab:
            for sym in symtab.iter_symbols():
                if sym['st_info']['type'] in ('STT_FUNC', 'STT_NOTYPE') and sym['st_size'] > 0:
                    addr_to_name[sym['st_value'] & ~1] = sym.name  # clear Thumb bit

        for section in elf.iter_sections():
            if not (section['sh_flags'] & 0x4):  # SHF_EXECINSTR
                continue
            data = section.data()
            base = section['sh_addr']
            lines.append(f"\nDisassembly of section {section.name}:\n")

            # Sort and group by function
            for addr, name in sorted(addr_to_name.items()):
                if not (base <= addr < base + len(data)):
                    continue
                offset = addr - base
                # Find next symbol to bound size
                next_addrs = sorted(a for a in addr_to_name if a > addr and base <= a < base + len(data))
                end_off = (next_addrs[0] - base) if next_addrs else len(data)
                func_bytes = data[offset:end_off]

                lines.append(f"\n{addr:08x} <{name}>:")
                for insn in md.disasm(func_bytes, addr):
                    bytes_hex = ' '.join(f'{b:02x}' for b in insn.bytes)
                    lines.append(f" {insn.address:7x}:\t{bytes_hex:<20}\t{insn.mnemonic} {insn.op_str}")

                    # Print call targets in angle brackets (matching objdump format)
                    if insn.mnemonic.lower() in ('bl', 'blx', 'b'):
                        # Try to resolve target
                        for op in insn.operands:
                            if hasattr(op, 'imm'):
                                target = op.imm & ~1
                                tname = addr_to_name.get(target, f"0x{target:x}")
                                # Replace last part of line with <name>
                                lines[-1] = lines[-1] + f"\t; <{tname}>"

        with open(out_path, 'w', encoding='utf-8') as out:
            out.write('\n'.join(lines))
        print(f"Written: {out_path}")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python elf_to_disasm.py firmware.elf output.txt")
        sys.exit(1)
    disassemble_elf(sys.argv[1], sys.argv[2])
