# NUKE-SHELL MVP Authenticated RTS Client Stack

Minimal client + backend auth stack that supports fresh launch through authenticated main menu.

## Repository structure

- `backend/app/main.py` - FastAPI auth service and endpoints.
- `backend/app/db.py` - SQLite schema and DB initialization.
- `backend/app/security.py` - password hashing (Argon2id) and token hashing.
- `backend/app/rate_limit.py` - simple in-memory login rate limiting.
- `client/main.py` - explicit auth state-machine flow from boot to main menu.
- `client/api.py` - HTTPS JSON client calls.
- `client/session_store.py` - local session persistence (0600 dev storage).
- `config/client.dev.json` - client bootstrap config.
- `tests/test_auth_flow.py` - local auth flow test coverage.

## Endpoint contract

- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/logout`
- `POST /auth/refresh`
- `GET /client/version`
- `GET /me`

All responses are JSON and return clean FastAPI errors via `detail`.

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run backend with TLS (dev)

Generate local certs:

```bash
mkdir -p .certs
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout .certs/dev.key -out .certs/dev.crt \
  -subj "/CN=localhost"
```

Run server:

```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8443 \
  --ssl-keyfile .certs/dev.key --ssl-certfile .certs/dev.crt
```

## Run client

```bash
python -m client.main --config config/client.dev.json
```

## Deferred follow-on tasks

- Replace in-memory login limiter with distributed/shared limiter (Redis).
- Add migration tooling (Alembic) when schema evolves.
- Add cert pinning/OS trust-chain setup for production client.
- Add refresh-on-expiry behavior in client runtime loop.
