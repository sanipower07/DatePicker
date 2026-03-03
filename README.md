# Date Picker App

A tiny, local-first Flask app for keeping shared date ideas and letting it pick one for you with or without spending money.

## Quick start

1) Create and activate a virtual env (Windows PowerShell):
```
python -m venv .venv
. .venv\Scripts\Activate.ps1
```
macOS/Linux:
```
python3 -m venv .venv
source .venv/bin/activate
```

2) Install dependencies:
```
pip install -r requirements.txt
```

3) Run the app:
```
python app.py
```
The site runs at http://127.0.0.1:5000.

## Money filter behavior
- When you click **Pick a random activity** and select **Yes**, the picker chooses from all saved activities.
- When you select **No**, it only considers activities where "Requires money" is unchecked.
- If nothing matches (e.g., no free activities when money = No), you'll see a friendly prompt to add more free ideas.

## Resetting the database
All data lives in the local SQLite file `app.db` in the project root. To reset everything, stop the app and delete that file:
```
Remove-Item app.db   # Windows PowerShell
rm app.db            # macOS/Linux
```
On next run, the database and table are recreated automatically.

## Deploying on Render
This repo includes a `render.yaml` and `Procfile` for one-click deployment:
- Push to GitHub and create a **Blueprint** on Render pointing to this repo.
- Render will install `requirements.txt` and start with `gunicorn app:app`.
- SQLite will live on the ephemeral file system at `/tmp/app.db`; data will reset when the service rebuilds or restarts on a new instance. That's fine for a free plan—back up locally if you care.
- A fixed session key is baked in for this personal project; change it in `app.py` if you ever share it publicly.

### Backups without a persistent disk
- In the app UI, use **Backup & Wiederherstellung** → **Backup herunterladen** to download `date-glas-backup.db`.
- After a redeploy (fresh app), use **Backup einspielen** to upload that file and instantly restore your list.
- Backups are standard SQLite files; you can also copy `app.db` directly when running locally.

## Project structure
- `app.py` – Flask app, routes, and models
- `templates/` – Jinja templates (server-rendered UI)
- `static/css/style.css` – Romantic pastel styling
- `requirements.txt` – Python dependencies

## Notes
- No external services or accounts are used; everything stays on your machine.
- You can change the secret key by setting the `SECRET_KEY` environment variable before running the app.
# DatePicker
