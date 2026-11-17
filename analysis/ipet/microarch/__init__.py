"""
analysis/ipet/microarch/ — Microarchitectural Analysis Package
for ARM Cortex-M0/M3/M4 in-order processors.
"""

from .pipeline_model import (
    InsnClass,
    PipelineState,
    BASE_LATENCY,
    classify_instruction,
    compute_instruction_cycles,
    simulate_block,
)
from .memory_model import (
    PrefetchBufferState,
    PREFETCH_BUFFER_WIDTH_BYTES,
    DATA_LATENCY_CYCLES,
    fetch_cost_m3m4,
    fetch_cost_m0,
)
from .edge_annotator import annotate_edges

__all__ = [
    "InsnClass",
    "PipelineState",
    "BASE_LATENCY",
    "classify_instruction",
    "compute_instruction_cycles",
    "simulate_block",
    "PrefetchBufferState",
    "PREFETCH_BUFFER_WIDTH_BYTES",
    "DATA_LATENCY_CYCLES",
    "fetch_cost_m3m4",
    "fetch_cost_m0",
    "annotate_edges",
]

