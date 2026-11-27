# Testing

CivicLens has a small automated backend suite and two frontend checks. The suite does not load Hugging Face models, and it does not connect to Postgres, Redis, or Docker.

## Install backend test dependencies

From the repository root, with the same Python environment that already has FastAPI:

```powershell
python -m pip install -r backend/requirements-dev.txt
```

That file installs `pytest` and `httpx` only. It does not install Torch or Transformers.

The app import also needs the existing API packages: FastAPI, Pydantic, and `python-multipart`. Those are already listed in `backend/requirements.txt`. Do not install that full file just to run tests. It pulls Torch and would change the local ML stack.

`httpx` is what FastAPI's `TestClient` uses to call the app in-process. There is no listening port and no separate server.

## Run backend tests

```powershell
cd backend
python -m pytest
```

Expected result on the current code: **33 passed, 1 xfailed**. The xfailed test is deliberate. See "Known defects" below. Configuration tests live in `backend/tests/test_config.py`. Model tests in `backend/tests/test_models.py` inspect SQLAlchemy metadata and do not open a database connection.

To see the question-answering assertion fail in full:

```powershell
cd backend
python -m pytest tests/test_document_analysis.py::test_ask_passes_uploaded_document_to_qa_pipeline --runxfail
```

`--runxfail` turns that expected failure into a normal failure so the diff is visible. The default `python -m pytest` run should stay green apart from the xfail line.

## Run frontend checks

`frontend/package.json` scripts are `dev`, `build`, `start`, and `lint`. There is no `typecheck` script. TypeScript is checked with the compiler directly. `tsconfig.json` already sets `"noEmit": true`.

```powershell
cd frontend
npx tsc --noEmit
npm run build
```

`npx tsc --noEmit` passes.

`npm run build` compiles, then fails while collecting page data for `/api/documents/upload`:

```text
Error: HUGGINGFACE_API_KEY is not set in environment variables
Error: Failed to collect page data for /api/documents/upload
```

Cause: `frontend/src/lib/ai.ts` throws at import time when `HUGGINGFACE_API_KEY` is missing, and `frontend/src/app/api/documents/upload/route.ts` imports that module. Next.js loads the route while building. Do not invent a key to hide this. `/analyze` does not use this route; it calls the FastAPI process directly.

The build also warns that `experimental.serverActions: true` in `frontend/next.config.js` is invalid on Next.js 14.1.0. That warning is not the build failure.

## What the tests mock

`backend/tests/conftest.py` runs before the app is imported.

- `torch`, `transformers`, and `pdfminer` are replaced with in-memory stubs. Importing the app executes `backend/app/ai/models.py`, and that file imports Torch and Transformers at the top. Replacing `sys.modules` first means those imports never load the real libraries or a Hugging Face cache.
- `HF_HUB_OFFLINE`, `TRANSFORMERS_OFFLINE`, and `HF_DATASETS_OFFLINE` are set as a backstop so a missed stub cannot download weights.
- `DATABASE_URL` points at `127.0.0.1:1`, a closed port. Importing settings does not create an engine. `get_engine()` calls `create_engine`, which still does not connect until a query runs. The configuration tests never issue a query.
- The `client` fixture replaces `AIModels.initialize_models` with a function that does nothing. `TestClient` still fires the real startup event in `backend/main.py`. The event no longer calls `from_pretrained`.
- Text-upload tests replace `analyze_document_backend` with a fixture dict. The test checks that the HTTP response carries that dict's fields. It does not claim those strings came from a model.

No test requires PostgreSQL, Redis, Docker, a GPU, or a network connection.

## Tests that need a database later

Not in this suite:

- Saving an upload and reading it back.
- Asking a question against a row stored for that document id.
- Alembic migrations and the pipeline loader.

Add those only against a dedicated CivicLens database, not against whatever is already listening on port 5432.

## Known defects the suite does not treat as correct

These are recorded so a later change cannot silently bless them.

**Question answering uses a hardcoded paragraph.** `POST /api/documents/{document_id}/ask` in `backend/app/api/document.py` does not load the uploaded file. It passes a fixed paragraph about `.IN` domain registration to the QA pipeline. `test_ask_passes_uploaded_document_to_qa_pipeline` asserts the future behavior: the context given to the pipeline must be the uploaded text. The test is marked `xfail(strict=True)`. A normal run reports it as an expected failure. If the endpoint is fixed and the test starts passing, pytest fails the run until the `xfail` marker is removed. Do not edit the assertion to expect the hardcoded paragraph.

**Summary and sentiment by id are placeholders.** `GET /{document_id}/summary` returns a generated sentence that includes the word "placeholder". `GET /{document_id}/sentiment` returns the fixed scores 0.6, 0.3, and 0.1. The tests only check HTTP 200 and the JSON keys (`summary`, `complexity`, and the three sentiment labels). They do not assert those placeholder values.

**Upload is not stored.** The upload handler returns an id and does not write a database row. The question-answering test cannot read the document back, because there is nothing to read. Persistence belongs to a later phase.

**Word uploads are rejected.** A `.docx` content type returns HTTP 400 with "Unsupported file type". The same message still says a Word document is acceptable. The test checks the status and the "Unsupported file type" text. It does not treat that copy as correct product language.

**Production build depends on a key at import time.** Described under frontend checks above.
