import os
import subprocess

cmd = [
    'python', '../../main.py',
    '--elf', 'firmware.elf',
    '--map', 'firmware.map',
    '--ld', 'linker.ld',
    '--chip', 'stm32f407.yaml',
    '--autosar-config', 'schedule.json',
    '--charts-dir', 'charts',
    '--stochastic-sim',
    '--su-dir', '.'
]

env = os.environ.copy()
env['PYTHONIOENCODING'] = 'utf-8'

with open('results.md', 'w', encoding='utf-8') as f:
    subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, env=env)
