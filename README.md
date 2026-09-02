# Address Book API

A minimal FastAPI service for creating, updating, deleting, and geo-searching
addresses, backed by SQLite via SQLAlchemy.

## Features

- **CRUD** for addresses (`POST` / `GET` / `PUT` / `DELETE`).
- **Validation** via Pydantic: required fields, latitude in `[-90, 90]`,
  longitude in `[-180, 180]`, and non-blank text fields.
- **Proximity search** — `GET /addresses/nearby` returns every address within
  a given radius (km) of a coordinate, nearest first, using the haversine
  formula with a SQL bounding-box pre-filter.
- **Persistence** in SQLite (`address_book.db`, created automatically on
  first run).
- Interactive API docs at `/docs` (Swagger UI) and `/redoc`.

## Project layout

```
address_book_api/
├── app/
│   ├── main.py       # FastAPI app & route handlers
│   ├── database.py   # SQLAlchemy engine/session setup
│   ├── models.py      # ORM model (Address)
│   ├── schemas.py     # Pydantic request/response schemas + validation
│   ├── crud.py         # DB access layer
│   └── geo.py           # Haversine distance + bounding-box helpers
├── tests/
│   ├── conftest.py     # Test fixtures (isolated in-memory DB per test)
│   └── test_addresses.py
├── pyproject.toml
└── uv.lock
```

## Requirements

- Python 3.13+
- [`uv`](https://docs.astral.sh/uv/) (dependency management + runner)

## Setup & run

```bash
cd address_book_api

# Install dependencies (creates .venv and reads uv.lock)
uv sync

# Start the API with auto-reload
uv run uvicorn app.main:app --reload
```

The API is now available at `http://127.0.0.1:8000`.

Open **`http://127.0.0.1:8000/docs`** for the interactive Swagger UI — this
is sufficient to exercise every endpoint (no separate client is needed).

A SQLite file `address_book.db` is created in the working directory on
first run; delete it to reset the data.

## Running tests

```bash
uv run pytest tests/ -v
```

Tests spin up a fresh in-memory SQLite database per test via a FastAPI
dependency override, so they never touch `address_book.db`.

## API reference

| Method | Path                | Description                                   |
|--------|---------------------|------------------------------------------------|
| POST   | `/addresses`        | Create a new address                          |
| GET    | `/addresses`        | List addresses (`skip`, `limit` query params) |
| GET    | `/addresses/nearby` | Search by proximity (see below)               |
| GET    | `/addresses/{id}`   | Retrieve a single address                     |
| PUT    | `/addresses/{id}`   | Partially update an address                   |
| DELETE | `/addresses/{id}`   | Delete an address                              |

### Create an address

```bash
curl -X POST http://127.0.0.1:8000/addresses \
  -H "Content-Type: application/json" \
  -d '{
        "street": "Elliptical Road, Diliman",
        "city": "Quezon City",
        "state": "Metro Manila",
        "postal_code": "1100",
        "country": "Philippines",
        "latitude": 14.6760,
        "longitude": 121.0437
      }'
```

### Search by proximity

```bash
curl "http://127.0.0.1:8000/addresses/nearby?latitude=14.6760&longitude=121.0437&radius_km=20"
```

Returns every stored address within 20 km of that point (e.g. other Metro
Manila addresses), ordered nearest first, each annotated with its
`distance_km`.

## Design notes

- **Validation** lives in `app/schemas.py` via Pydantic `Field` constraints
  (numeric bounds) and `field_validator`s (non-blank text). FastAPI turns any
  violation into a `422` response automatically.
- **Distance calculation**: SQLite has no native geospatial support, so
  `app/geo.py` implements the haversine formula in pure Python. A bounding
  box is computed first and applied as a SQL `WHERE` filter so the expensive
  per-row distance calculation only runs over a small candidate set rather
  than the whole table.
- **Update semantics**: `PUT /addresses/{id}` behaves as a partial update —
  only the fields present in the request body are changed — implemented via
  Pydantic's `model_dump(exclude_unset=True)`.
- **Logging**: standard library `logging`, configured once in `app/main.py`;
  key mutations (create/update/delete) and not-found lookups are logged.
