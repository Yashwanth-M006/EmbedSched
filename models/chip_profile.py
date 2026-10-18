import yaml
from typing import Dict, Any

def load_chip_profile(filepath: str) -> Dict[str, Any]:
    """
    Loads and parses the chip profile YAML file.
    Returns a dictionary representing the MCU profile.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        profile = yaml.safe_load(f)
        
    # Basic validation
    required_keys = ['name', 'memory_regions']
    for key in required_keys:
        if key not in profile:
            raise ValueError(f"Invalid chip profile: missing required key '{key}'")
    if 'core' not in profile and 'core_types' not in profile:
        raise ValueError("Invalid chip profile: must have 'core' or 'core_types'")
            
    return profile
