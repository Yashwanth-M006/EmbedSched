import re
from typing import List

def parse_startup_file(filepath: str) -> List[str]:
    """
    Parses a startup assembly file to extract ISR handler names from the vector table.
    Looks for labels like g_pfnVectors: or __Vectors: and reads .word entries.
    """
    handlers = []
    
    vector_label_pattern = re.compile(r'^(g_pfnVectors|__Vectors)\s*:')
    word_pattern = re.compile(r'^\s*\.word\s+([A-Za-z0-9_]+)')
    
    in_vector_table = False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line_clean = line.split('/*')[0].split('//')[0].split(';')[0].rstrip()
            
            if not in_vector_table:
                if vector_label_pattern.match(line_clean):
                    in_vector_table = True
            else:
                # If we hit a new label or empty line that isn't a word (heuristic)
                # We'll just collect all .word entries that follow until a new label.
                if re.match(r'^[A-Za-z0-9_]+\s*:', line_clean):
                    # Reached end of vector table (another label)
                    break
                    
                match = word_pattern.search(line_clean)
                if match:
                    handler = match.group(1)
                    # Ignore estack and similar 0-element handlers if needed
                    # but typically they are just addresses.
                    if handler != '0' and not handler.startswith('_e'):
                        handlers.append(handler)
                        
    return handlers
