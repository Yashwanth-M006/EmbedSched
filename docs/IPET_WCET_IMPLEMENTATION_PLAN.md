# Implicit Path Enumeration Technique (IPET) WCET Implementation Plan
## Target Architecture: ARM Cortex-M0 / Cortex-M3 / Cortex-M4 (In-Order Microarchitectures)

---

## 1. Executive Summary & Problem Formulation

### 1.1 The Fundamental Flaw of Code-Size Heuristics
Traditional static firmware timing estimation frequently relies on byte-per-instruction (BPI) or average cycles-per-instruction (CPI) linear scaling models. In hard real-time and safety-critical embedded systems (e.g. AUTOSAR automotive ECUs), such heuristics are provably unsound due to three fundamental oversights:

1. **Loop Blindness**: Code-size heuristics inspect static binary footprints rather than dynamic execution paths. A 16-byte basic block implementing an iterative numerical filter body executing 10,000 iterations is treated identically to an unlooped 16-byte initialization sequence, introducing errors of several orders of magnitude.
2. **Context-Free Scalar Costs**: In pipelined microarchitectures, the execution duration of an instruction block is not an invariant scalar constant. It depends strictly on the microarchitectural state entering the block, including pipeline interlocks, register dependencies, and bus interface buffering.
3. **Branch Asymmetry**: The hardware cost of taking a branch versus falling through an evaluation condition is asymmetric due to pipeline flushes and instruction prefetch buffer invalidation.

### 1.2 The IPET Paradigm
To guarantee timing safety without underestimating execution duration, the system implements the **Implicit Path Enumeration Technique (IPET)**. Originally formalized by Li and Malik, IPET models the control flow of a program as a network flow graph and formulates the worst-case execution time (WCET) problem as an **Integer Linear Program (ILP)**.

Rather than explicitly enumerating an exponential number of program paths, IPET implicitly determines the worst-case path by maximizing an objective function representing total cycle consumption subject to structural control flow conservation laws and loop iteration bounds.

---

## 2. End-to-End System Architecture

The analysis pipeline processes bare-metal ARM Cortex-M ELF binaries through six formal stages:

```
                  ELF Binary (.elf)
                          │
                          ▼
        ┌───────────────────────────────────┐
        │   Phase 1: Disassembly Parser     │
        │   - Symbol resolution (.symtab)   │
        │   - Thumb-2 instruction stream    │
        └─────────────────┬─────────────────┘
                          │
                          ▼
        ┌───────────────────────────────────┐
        │   Phase 2: CFG Reconstruction     │
        │   - Basic block boundary analysis │
        │   - Directed control flow edges   │
        │   - 3-color DFS cycle discovery   │
        │   - Reducibility verification     │
        └─────────────────┬─────────────────┘
                          │
                          ▼
        ┌───────────────────────────────────┐
        │   Phase 3: Loop Bound Extraction  │
        │   - Tier 1: User annotations      │
        │   - Tier 2: GCC -fopt-info (SCEV) │
        │   - Tier 3: DWARF debug records   │
        │   - Tier 4: Static pattern match  │
        │   - Tier 5: Fallback & safeguards │
        └─────────────────┬─────────────────┘
                          │
                          ▼
        ┌───────────────────────────────────┐
        │   Phase 4: Microarchitectural     │
        │            Timing Analysis        │
        │   - 4a: Pipeline FSM & interlocks │
        │   - 4b: Flash prefetch buffer     │
        │   - 4c: Edge cost assignment      │
        └─────────────────┬─────────────────┘
                          │
                          ▼
        ┌───────────────────────────────────┐
        │   Phase 5: Integer Linear         │
        │            Programming (ILP)      │
        │   - Edge flow conservation        │
        │   - Ingress/egress constraints    │
        │   - Loop capacity constraints     │
        │   - HiGHS Branch-and-Cut solver   │
        │   - Fallback inflation guard      │
        └─────────────────┬─────────────────┘
                          │
                          ▼
        ┌───────────────────────────────────┐
        │   Phase 6: Whole-Program          │
        │            Inter-Procedural DFS   │
        │   - Call graph composition        │
        │   - Call-site BL overhead modeling│
        │   - Critical path extraction      │
        │   - Microsecond timing conversion │
        └─────────────────┬─────────────────┘
                          │
                          ▼
         Auditable WCET & Confidence Tag
       [IPET] / [IPET-ANNOTATED] / [IPET-CONSERVATIVE]
```

---

## 3. Methodologies by Analysis Phase

### 3.1 Phase 1: Disassembly & Instruction Stream Extraction

#### 3.1.1 Symbol Resolution & Boundary Disambiguation
The analysis reads raw ELF binaries and consults the static symbol table (`.symtab`), falling back to the dynamic symbol table (`.dynsym`) when binaries are stripped. Symbols typed as functions (`STT_FUNC`) or untyped symbols located in executable sections (`SHF_EXECINSTR`) are cataloged.

Because ARM Cortex-M microcontrollers exclusively execute in the Thumb-2 instruction state, symbol addresses have their least-significant bit set to 1. The loader clears this bit (masking with `~1`) to determine true physical memory alignment. When symbol sizes are reported as zero, function boundaries are determined using the monotonic distance to the next symbol entry in the enclosing section.

#### 3.1.2 Machine Instruction Parsing
Machine code bytes within function boundaries are disassembled into canonical instruction representations containing:
- Explicit 32-bit physical instruction address.
- Lowercase normalized mnemonic string.
- Decomposed operand string.
- Physical byte length (2 bytes for 16-bit Thumb, 4 bytes for 32-bit Thumb-2).
- Raw byte sequence for verification.

---

### 3.2 Phase 2: Control Flow Graph (CFG) Construction & Cycle Detection

#### 3.2.1 Basic Block Partitioning via Leader Identification
A function's instruction stream is partitioned into basic blocks—maximal sequences of consecutive instructions executed strictly in order without branches into or out of the middle. The algorithm identifies basic block "leaders" based on three structural invariants:
1. The first instruction of the function is an initial leader.
2. Any instruction that is the target of a conditional or unconditional branch instruction is a leader.
3. Any instruction immediately succeeding a branch, subroutine call, table branch, or function return instruction is a leader.

Basic blocks are formed by aggregating instructions between consecutive sorted leaders.

#### 3.2.2 Edge Typology
Control flow transfers between basic blocks are modeled as directed edges classified into four distinct operational categories:
- **FALL_THROUGH**: Linear execution from a non-branch instruction (or non-taken conditional branch) into the physically adjacent successor block.
- **BRANCH_TAKEN**: Control transfer to the branch target when a conditional evaluation evaluates to true.
- **BRANCH_UNCONDITIONAL**: Unconditional redirection (`B`, `B.W`) to a target block within the function.
- **RETURN**: Function termination (`BX LR`, `POP {..., PC}`, `LDM ..., {..., PC}`) leading to the exit node.

Subroutine calls (`BL`, `BLX`) represent intra-procedural call sites: execution branches to an external callee and returns to the immediately succeeding instruction. Within the local CFG, this is modeled as an edge to the return site whose cycle latency incorporates both the callee's execution and the architectural calling overhead.

#### 3.2.3 Natural Loop Discovery via 3-Color DFS
To identify iterative structures without relying on syntactic compiler hints, the analyzer performs a 3-color Depth-First Search traversal starting from the function entry block:
- **White**: Node unvisited.
- **Gray**: Node currently on the active DFS recursion stack.
- **Black**: Node and all downstream descendants completely explored.

A directed edge $(u \to v)$ is formally identified as a **back-edge** if and only if node $v$ is colored gray when visited from $u$. Node $v$ is designated as the **loop header** (the sole entrance into the loop body), and $u$ is designated as the **loop latch**. The natural loop corresponding to back-edge $(u \to v)$ is defined as the set of all nodes dominated by $v$ that can reach $u$ without passing through $v$.

#### 3.2.4 Irreducible Loop Detection & Safeguards
Standard natural loop identification assumes the control flow graph is **reducible**—meaning every cycle has a single unique entry node (the loop header) that dominates all nodes within the cycle. 

In hand-crafted assembly or unconventional code using computed table jumps, **irreducible loops** (cycles with multiple entry points) can theoretically occur. The analyzer includes an irreducibility check: if any cycle contains a node with predecessors outside the cycle that do not pass through the dominating header, the graph is flagged as irreducible. In safety-critical verification, irreducible loops cannot be soundly bounded by single-header structural constraints; the analyzer rejects irreducible graphs and triggers an auditable fallback to conservative estimation.

---

### 3.3 Phase 3: Multi-Tier Loop Bound Extraction

#### 3.3.1 The Halting Problem in ILP WCET
In an unconstrained network flow model, any directed cycle produces an unbounded objective function ($\text{WCET} \to \infty$). Every loop must be bound by a finite upper limit representing the maximum number of times the loop latch back-edge can be traversed relative to loop entry.

The analyzer enforces a five-tier priority hierarchy, choosing the highest-confidence source available:

```
    [Priority 1] User Annotations (schedule.json / configuration)
         │  (if not specified)
         ▼
    [Priority 2] GCC -fopt-info-loop (SCEV compiler analysis via DWARF lines)
         │  (if compiler log not provided)
         ▼
    [Priority 3] DWARF Debug Information (.debug_info array bounds/constants)
         │  (if not compiled with -g)
         ▼
    [Priority 4] Static Assembly Constant Pattern Matching (CMP reg, #N)
         │  (if loop condition is non-constant)
         ▼
    [Priority 5] Conservative Fallback (--max-loop-bound) -> [IPET-CONSERVATIVE]
```

#### 3.3.2 Tier 1: User / System Annotations
Explicit annotations provide deterministic bounds for complex algorithms (such as data-dependent convergence loops or sensor communication protocols). Annotations can specify target loops by basic block identifier, loop address, hex offset, or function name. When Tier 1 bounds are consumed, the task receives the specific safety audit tag `[IPET-ANNOTATED]` to differentiate human inputs from compiler-proven bounds.

#### 3.3.3 Tier 2: GCC Scalar Evolution (SCEV) Extraction (`-fopt-info-loop`)
When GCC compiles code with loop optimizations enabled (`-O2`, `-O3`), its internal Scalar Evolution (SCEV) engine and `tree-ssa-loop-niter` analyzer mathematically compute loop trip counts and iteration limits. GCC exports these proven bounds via compiler diagnostics (`-fopt-info-loop-all`).

The extraction methodology operates as follows:
1. **Diagnostic Parser**: Captures compiler notes reporting upper iteration limits, exact trip counts, or unrolling parameters associated with source file locations and line numbers.
2. **DWARF Line Table Mapping**: Parses the ELF binary's DWARF `.debug_line` program across all compilation units, building a bidirectional mapping between `(source_file, source_line)` pairs and 32-bit machine code instruction addresses.
3. **CFG Correlation**: Maps candidate physical addresses to basic blocks within the function CFG. If an address falls on a loop header or within a loop's natural body, the compiler-proven bound is bound directly to that loop header.

**Fragility Mitigation & Compiler Support**:
Because GCC's diagnostic messages are designed for human readability, the diagnostic syntax exhibits minor variations across major releases (specifically validated against GCC versions 10, 11, 12, 13, and 14). Furthermore, when GCC completely unrolls or vectorizes loops, loop diagnostics may disappear from the log. For this reason, Tier 2 is seamlessly backed by Tier 3 (DWARF) and Tier 4 (static disassembly) to guarantee robust extraction.

#### 3.3.4 Tier 3: DWARF Heuristic Extraction
When explicit compiler diagnostic logs are absent, debug information in `.debug_info` provides structural iteration bounds directly embedded in the binary:
- Local array dimensions defined via `DW_TAG_subrange_type` with `DW_AT_upper_bound` indicate buffer boundaries over which local iterative algorithms sweep (e.g. `upper_bound = 31` implies $32$ iterations).
- Constant induction limits declared via `DW_TAG_variable` or `DW_TAG_constant` holding `DW_AT_const_value` attributes within the enclosing subprogram.

#### 3.3.5 Tier 4: Static Assembly Constant Pattern Matching
When debug information is completely stripped, the analyzer inspects machine instructions within the loop header and loop latch blocks. It extracts comparison instructions (`CMP`, `CMP.W`, `CMN`, `SUBS`) occurring immediately prior to the conditional back-edge or loop exit branch:
- Immediate comparisons (`CMP reg, #N` followed by unsigned or signed lower/less-than branches) yield bound $N$.
- Inclusive comparisons (less-than-or-equal branches) yield bound $N + 1$.
- Decrementing countdown loops (`SUBS reg, #1; BNE`) trace backward into the loop pre-header block to identify immediate register initialization (`MOV reg, #N`).
- Sanity validation enforces $1 \le N \le 100{,}000$ to prevent errant register encodings from being treated as iteration bounds.

#### 3.3.6 Tier 5: Conservative Upper Bounding & Safety Fallback
If an identified loop cannot be resolved by Tiers 1–4:
- In standard mode: The loop is bounded by `--max-loop-bound` (default 1,000 iterations), and the analysis confidence rating is degraded to `[IPET-CONSERVATIVE]`.
- In strict mode (`--strict-loop-bounds`): The loop is marked as unanalyzable, causing IPET to abort for that function and fall back to the safe baseline heuristic while surfacing the unbounded loop header address to the safety engineer.

---

### 3.4 Phase 4: Microarchitectural Timing Analysis

#### 3.4.1 Path Dependency and Edge Costs
In pipelined hardware, assigning a single cycle cost to a basic block is fundamentally incorrect:
- A basic block beginning with an `ADD` instruction that consumes data loaded by an immediately preceding `LDR` instruction incurs a 1-cycle pipeline interlock (load-use stall) if reached via fall-through.
- If the exact same block is reached via a taken branch, the pipeline was flushed; the branch flush latency dominates, and the load-use hazard is extinguished because the execution registers were refreshed.

Therefore, the cost function must be mapped onto **directed edges**:
$$\text{Cost}(u \to v) = \text{Penalty}_{\text{flush}}(u \to v) + \text{Penalty}_{\text{fetch}}(u \to v) + \text{ExecutionCycles}(v \mid \text{State}_{\text{entry}}(u \to v))$$

#### 3.4.2 Phase 4a: In-Order Pipeline State Machine Modeling
Cortex-M0, M3, and M4 utilize shallow, strictly in-order integer execution pipelines (2 to 3 stages). At any basic block boundary, the microarchitectural state reduces to:
$$\text{PipelineState} = \langle \text{LastInstructionClass}, \text{PendingStallCycles} \rangle$$

The pipeline simulator classifies instructions into operational categories:
- **ALU**: Data processing instructions executing in 1 cycle.
- **LOAD**: Single-register memory reads (`LDR`, `LDRB`, etc.) requiring 2 cycles and producing a delayed destination register availability.
- **LOAD_MULTI / POP**: Multi-register memory operations consuming $1 + N$ cycles ($N = \text{register count}$). When the Program Counter (`PC`) is present in the unstacking list (e.g. `POP {..., PC}` function return), an additional indirect branch flush penalty (+3 cycles on Cortex-M4, +3 on M3, +2 on M0) is incurred.
- **STORE / STORE_MULTI / PUSH**: Single or multi-register memory writes consuming 2 cycles (or $1 + N$ cycles) without producing register interlocks.
- **MULTIPLY**: Core-dependent multiplication latency:
  - Cortex-M0: Up to 32 cycles (iterative hardware multiply without early termination guarantees).
  - Cortex-M3 / M4: 1 cycle (single-cycle hardware multiplier).
- **DIVIDE**: Non-pipelined hardware divide (`UDIV`, `SDIV`):
  - Cortex-M0: Unsupported (illegal instruction trap).
  - Cortex-M3 / M4: Variable 2–12 cycles (worst-case bound: 12 cycles).
- **FPU Operations (Cortex-M4F)**:
  - **Pipelined FPU Operations** (`VADD.F32`, `VSUB.F32`, `VMUL.F32`, `VMLA.F32`): Fully pipelined execution (1–2 cycles throughput) operating concurrently within the FPU without stalling the integer core, unless an explicit core register dependency occurs.
  - **Non-Pipelined Core-Blocking Operations** (`VDIV.F32`, `VSQRT.F32`): Iterative coprocessor operations taking a fixed 14 cycles, completely stalling integer instruction retirement.
- **BRANCH**: Control instructions triggering pipeline flushes upon execution.

**Intra-Block and Inter-Block Load-Use Hazard Analysis**:
Load-use interlocks occur whenever an instruction reads a register whose contents are currently being fetched from memory by an immediately preceding load instruction. The analyzer tracks this hazard at two levels:
1. **Intra-Block Tracking**: During sequential simulation within a basic block, the destination register of every load instruction is tracked. If the immediately succeeding instruction reads that destination register as a source operand, an explicit 1-cycle pipeline interlock stall is injected.
2. **Inter-Block Tracking**: Across block transitions, if the final instruction of predecessor block $u$ was a load and the initial instruction of successor block $v$ reads that target register across a `FALL_THROUGH` edge, a 1-cycle stall is injected into the entry cost of block $v$.

#### 3.4.3 Phase 4b: Flash Memory Hierarchy & Prefetch Buffer Analysis
ARM microcontrollers running at high core clock frequencies (e.g. STM32F4 at 168 MHz) experience memory latency penalties because Flash access times cannot exceed ~30 MHz. Microcontrollers bridge this gap using Flash wait states and an **instruction prefetch buffer**:

1. **128-Bit Prefetch Buffer (Cortex-M3 / Cortex-M4)**:
   - The memory interface fetches 128 bits (16 bytes = up to 4 Thumb-2 or 8 Thumb-16 instructions) in a single Flash transaction aligned to 16-byte physical memory boundaries (`address & ~0xF`).
   - **Buffer Hit**: Any instruction located within the currently active 16-byte aligned address window incurs **0 extra fetch cycles**.
   - **Buffer Miss / Cold Refill**: When an execution branch jumps to a target address outside the pre-buffered window, the core stalls for the full memory access latency:
     $$\text{FetchLatency} = 1 + \text{WaitStates} \quad (\text{cycles})$$
     At 168 MHz with 5 Flash wait states, an unbuffered branch target costs **6 cycles** before the first instruction can execute.
   - **Sequential Window Crossing in Edge Timing**: When sequential execution crosses a 16-byte physical boundary, the next 128-bit line must be loaded, incurring $1 + \text{WaitStates}$ cycles. The edge cost model explicitly evaluates the physical addresses from the ELF binary: if a `FALL_THROUGH` edge transitions into a block that begins on a new 16-byte boundary, the 6-cycle refill penalty is assigned directly to that edge. Tight loop bodies that straddle a 16-byte Flash boundary incur this refill penalty on every single iteration.

2. **Von Neumann Single Bus (Cortex-M0)**:
   - Lacks an instruction prefetch buffer.
   - Every 16-bit instruction word requires an explicit bus read costing $1 + \text{WaitStates}$ cycles. A 32-bit Thumb-2 instruction requires two sequential reads:
     $$\text{FetchLatency}_{\text{M0}} = \left(\frac{\text{InstructionSize}}{2}\right) \cdot (1 + \text{WaitStates})$$

#### 3.4.4 Phase 4c: Edge Timing Assignment & Cortex-M3 Flush Specifications
For each directed edge $(u \to v)$ in the CFG:
1. **Branch Flush Penalty**: If $u \to v$ represents a taken branch, the core incurs an architectural pipeline refill penalty:
   - Cortex-M0: 2 cycles.
   - Cortex-M4: 1 cycle for direct branch (target resolved at decode stage), 3 cycles for indirect register branch (`BX reg`).
   - **Cortex-M3 Specification Note**: The Cortex-M3 Technical Reference Manual (r2p1) specifies:
     - Branch taken (target known at decode, 16-bit encoding): 1 cycle penalty.
     - Branch taken (32-bit encoding or target not resolved at decode): 3 cycles penalty.
     - Indirect branch (`BX reg`, `BLX reg`): 3 cycles penalty.
     *Deliberate Conservative Choice*: For Cortex-M3, the timing engine adopts a uniform 3-cycle penalty for taken branches. This is a deliberate, provably safe conservative choice. For tight loops composed of 16-bit branch encodings, this introduces up to 2 cycles of pessimism per iteration (e.g. 2,000 cycles over 1,000 iterations), ensuring timing guarantees remain sound without requiring complex instruction-length decode heuristics.
2. **Fetch Penalty**: If entering via a branch, the prefetch buffer is cold ($1 + \text{WaitStates}$). If entering via fall-through, the prefetch state evaluates whether the block boundary crossed a 16-byte physical Flash line.
3. **Block Execution**: The block instructions are simulated through the pipeline state machine, including intra-block load-use hazard checks.
4. The total cycle cost is summed and assigned directly to edge $(u \to v)$.
5. A virtual ingress edge $(\text{\_\_entry\_\_} \to \text{entry\_bb})$ is created and assigned the cold entry flush penalty, cold fetch latency, and entry block execution cycles.

---

### 3.5 Phase 5: Integer Linear Programming (ILP) Formulation

#### 3.5.1 Decision Variables
Let $G = (V, E)$ represent the function CFG, where $V$ is the set of basic blocks augmented with virtual nodes $\{\text{\_\_entry\_\_}, \text{\_\_exit\_\_}\}$, and $E$ is the set of directed control flow edges.

For each directed edge $e = (u \to v) \in E$, the ILP defines an integer decision variable:
$$x_e \in \mathbb{Z}_{\ge 0}$$
representing the exact number of times edge $e$ is traversed in the worst-case execution path.

#### 3.5.2 Objective Function
The objective is to maximize the cumulative cycle latency consumed across all traversed edges:
$$\text{Maximize } \mathcal{Z} = \sum_{e \in E} \text{Cost}(e) \cdot x_e$$
where $\text{Cost}(e)$ is the microarchitectural cycle latency computed in Phase 4c.

#### 3.5.3 Structural Flow Conservation Constraints
To ensure the edge execution frequencies form a topologically valid execution path through the control flow graph, Kirchhoff-like flow conservation constraints are applied to every basic block node:

$$\sum_{e \in \text{In}(v)} x_e = \sum_{e \in \text{Out}(v)} x_e \quad \forall v \in V \setminus \{\text{\_\_entry\_\_}, \text{\_\_exit\_\_}\}$$

where $\text{In}(v) = \{(u \to v) \in E\}$ and $\text{Out}(v) = \{(v \to w) \in E\}$.

#### 3.5.4 Ingress and Egress Normalization
The function is invoked exactly once per activation:
$$x_{(\text{\_\_entry\_\_} \to \text{entry\_bb})} = 1$$
Similarly, the function terminates exactly once:
$$\sum_{e \in \text{In}(\text{\_\_exit\_\_})} x_e = 1$$

#### 3.5.5 Structural Loop Capacity Constraints
For every natural loop $L$ having header block $h \in V$, loop latch back-edge $e_{\text{back}} = (\text{latch} \to h)$, and loop bound $N_L$ extracted in Phase 3:

The number of times the loop back-edge is executed cannot exceed $N_L$ times the number of times the loop was entered from outside the loop:
$$x_{e_{\text{back}}} \le N_L \cdot \sum_{e \in \text{In}(h) \setminus E_{\text{back}}} x_e$$

For single-entry non-nested loops, the external ingress evaluates to 1, bounding the back-edge traversal to at most $N_L$. For nested loops, the constraint naturally scales the inner loop traversal count relative to the outer loop's actual execution frequency.

#### 3.5.6 Mathematical Solver & Fallback Inflation Safeguards
The ILP problem is solved using the **HiGHS** simplex and branch-and-cut solver (via `scipy.optimize.milp`). Because the ILP formulation is integer-constrained, the resulting objective value $\mathcal{Z}^*$ is an exact integer representing the true worst-case execution time in hardware clock cycles.

**Fallback Inflation Guard**:
When loops fall back to Tier 5 conservative defaults (e.g. 1,000 iterations), deeply nested loops compound multiplicatively (e.g. $1000 \times 1000 = 1{,}000{,}000$ iterations). While the ILP solver guarantees termination and mathematical feasibility, the resulting cycle count can become astronomically pessimistic. 

To safeguard the AUTOSAR scheduling analysis from false unschedulability alarms:
- The solver evaluates the ratio between computed WCET and the task deadline ($D_i$) or period ($T_i$).
- If $\text{WCET} > 10 \cdot T_i$ and the task contains Tier 5 fallback bounds, the system flags the result as a **"Fallback Inflation Artifact"** and reports the unannotated inner loop addresses, preventing unusable pessimism from masking real scheduling behavior.

---

### 3.6 Phase 6: Whole-Program Inter-Procedural Composition

#### 3.6.1 Hierarchical Call Graph Traversal & Call-Site Overhead
Firmware execution extends beyond isolated subroutines into call trees. The global timing model traverses the program call graph generated from call instructions (`BL`, `BLX`):
1. **Recursion Verification**: In safety-critical embedded systems (AUTOSAR / ISO 26262), recursion is prohibited. The call graph is verified as a Directed Acyclic Graph (DAG); recursive cycles trigger immediate safety audit violations.
2. **Reverse Topological Evaluation**: Functions are analyzed leaf-first.
3. **Explicit Call-Site Overhead Modeling**:
   When function $A$ calls function $B$ via `BL target`, the call is not a frictionless transition:
   - `BL` causes an indirect branch pipeline flush (3 cycles on Cortex-M4, 3 on M3, 2 on M0).
   - Calling does not trigger automatic hardware register stacking (hardware stacking occurs only on interrupt service routines). Software stack allocation (`PUSH {r4-r7, lr}`) and deallocation (`POP {r4-r7, pc}`) are accounted for within callee $B$'s own ILP analysis.
   - The caller's call-site edge incorporates both the callee's worst-case cycle latency and the calling instruction's pipeline flush penalty:
     $$\text{Cost}_{\text{call\_edge}} = \text{Penalty}_{\text{BL\_flush}} + \text{Penalty}_{\text{fetch}} + \text{WCET}_{\text{callee}} + \text{Cost}_{\text{return\_site}}$$

#### 3.6.2 Physical Timing Conversion
Cycle counts are converted to wall-clock microseconds ($\mu\text{s}$) using the target core operating frequency specified in the microcontroller chip profile:
$$\text{WCET}_{\mu\text{s}} = \frac{\text{WCET}_{\text{cycles}}}{f_{\text{core}} \text{ (MHz)}}$$

---

## 4. Hardware Timing Reference Specifications

The microarchitectural analysis engine implements timing parameters derived directly from manufacturer reference manuals:

| Parameter | Cortex-M0 | Cortex-M3 | Cortex-M4 / M4F |
| :--- | :---: | :---: | :---: |
| **Pipeline Architecture** | 2-stage in-order | 3-stage in-order | 3-stage in-order |
| **Branch Predictor** | None (Static) | None (Static) | None (Static) |
| **Data Cache (D-Cache)** | None | None | None |
| **Instruction Cache (I-Cache)** | None | None | None |
| **Instruction Prefetch Buffer** | None | 128-bit (16 bytes) | 128-bit (16 bytes) |
| **Load-Use Interlock Penalty** | 1 cycle stall | 1 cycle stall | 1 cycle stall |
| **Direct Branch Flush Penalty** | 2 cycles | 1–3 cycles (3 cyc conservative) | 1 cycle |
| **Indirect Branch Flush Penalty** | 2 cycles | 3 cycles | 3 cycles |
| **POP {..., PC} Return Penalty** | $1 + N + 2$ cycles | $1 + N + 3$ cycles | $1 + N + 3$ cycles |
| **Hardware Multiply (`MUL`)** | Up to 32 cycles | 1 cycle | 1 cycle |
| **Multiply-Accumulate (`MLA`)** | Unsupported | 2 cycles | 1–2 cycles |
| **Hardware Divide (`UDIV`/`SDIV`)** | Unsupported | 2–12 cycles (12 cyc bound) | 2–12 cycles (12 cyc bound) |
| **Single-Precision FPU Addition** | Unsupported | Unsupported | 1 cycle (pipelined) |
| **Single-Precision FPU Multiply** | Unsupported | Unsupported | 1–2 cycles (pipelined) |
| **Non-Pipelined FPU Divide (`VDIV`)** | Unsupported | Unsupported | 14 cycles (core blocking) |
| **Non-Pipelined FPU Root (`VSQRT`)**| Unsupported | Unsupported | 14 cycles (core blocking) |

---

## 5. Confidence Hierarchy & Safety Tagging

The static analysis engine tags every computed task WCET with an explicit confidence classification to ensure transparent auditability in compliance with ISO 26262 ASIL timing requirements:

| Confidence Tag | Timing Methodology | Real-Time Safety |
| :--- | :--- | :--- |
| `[SIMULATED]` | Cycle-accurate trace from Renode emulation | Verified Empirical |
| `[IPET]` | Formal IPET + Pipeline model + Compiler bounds | Provably Sound Bound |
| `[IPET-ANNOTATED]` | Formal IPET + Verified user loop annotations | Domain Bounded |
| `[IPET-CONSERVATIVE]` | Formal IPET + Fallback loop bounds | Upper Bound (Pess.) |
| `[CALCULATED]` | Static code size BPI/CPI linear heuristic | Unverified Heuristic |
| `[HEURISTIC]` | Placeholder estimate (10 cycles) | Non-operational |

### Contamination Propagation Rule
In task call trees, confidence propagates according to the **weakest-link principle**: if task $T$ calls three functions where two evaluate to `[IPET]` but one evaluates to `[IPET-CONSERVATIVE]` due to an unbounded loop, the composite task confidence degrades to `[IPET-CONSERVATIVE]`. If any callee falls back to `[CALCULATED]`, the entire task is flagged as `[CALCULATED]`.

---

## 6. Implementation Phasing & Validation Milestones

| Step | Milestone | Core Analytical Goal | Validation Test |
| :---: | :--- | :--- | :--- |
| **A** | **CFG Reconstruction** | Partition instruction stream into basic blocks, verify reducibility, and discover loops via 3-color DFS. | Compare CFG against GCC compiler graph on test suites. |
| **B** | **Pipeline Simulator** | Model in-order instruction latencies, intra-block and inter-block load-use hazard stalls. | Verify load-use penalty: consecutive load and dependent add yields +1 stall cycle. |
| **C** | **Flash Memory Model** | Model 128-bit prefetch buffer hits, cold misses, and 16-byte physical boundary crossing. | Verify branch jump incurs $1 + \text{WS}$ cycles while sequential instructions cost 0. |
| **D** | **CFG Edge Annotation** | Compute path-dependent costs across all directed edges, incorporating POP {..., PC} flush penalties. | Confirm taken branch edge cost exceeds fall-through edge cost for conditional blocks. |
| **E** | **Loop Bound Extractor** | Extract bounds via user annotations, GCC `-fopt-info-loop`, DWARF, and static assembly patterns. | Correlate GCC SCEV loop bounds against firmware loops via DWARF line tables. |
| **F** | **ILP Mathematical Solver** | Formulate network flow and solve via HiGHS Branch-and-Cut with Fallback Inflation Guard. | Solve canonical loop: $\text{WCET} = \text{Init} + N \cdot \text{Body} + \text{Exit}$. |
| **G** | **Extractor Integration** | Wire IPET solver into whole-program AUTOSAR scheduling analysis engine. | Validate that static IPET bound upper-bounds Renode simulation measurements. |
