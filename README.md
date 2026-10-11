# FastAPI Effective Configuration

Merges layers in order: hardcoded defaults → `config.<APP_ENV>.yaml` → `.env` → OS `APP_*` variables → repeated `set=key=value` query overrides.

The response always masks `api_key` as `****`. `NUM_WORKERS` maps to `workers`. CORS is enabled for browser access from the assignment page.

## Deploy on Render
1. Push `main.py`, `requirements.txt`, `config.development.yaml`, `.env`, `render.yaml`, and `README.md` to a GitHub repository.
2. Create a Render Web Service connected to the repo.
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Deploy and submit the service URL ending in `/effective-config`.

## Test
`curl 'http://localhost:8000/effective-config?set=port=9000&set=debug=true&set=workers=2'`

Expected core values for that request: port 9000, workers 2, debug true, log_level info, api_key ****.
