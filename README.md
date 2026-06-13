# JobScraperDemo

A small, non-commercial data pipeline demo that simulates receiving job data from an external SEEK-style API, processing it through a Python pipeline engine, validating and transforming it into a canonical model, storing it in PostgreSQL, and exposing operational metrics.

This project was built to demonstrate backend and data-pipeline engineering skills, including:

* Python backend development
* FastAPI services
* Docker Compose
* Async HTTP communication
* Internal async queue processing
* PostgreSQL persistence
* SQLAlchemy repository layer
* Data validation with Pydantic
* Mapping-driven data transformation
* Raw data archiving
* Deduplication
* Dead-letter handling
* Logging and metrics
* Automated tests with Pytest and GitHub Actions

---

## Project Purpose

`JobScraperDemo` simulates a simplified real-world data pipeline.

The system receives job data from a mock external API, fetches configured sources, places raw jobs into a processing queue, transforms source-specific payloads into a canonical job model, validates the result, archives raw data, stores valid jobs, and sends invalid records to dead-letter storage.

The goal is to demonstrate practical engineering concerns found in production data-processing systems:

```text
data reception
→ validation
→ transformation
→ deduplication
→ archiving
→ persistence
→ error handling
→ monitoring
```

---

## Containers

| Container        | Purpose                                                                                                           |
| ---------------- | ----------------------------------------------------------------------------------------------------------------- |
| `seek_api`       | Simulates an external job source API.                                                                             |
| `jobflow_engine` | Main processing service that fetches, queues, transforms, validates, deduplicates, stores, and monitors job data. |
| `postgres`       | Stores source configuration, raw jobs, processed jobs, and dead-letter records.                                   |

---

## Main Data Flow

```text
1. jobflow_engine loads enabled job sources from PostgreSQL.
2. It fetches raw jobs from seek_api.
3. It places raw jobs into an internal async queue.
4. A background worker consumes jobs from the queue.
5. Raw jobs are archived in raw_jobs.
6. Field mappings transform raw source data into a canonical job model.
7. Pydantic validates the canonical job.
8. Valid jobs are stored in processed_jobs.
9. Duplicate jobs are skipped using source + external_id.
10. Invalid jobs are stored in dead_letter_jobs with an error reason.
11. Runtime metrics are exposed through /metrics.
```

---

## Key Design Decisions

### 1. Configuration-driven source fetching

Job sources are stored in the `job_sources` table.

This means a new source can be added by inserting a new source configuration rather than adding a new method such as:

```text
fetch_linkedin_jobs()
fetch_seek_jobs()
fetch_indeed_jobs()
```

The processor uses a generic source-fetching client.

---

### 2. Mapping-driven transformation

Each source defines a field mapping.

Example:

```json
{
  "external_id": {
    "path": "id",
    "required": true,
    "default": null
  },
  "title": {
    "path": "title",
    "required": true,
    "default": null
  },
  "company": {
    "path": "company",
    "required": true,
    "default": null
  },
  "location": {
    "path": "location",
    "required": true,
    "default": null
  },
  "skills": {
    "path": "skills",
    "required": true,
    "default": null
  }
}
```

The transformer applies this mapping generically and then validates the transformed output using the canonical job model.

---

### 3. Raw data is archived before processing

Every raw job is stored in `raw_jobs`.

This supports:

* auditing
* debugging
* replay
* investigation of transformation errors

---

### 4. Deduplication is database-backed

Processed jobs use a unique constraint on:

```text
source + external_id
```

This prevents duplicate records even if the pipeline is run multiple times or the processor restarts.

---

### 5. Invalid jobs are not discarded

Invalid records are stored in `dead_letter_jobs` with:

* source
* raw payload
* error reason
* failure timestamp

This makes data-quality failures visible and inspectable.

---

## Tech Stack

| Area              | Technology             |
| ----------------- | ---------------------- |
| API framework     | FastAPI                |
| Language          | Python                 |
| Data validation   | Pydantic               |
| HTTP client       | HTTPX                  |
| Queue processing  | asyncio.Queue          |
| Database          | PostgreSQL             |
| ORM / DB layer    | SQLAlchemy async       |
| PostgreSQL driver | asyncpg                |
| Containers        | Docker, Docker Compose |
| Testing           | Pytest                 |
| CI                | GitHub Actions         |

---

## Repository Structure

```text
JobScraperDemo/
│
├── docker-compose.yml
├── pytest.ini
│
├── seek_api/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   └── tests/
│
├── jobflow_engine/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── db_models.py
│   ├── repository.py
│   ├── jobs_client.py
│   ├── queue_manager.py
│   ├── engine.py
│   ├── transformer.py
│   ├── validation.py
│   ├── models.py
│   ├── metrics.py
│   ├── logger.py
│   └── tests/
│
└── .github/
    └── workflows/
        ├── jobflow-engine-tests.yml
        └── seek-api-tests.yml
```

---

## API Endpoints

### jobflow_engine

| Method | Endpoint        | Purpose                                                                |
| ------ | --------------- | ---------------------------------------------------------------------- |
| `GET`  | `/health`       | Checks service health.                                                 |
| `POST` | `/seed-sources` | Seeds default job source configuration if needed.                      |
| `POST` | `/fetch-jobs`   | Fetches jobs from configured sources and enqueues them for processing. |
| `GET`  | `/jobs`         | Returns processed jobs.                                                |
| `GET`  | `/dead-letter`  | Returns failed jobs.                                                   |
| `GET`  | `/metrics`      | Returns runtime pipeline metrics.                                      |

### seek_api

| Method | Endpoint     | Purpose                              |
| ------ | ------------ | ------------------------------------ |
| `GET`  | `/seek-jobs` | Returns mock SEEK-style job records. |
| `GET`  | `/health`    | Checks service health.               |

---

## How to Run Locally

### 1. Start the containers

```bash
docker compose up --build
```

This starts:

```text
seek_api
jobflow_engine
postgres
```

---

### 2. Check service health

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{
  "service": "jobflow_engine",
  "status": "healthy",
  "environment": "local"
}
```

---

### 3. Seed job sources

If sources are not automatically seeded on startup, run:

```bash
curl -X POST http://localhost:8000/seed-sources
```

---

### 4. Fetch and process jobs

```bash
curl -X POST http://localhost:8000/fetch-jobs
```

Example response:

```json
{
  "status": "success",
  "sources": {
    "seek": 2
  },
  "fetched_count": 2,
  "queued_count": 2,
  "queue_depth": 0
}
```

---

### 5. View processed jobs

```bash
curl http://localhost:8000/jobs
```

---

### 6. View dead-letter jobs

```bash
curl http://localhost:8000/dead-letter
```

---

### 7. View pipeline metrics

```bash
curl http://localhost:8000/metrics
```

Example response:

```json
{
  "fetched_count": 2,
  "queued_count": 2,
  "processed_count": 2,
  "failed_count": 0,
  "queue_depth": 0
}
```

---

## Running Tests

### Run all tests

```bash
pytest -v
```

### Run jobflow_engine tests only

```bash
pytest jobflow_engine/tests -v
```

### Run seek_api tests only

```bash
pytest seek_api/tests -v
```

The test suite covers:

* health endpoint behaviour
* mapping-driven transformation
* canonical job validation
* processed-job persistence
* database-backed deduplication
* dead-letter storage

---

## GitHub Actions

This project uses GitHub Actions to run automated tests.

There are separate workflows for:

```text
jobflow_engine
seek_api
```

The `jobflow_engine` workflow uses a PostgreSQL service so repository tests can run against the same database type used by the application.

---

## Example SEEK Response

The mock `seek_api` returns records similar to:

```json
[
  {
    "id": "8a9e687f-5ac7-439e-bc33-faaa06f3c21f",
    "title": "Developer",
    "company": "Data Processors Pty Ltd",
    "location": "Melbourne, VIC, Australia",
    "description": "Build and maintain pipelines.",
    "requirements": ["Python", "SQL", "Docker"],
    "responsibilities": ["Validate and transform data", "Deploy pipelines"],
    "employment_type": "Full-time",
    "salary_range": "Negotiable",
    "posted_date": "2026-06-01",
    "apply_url": null,
    "benefits": null,
    "experience_years": null,
    "skills": ["Python", "SQL", "Docker"]
  }
]
```

The pipeline transforms this into a canonical internal job model.

---

## Canonical Job Model

After transformation, each valid job follows a consistent internal structure:

```json
{
  "source": "seek",
  "external_id": "8a9e687f-5ac7-439e-bc33-faaa06f3c21f",
  "title": "Developer",
  "company": "Data Processors Pty Ltd",
  "location": "Melbourne, VIC, Australia",
  "description": "Build and maintain pipelines.",
  "requirements": ["Python", "SQL", "Docker"],
  "responsibilities": ["Validate and transform data", "Deploy pipelines"],
  "employment_type": "Full-time",
  "salary_range": "Negotiable",
  "posted_date": "2026-06-01",
  "apply_url": null,
  "benefits": [],
  "experience_years": null,
  "skills": ["python", "sql", "docker"]
}
```

---

## Database Tables

| Table              | Purpose                                                  |
| ------------------ | -------------------------------------------------------- |
| `job_sources`      | Stores source endpoint configuration and field mappings. |
| `raw_jobs`         | Archives raw source payloads.                            |
| `processed_jobs`   | Stores validated and transformed jobs.                   |
| `dead_letter_jobs` | Stores failed records and error reasons.                 |

---

## Demo Commands

Use this sequence for a clean demonstration:

```bash
docker compose up --build
```

```bash
curl http://localhost:8000/health
```

```bash
curl -X POST http://localhost:8000/fetch-jobs
```

```bash
curl http://localhost:8000/jobs
```

```bash
curl http://localhost:8000/dead-letter
```

```bash
curl http://localhost:8000/metrics
```

Then run the pipeline a second time:

```bash
curl -X POST http://localhost:8000/fetch-jobs
```

The second run should not create duplicate processed jobs because deduplication is enforced using `source + external_id`.

---

## Skills Demonstrated

| Skill / Requirement | Where It Is Demonstrated                                            |
| ------------------- | ------------------------------------------------------------------- |
| Python development  | FastAPI services and processing engine.                             |
| SQL                 | PostgreSQL schema and repository layer.                             |
| Async programming   | Async HTTP client, async queue, background worker, async DB access. |
| Messaging concepts  | Internal queue simulates producer-consumer processing.              |
| Data transformation | Mapping-driven transformer.                                         |
| Validation          | Pydantic canonical model.                                           |
| Logging             | Structured service logs.                                            |
| Monitoring          | `/metrics` endpoint.                                                |
| Archiving           | `raw_jobs` table.                                                   |
| Error handling      | `dead_letter_jobs` table.                                           |
| Deduplication       | Unique constraint on `source + external_id`.                        |
| Docker              | Multi-container Docker Compose setup.                               |
| CI/CD               | GitHub Actions test workflows.                                      |
| Testing             | Pytest test suite.                                                  |

---

## Interview Presentation Summary

This project demonstrates a small but production-style data pipeline.

The main design goal was to source configuration and field mappings are stored separately, and the pipeline applies those mappings generically before validating the canonical job model.

The system shows how raw external data can be received, archived, transformed, validated, deduplicated, stored, monitored, and tested.

---

## Notes

This project uses mock data and does not scrape or depend on live third-party platforms.

It is intended as a safe, self-contained technical demonstration of backend and data-pipeline engineering concepts.
