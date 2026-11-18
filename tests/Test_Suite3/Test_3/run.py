import os
import subprocess

cmd = [
    'python', '../../../main.py',
    '--elf', 'firmware.elf',
    '--map', 'firmware.map',
    '--ld', 'linker.ld',
    '--chip', 'stm32f407.yaml',
    '--autosar-config', 'schedule.json',
    '--charts-dir', 'charts',
    '--stochastic-sim'
]

env = os.environ.copy()
env['PYTHONIOENCODING'] = 'utf-8'

proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env)

with open('results.md', 'w', encoding='utf-8') as f:
    f.write("```\n")
    f.write(proc.stdout.strip())
    f.write("\n```\n")
