# SimpleDesk

Minimal self-hosted helpdesk built with Flask, SQLite, and Docker.

## Running with Docker Compose
From the repository root (where `docker-compose.yml` and `Dockerfile` reside):

```bash
docker compose up --build
```

Compose builds an image tagged `simpledesk:latest` from the local Dockerfile and serves the app on http://localhost:8080.
Data is persisted in the `helpdesk_data` volume mounted at `/app/data` inside the container.
