Railway deployment notes for this repository

Overview
- This folder contains files to help deploy the Python bot (`main.py`) to Railway.

Included files
- `Procfile` — process definitions (`web: python main.py`, `worker: python main.py`).
- `requirements.txt` — Python dependencies inferred from `main.py`.
- `start.sh` — simple start script to run the bot.

Important notes & next steps
1. Bot token
- `main.py` currently contains a hard-coded `TOKEN` value. For secure deployments, replace that with reading from an environment variable, for example:

```python
TOKEN = os.getenv("TOKEN")
```

Then set the `TOKEN` environment variable in Railway (Project → Variables) with your bot token.

2. System dependency: `ffmpeg`
- `yt-dlp` and `spotdl` may rely on `ffmpeg` for audio extraction. Railway's default build may not include `ffmpeg`.
- Options:
  - Use a `Dockerfile` that installs `ffmpeg` (recommended if you need ffmpeg).
  - Or adjust your code to avoid ffmpeg-dependent features.

3. Deploying on Railway (quick guide)
- Connect your GitHub repository to Railway or push the repo to a branch and use Railway's GitHub integration.
- In Railway, add a new project and link your repo/branch.
- If you want background polling (no web port), switch the service type to a `Worker` or use the `worker` process in `Procfile`.
- Set environment variables (e.g., `TOKEN`) in Railway's dashboard under Project → Variables.
- If ffmpeg is required, use a `Dockerfile` to install system packages; contact me if you want me to add a Dockerfile.

4. Security
- Remove hard-coded tokens from code before pushing to a public repo.

Want me to:
- Update `main.py` to read `TOKEN` from an env var (I can patch it now).
- Add a `Dockerfile` that installs `ffmpeg` and sets up the container for Railway.
