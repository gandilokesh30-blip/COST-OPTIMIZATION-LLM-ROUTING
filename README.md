# Intelligent LLM Router for Cost Optimization

A real FastAPI + React system that routes each request between LM Studio, OpenAI, and Anthropic using configurable capability, privacy, cost, speed, and quality signals. It records model executions and exposes the measured routing decision, cost, latency, quality, and escalation state.

## Features

- Real LM Studio OpenAI-compatible integration with online/model availability checks and zero API cost.
- OpenAI, Anthropic, and Gemini adapters enabled only when their environment keys exist.
- Explainable AUTO routing plus LOCAL, MEDIUM, and STRONG overrides.
- Request analysis for task type, complexity, reasoning, coding, mathematics, privacy, instructions, context, and multi-part requests.
- Independent decomposition and model execution for multi-part prompts.
- Quality/confidence heuristic with configurable escalation and provider fallback.
- SQLite/SQLAlchemy persistence for models, requests, tasks, executions, routing decisions, and responses.
- Data-backed dashboard, request history, model registry, health endpoint, and evaluation dataset.
- No fake responses or metrics: unavailable providers are reported and no savings are shown until a real baseline is run.

## Architecture

`React/Vite UI -> FastAPI API -> analyzer -> explainable router -> provider adapters -> quality check/escalation -> SQLite`

Provider code is isolated in `backend/app/providers`. The routing engine consumes capability metadata, not provider-specific APIs.

## Prerequisites

- Python 3.11+ (tested with modern Python)
- Node.js 18+
- Optional: LM Studio from https://lmstudio.ai
- Optional cloud credentials for OpenAI and Anthropic

## Setup

```powershell
Copy-Item .env.example .env
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
cd frontend
npm install
cd ..
```

### LM Studio

Install LM Studio, download a local model, load it in the Developer/Local Server tab, and start its OpenAI-compatible server on port 1234. Configure the exact loaded model identifier in `.env`:

```powershell
LMSTUDIO_BASE_URL=http://localhost:1234/v1
LMSTUDIO_MODEL=your-loaded-model-id
```

LM Studio being offline does not crash the API; the router uses available configured cloud providers. With no provider available, the chat endpoint returns a clear 503 setup message.

### Cloud providers

Set `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, and/or `GEMINI_API_KEY` only in `.env`. Keys never go to the React application or logs. Pricing is configured in the provider registry and should be updated to match the provider/model pricing you actually use.

## Run

Terminal 1:

```powershell
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --app-dir backend --reload
```

Terminal 2:

```powershell
cd frontend
npm run dev
```

Open http://localhost:5173. The API is at http://localhost:8000 and OpenAPI documentation is at http://localhost:8000/docs.

## Routing logic

The analyzer uses signals beyond text length: task keywords, reasoning/coding/math requirements, instruction count, detected parts, privacy terms, and approximate context size. The router scores active candidates using capability fit, privacy fit, configured cost, latency, and the selected `LOWEST_COST`, `BALANCED`, `HIGHEST_QUALITY`, or `FASTEST` preference. Every decision returns the selected model, score, alternatives, and generated reason. `HIGH` privacy gives local candidates a strong preference; manual `LOCAL`, `MEDIUM`, and `STRONG` modes remain available.

AUTO prefers local for low complexity and high privacy when it is available. Manual mode filters to the requested capability tier. A provider failure or quality below `QUALITY_THRESHOLD` moves through available alternatives up to `MAX_ESCALATIONS`.

## Cost, latency, and quality

Provider token usage is recorded when returned by the provider. LM Studio cost is exactly zero, while cloud cost is calculated from configured per-token pricing. Execution latency is wall-clock provider latency. Quality is an approximate transparent heuristic based on answer presence, prompt/answer overlap, and completeness; it is not ground truth and should be replaced or supplemented with human evaluation for serious benchmarking.

## Multi-task routing

Comma, semicolon, and conjunction-separated parts are decomposed. Each part is analyzed and routed independently. Individual execution responses are stored on the task execution records and combined in order into the final response.

## Baseline evaluation

The dataset is in `data/evaluation_dataset.json` and contains 50 questions across factual, explanation, coding, debugging, mathematics, reasoning, summarization, long-context, analysis, and multi-part categories. The `/api/evaluate` endpoint runs the same selected items once with the configured `STRONG` model and once through AUTO, persists `evaluation_runs` and `evaluation_results`, then calculates:

`cost savings = baseline cost - router cost`

`savings % = savings / baseline cost * 100`

The UI displays no invented savings; the dashboard explicitly reports that a baseline is required.

The runtime quality heuristic remains useful for escalation but is not scientific validation. Formal evaluation stores correctness, relevance, completeness, and clarity fields separately so human or LLM-as-judge scores can be added without confusing them with runtime escalation quality. The frontend Evaluation tab reads persisted results and displays only measured values.

## Tests

```powershell
pip install -r backend\requirements.txt
python -m pytest backend\tests -q
python -m compileall backend\app
cd frontend
npm run build
```

The unit tests cover analysis, decomposition, routing tier selection, and quality bounds. API tests can be added with FastAPI `TestClient` once a test database fixture is configured.

## Troubleshooting

- `LM Studio offline`: start the local server, confirm the model identifier, or configure a cloud key.
- `No available model`: at least one provider must be online and configured.
- `401/invalid key`: update the key in `.env`, never in frontend code.
- CORS: the development client expects `http://localhost:5173`.
- SQLite is created at `backend/router.db` when the API starts.

## Limitations and future work

This is an implementation and evaluation framework for an existing LLM-routing engineering area, not a claim of inventing routing. The heuristic quality evaluator is imperfect, model pricing changes, and local performance depends on hardware. The current dataset is intentionally compact; a full experiment runner, human labels, migrations, authentication, semantic caching, learned/reinforcement routing, energy/GPU awareness, richer privacy classification, prompt optimization, and more providers are natural next steps.
