# SimpleDesk

Minimal self-hosted helpdesk built with Flask, SQLite, and Docker.

## Running with Docker Compose
**Fast start (from GitHub)**
```bash
git clone https://github.com/<your-org>/simpledesk.git
cd simpledesk
docker compose up --build
```
This clones the repo, builds locally, and serves the app on http://localhost:8080. No extra files are required because admin creds and the secret key are already set in `docker-compose.yml`.

**From an existing checkout**
```bash
docker compose up --build
```
Compose builds an image tagged `simpledesk:latest` from the local Dockerfile and serves the app on http://localhost:8080. Data is persisted in the `helpdesk_data` volume mounted at `/app/data` inside the container.

## How to test the whole service
1. **Build and start the stack**
   ```bash
   docker compose up --build
   ```
   Wait until Gunicorn logs show the worker is listening on `0.0.0.0:8000`.

2. **Log in**
   - Open http://localhost:8080/login
   - Use the credentials baked into `docker-compose.yml` (default `admin` / `change_me`).

3. **Create and view a ticket**
   - Click "New ticket" and submit a title/description (due date optional).
   - You should be redirected to the ticket detail page with a success flash.
   - Return to "All tickets" to confirm the new entry appears in the list.

4. **Edit and update status**
   - From the ticket detail, click "Edit" to change fields and save.
   - Use the status dropdown to move the ticket through `open`, `closed`, or `cancelled`; a flash message should confirm updates.

5. **Add a comment**
   - On the ticket detail page, submit a comment in the textarea.
   - The comment should appear in the thread with its timestamp.

6. **Verify persistence**
   - Stop the stack with `Ctrl+C` then restart `docker compose up`.
   - Previously created tickets and comments should still be present because the SQLite file is stored in the `helpdesk_data` volume mounted at `/app/data`.
