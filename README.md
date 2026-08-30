# BigDSA — Backend

> AST-powered Big O complexity analysis

## What is BIGDSA - Backend?

BigDSA Backend is a REST API for analyzing the time complexity (Big O) of Python code using AST parsing and optional AI explanation via AI Model.
The name is a double reference — to **Big O notation** (the backbone of algorithm analysis) and to **Data Structures & Algorithms (DSA)**.

## Stack

- **FastAPI** — web framework
- **ast** — code parsing and AST traversal
- **radon** — code metrics
- **Redis** — caching analysis results
- **Groq (llama-3.3-70b-versatile)** — AI explanations
- **uv** — dependency management
- **Ruff / Black** — linting and formatting

---

## Architecture

```
app/
├── main.py                     # FastAPI app entry point
├── core/
│   ├── config.py               # Settings via pydantic-settings (.env)
│   ├── middleware.py            # CORS middleware setup
│   └── exceptions.py           # Custom exception types
├── features/
│   ├── temporal_complexity/    # Time complexity analysis feature
│   │   ├── router.py           # POST /api/analyze/temporal
│   │   ├── service.py          # Orchestration: cache → analyze → AI
│   │   ├── analyzer.py         # AST-based Big O inference
│   │   ├── request.py          # Request schema (Pydantic)
│   │   └── dto.py              # Response DTO
│   ├── spatial_complexity/     # Space (memory) complexity feature
│   │   ├── router.py           # POST /api/analyze/spatial
│   │   ├── service.py          # Orchestration: cache → analyze → AI
│   │   └── analyzer.py         # AST-based space Big O inference
│   └── reports/                # Shared report value objects
│       ├── temporal_analysis_report.py
│       └── spatial_analysis_report.py
└── shared/
    ├── ast/
    │   ├── parser.py           # Python AST parser wrapper
    │   ├── fingerprint.py      # Code fingerprint for cache keys
    │   ├── value_objects/      # NormalizedCode value object
    │   ├── visitors/           # Allocation / recursion AST visitors (raw counts)
    │   └── complexity/         # Symbolic Big O cost engine (time + space)
    ├── cache/
    │   ├── service.py          # Redis get/set abstraction
    │   ├── client.py           # Redis client factory
    │   └── mixin.py            # CacheMixin for services
    └── ai/
        ├── ai.py               # Groq API wrapper
        ├── client.py           # AI client factory
        └── service.py          # AI prompt orchestration
```

### Request flow

```
POST /api/analyze/temporal
        │
        ▼
TemporalComplexityService
        │
        ├─ NormalizedCode + Fingerprint (cache key)
        │
        ├─ Cache hit? ──yes──▶ return cached TemporalAnalysisReport
        │
        └─ Cache miss ──▶ TemporalComplexityAnalyzer (AST)
                               │
                               ▼
                     CostEvaluator (shared/ast/complexity)
                       walks the tree and composes a symbolic
                       Big O expression:
                         • sequential loops add      → O(n + m)
                         • nested loops multiply      → O(n²)
                         • sorted()/membership/slices → O(n log n)
                         • recursion (recursion-tree) → O(log n) … O(2^n)
                               │
                      (if explain_ai=true)
                               │
                               ▼
                         AIService → Groq LLM → TemporalAIReport
```

---

## Endpoints

| Method | Path                    | Description                             |
| ------ | ----------------------- | -------------------------------------- |
| `GET`  | `/api/health`           | Health check                           |
| `POST` | `/api/analyze/temporal` | Analyze time complexity of Python code  |
| `POST` | `/api/analyze/spatial`  | Analyze space complexity of Python code |

### `POST /api/analyze/temporal`

**Request body:**

```json
{
  "code": "for i in range(n):\n    for j in range(n):\n        pass",
  "explain_ai": false
}
```

**Response:**

```json
{
  "analysis": {
    "time_complexity": "O(n²)",
    "terms": ["n²"],
    "variables": [{ "symbol": "n", "source": "range(n)" }],
    "max_loop_depth": 2,
    "loop_count": 2,
    "recursive": false,
    "recursion_kind": null
  },
  "ai": null
}
```

- `terms` — the additive terms of the Big O expression, biggest first (`["n²", "m"]` for `O(n² + m)`).
- `variables` — each Big O symbol and the source expression it was resolved from.
- `recursion_kind` — `linear`, `logarithmic`, `divide_and_conquer`, `polynomial`, `exponential` or `null`.

Set `explain_ai: true` to include an LLM-generated explanation of the result.

### What the analyzer detects

| Code shape | Result |
| ---------- | ------ |
| one loop over `n` | `O(n)` |
| two **sequential** loops over the same collection | `O(n)` |
| two **sequential** loops over different collections | `O(n + m)` |
| two **nested** loops | `O(n²)` (nested loops collapse to one variable) |
| a nested pair followed by a separate loop | `O(n² + m)` |
| `for _ in range(10)` (constant bound) | `O(1)` |
| `sorted(x)` / `x.sort()` / `for x in sorted(...)` | `O(n log n)` |
| `x in some_list` inside a loop | `O(n²)` |
| linear recursion (`f(n - 1)`) | `O(n)` |
| binary search (`f(n // 2)`) | `O(log n)` |
| merge sort (two halved self-calls + linear merge) | `O(n log n)` |
| naive fibonacci (two `f(n - 1)` / `f(n - 2)` calls) | `O(2^n)` |

Limitations: nested loops always collapse to a single variable (`O(n·m)` is never
emitted); `while` loops with no detectable bound are assumed `O(n)`;
interprocedural analysis is one call level deep; worst-case only (`break` / early
return ignored).

### `POST /api/analyze/spatial`

Same request shape. Measures the **extra** memory an algorithm allocates.

```json
{
  "analysis": {
    "space_complexity": "O(n²)",
    "terms": ["n²"],
    "variables": [{ "symbol": "n", "source": "n" }],
    "recursion_kind": null,
    "total_allocations": 2,
    "list_allocations": 2,
    "dict_allocations": 0,
    "set_allocations": 0,
    "comprehensions": 0,
    "generator_expressions": 0,
    "dynamic_growth_operations": 1,
    "recursive_functions": 0
  },
  "ai": null
}
```

| Code shape | Result |
| ---------- | ------ |
| scalars / in-place swaps / `sorted()` used but discarded | `O(1)` |
| a generator expression (`(x for x in xs)`) | `O(1)` (lazy) |
| `[f(x) for x in data]` / `[0] * n` / `arr[a:b]` / `sorted(arr)` | `O(n)` |
| a list/dict/set filled with `append` / `d[k]=v` / `add` in one loop | `O(n)` |
| a structure filled in **two nested** loops, or `[[0] * n for _ in range(m)]` | `O(n²)` |
| two independent structures over different inputs | `O(n + m)` |
| linear or tree recursion (stack **depth**, not call count) | `O(n)` |
| divide-and-conquer recursion (`f(n // 2)`) | `O(log n)` |

Limitations: recursion contributes stack **depth** (fibonacci is `O(n)` space, not
`O(2^n)`); a container's size is attributed to the loops enclosing its *mutation*
sites; mutating a caller's argument is not counted as auxiliary space.

---

## Setup

### Prerequisites

- Python 3.12+
- Redis running on `localhost:6379`
- [uv](https://docs.astral.sh/uv/) installed

### 1. Clone and enter the project

```bash
mkdir big-dsa
cd big-dsa
git clone https://github.com/Riodev28/be-big-dsa.git backend
cd backend
```

### 2. Create the virtual environment and install dependencies

```bash
uv sync
```

To include dev dependencies:

```bash
uv sync --group dev
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env`:

```env
CACHE_URL=redis://localhost:6379
AI_API_KEY=your_groq_api_key_here
```

Get a free Groq API key at [console.groq.com](https://console.groq.com).

### 4. Start Redis

```bash
# Docker
docker run -d -p 6379:6379 redis
```

### 5. Run the server

```bash
uv run uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

Interactive docs: `http://localhost:8000/docs`

---

## Development

### Run tests

```bash
uv run pytest
```

### Lint

```bash
uv run ruff check .
```

### Format

```bash
uv run black .
```

### Run lint and format together

```bash
uv run ruff check . && uv run black .
```
