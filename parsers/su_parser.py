import os
import glob
from typing import Dict

def parse_su_files(su_dir: str) -> Dict[str, int]:
    """
    Parses all .su files in the given directory and its subdirectories.
    Returns a dictionary mapping function names to their static frame size.
    Format: file:line:col:function_name   frame_size   type
    """
    usage = {}
    
    if not su_dir or not os.path.exists(su_dir):
        return usage
        
    for filepath in glob.glob(os.path.join(su_dir, '**', '*.su'), recursive=True):
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 2:
                    location = parts[0]
                    # location is file:line:col:func
                    func_name = location.split(':')[-1]
                    try:
                        frame_size = int(parts[1])
                        usage[func_name] = frame_size
                    except ValueError:
                        pass
                        
    return usage
