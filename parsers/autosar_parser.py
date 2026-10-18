"""
parsers/autosar_parser.py

Parses AUTOSAR OS task configuration from:
  - A simplified JSON format (primary, designed for this tool)
  - A minimal OIL-subset text format (secondary, for real AUTOSAR projects)

JSON format (preferred):
{
  "tasks": [
    {
      "name":        "Task_MotorControl",
      "period_us":   1000,
      "deadline_us": 1000,
      "priority":    10,
      "core_id":     0,
      "function":    "motor_control_loop"
    },
    ...
  ],
  "isrs": [
    {
      "name":     "ADC_IRQHandler",
      "priority": 255,
      "core_id":  0
    }
  ]
}

OIL-subset format (parsed if file ends in .oil):
TASK Task_MotorControl {
    PRIORITY = 10;
    PERIOD = 1000 US;
    DEADLINE = 1000 US;
    CORE = 0;
    FUNCTION = motor_control_loop;
};
"""

import json
import re
from typing import List, Tuple, Dict
from dataclasses import dataclass
from models.autosar_task import AutosarTask, CoreConfig, Resource, InterCoreChannel

@dataclass
class AutosarConfig:
    tasks: List[AutosarTask]
    isrs: List[AutosarTask]
    cores: Dict[int, CoreConfig]
    resources: List[Resource]
    inter_core_channels: List[InterCoreChannel]
    scheduler_config: dict

def parse_autosar_config(path: str) -> AutosarConfig:
    """
    Parse an AUTOSAR OS config file.
    """
    if path.lower().endswith('.oil'):
        tasks, isrs = _parse_oil(path)
        return AutosarConfig(
            tasks=tasks, isrs=isrs,
            cores={0: CoreConfig(id=0, algorithm="RM")},
            resources=[], inter_core_channels=[],
            scheduler_config={"algorithm": "RM", "preemptive": True, "resource_protocol": "PCP"}
        )
    else:
        return _parse_json(path)


def load_autosar_config(path: str, symbols: list = None) -> AutosarConfig:
    """
    Public alias for parse_autosar_config matching the SDK specification.
    Accepts optional symbols list for compatibility.
    """
    return parse_autosar_config(path)


# ---------------------------------------------------------------------------
# JSON parser
# ---------------------------------------------------------------------------

def _parse_json(path: str) -> AutosarConfig:
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 1. Parse Scheduler Config
    sched_cfg = data.get('scheduler', {"algorithm": "RM", "preemptive": True, "resource_protocol": "PCP"})

    # 2. Parse Cores
    cores = {}
    for c in data.get('cores', []):
        c_id = c.get('id', 0)
        cores[c_id] = CoreConfig(
            id=c_id,
            algorithm=c.get('algorithm', sched_cfg.get('algorithm', 'RM'))
        )
    if not cores:
        cores[0] = CoreConfig(id=0, algorithm=sched_cfg.get('algorithm', 'RM'))

    # 3. Parse Resources
    resources = []
    for r in data.get('resources', []):
        task_cs = {}
        if 'critical_sections_ms' in r:
            task_cs = {k: float(v) * 1000.0 for k, v in r['critical_sections_ms'].items()}
        elif 'critical_sections_us' in r:
            task_cs = {k: float(v) for k, v in r['critical_sections_us'].items()}

        resources.append(Resource(
            name=r['name'],
            type=r.get('type', 'mutex'),
            accessed_by=r.get('accessed_by', []),
            critical_section_us=float(r.get('max_critical_section_ms', r.get('critical_section_us', 0.005))) * 1000.0 if 'max_critical_section_ms' in r else float(r.get('critical_section_us', 5.0)),
            task_critical_sections_us=task_cs,
            acquisition_order=r.get('acquisition_order', {}),
        ))

    # 4. Parse Inter-Core Channels
    channels = []
    for ch in data.get('inter_core_channels', []):
        channels.append(InterCoreChannel(
            from_task=ch['from_task'],
            to_task=ch['to_task'],
            shared_region=ch['shared_region'],
            sync_mechanism=ch['sync_mechanism'],
            write_latency_us=float(ch.get('write_latency_us', ch.get('data_latency_us', 0.0)))
        ))

    # 5. Parse Tasks
    tasks: List[AutosarTask] = []
    for raw in data.get('tasks', []):
        # Support both new and old schemas
        name = raw['name']
        core_id = int(raw.get('core', raw.get('core_id', 0)))
        raw_priority = raw.get('priority')
        priority = int(raw_priority) if raw_priority is not None else 255
        function = raw.get('entry_function', raw.get('function', name))
        
        if 'period_ms' in raw:
            period = float(raw['period_ms']) * 1000.0
            deadline = float(raw.get('deadline_ms', raw['period_ms'])) * 1000.0
        else:
            period = float(raw.get('period_us', 0))
            deadline = float(raw.get('deadline_us', period))
            
        task_resources = raw.get('resources', [])
        stack_bytes = int(raw.get('stack_bytes', raw.get('stack_size', raw.get('stack', 0))))

        tasks.append(AutosarTask(
            name=name,
            period_us=period,
            deadline_us=deadline,
            priority=priority,
            core_id=core_id,
            function=function,
            resources=task_resources,
            stack_bytes=stack_bytes
        ))

    # 6. Parse ISRs
    isr_tasks: List[AutosarTask] = []
    for raw in data.get('isrs', []):
        name = raw['name']
        core_id = int(raw.get('core', raw.get('core_id', 0)))
        priority = int(raw.get('priority', 255))
        function = raw.get('entry_function', raw.get('function', name))
        
        if 'period_ms' in raw:
            period = float(raw['period_ms']) * 1000.0
            deadline = float(raw.get('deadline_ms', raw['period_ms'])) * 1000.0
        else:
            period = float(raw.get('period_us', 0))
            deadline = float(raw.get('deadline_us', 0))
            
        task_resources = raw.get('resources', [])
            
        isr_tasks.append(AutosarTask(
            name=name,
            period_us=period,
            deadline_us=deadline,
            priority=priority,
            core_id=core_id,
            function=function,
            resources=task_resources,
            is_isr=True,
        ))

    return AutosarConfig(
        tasks=tasks,
        isrs=isr_tasks,
        cores=cores,
        resources=resources,
        inter_core_channels=channels,
        scheduler_config=sched_cfg
    )

def _require_fields(obj: dict, fields: list, path: str):
    for f in fields:
        if f not in obj:
            raise ValueError(
                f"AUTOSAR config '{path}': task/isr entry missing required field '{f}'.\n"
                f"  Entry: {obj}"
            )


# ---------------------------------------------------------------------------
# OIL-subset parser
# ---------------------------------------------------------------------------
# Supports a simplified subset sufficient for schedulability analysis:
#   TASK <name> { PRIORITY = N; PERIOD = N US; DEADLINE = N US;
#                  CORE = N; FUNCTION = sym; };
#   ISR <name>  { PRIORITY = N; CORE = N; FUNCTION = sym; };
# ---------------------------------------------------------------------------

_OIL_BLOCK  = re.compile(
    r'(TASK|ISR)\s+(\w+)\s*\{([^}]*)\}', re.DOTALL | re.IGNORECASE
)
_OIL_KV     = re.compile(r'(\w+)\s*=\s*([^;]+);')
_TIME_VALUE  = re.compile(r'(\d+(?:\.\d+)?)\s*(US|MS|NS)?', re.IGNORECASE)


def _parse_oil(path: str) -> Tuple[List[AutosarTask], List[AutosarTask]]:
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()

    # Strip single-line comments
    text = re.sub(r'//[^\n]*', '', text)
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)

    tasks: List[AutosarTask] = []
    isr_tasks: List[AutosarTask] = []

    for m in _OIL_BLOCK.finditer(text):
        kind   = m.group(1).upper()
        name   = m.group(2)
        body   = m.group(3)
        kv: dict = {}
        for km in _OIL_KV.finditer(body):
            kv[km.group(1).upper()] = km.group(2).strip()

        priority = int(kv.get('PRIORITY', 1))
        core_id  = int(kv.get('CORE', 0))
        function = kv.get('FUNCTION', name)

        if kind == 'TASK':
            period_us  = _parse_time_us(kv.get('PERIOD',   '0'))
            deadline_us= _parse_time_us(kv.get('DEADLINE', str(period_us) + ' US'))
            tasks.append(AutosarTask(
                name=name,
                period_us=period_us,
                deadline_us=deadline_us,
                priority=priority,
                core_id=core_id,
                function=function,
            ))
        else:  # ISR
            period_us  = _parse_time_us(kv.get('PERIOD',   '0'))
            deadline_us= _parse_time_us(kv.get('DEADLINE', '0'))
            isr_tasks.append(AutosarTask(
                name=name,
                period_us=period_us,
                deadline_us=deadline_us,
                priority=priority,
                core_id=core_id,
                function=function,
                is_isr=True,
            ))

    return tasks, isr_tasks


def _parse_time_us(s: str) -> float:
    """Convert an OIL time expression to microseconds."""
    m = _TIME_VALUE.match(s.strip())
    if not m:
        return 0.0
    value = float(m.group(1))
    unit  = (m.group(2) or 'US').upper()
    if unit == 'NS':
        return value / 1000.0
    elif unit == 'MS':
        return value * 1000.0
    else:  # US
        return value
