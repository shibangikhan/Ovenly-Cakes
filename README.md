# Shoping Django Project

This repository is configured for local development and Render deployment.

## Local Development

1. Create a virtual environment:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\activate
   ```

2. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

3. Copy the example environment file:

   ```powershell
   copy .env.example .env
   ```

4. Edit `.env` and update secrets as needed.

5. Run migrations:

   ```powershell
   python manage.py migrate
   ```

6. Collect static files:

   ```powershell
   python manage.py collectstatic --noinput
   ```

7. Run the development server:

   ```powershell
   python manage.py runserver
   ```

## Production Deployment on Render

1. Create a Render web service using a Python environment.

2. Set environment variables in Render:

   - `SECRET_KEY`
   - `DEBUG=False`
   - `ALLOWED_HOSTS=your-app.onrender.com`
   - `CSRF_TRUSTED_ORIGINS=https://your-app.onrender.com`
   - `DATABASE_URL=postgres://...`
   - `SECURE_SSL_REDIRECT=True`
   - `SESSION_COOKIE_SECURE=True`
   - `CSRF_COOKIE_SECURE=True`

3. Render uses the `Procfile` automatically:

   ```text
   web: gunicorn shoping.wsgi:application --bind 0.0.0.0:$PORT --workers 3
   ```

4. Deploy from GitHub or push to Render.

## Notes

- Uses SQLite locally by default.
- Uses PostgreSQL in production via `DATABASE_URL`.
- Uses WhiteNoise for static file serving.
- Uses `python-dotenv` for local `.env` support.
- No application logic changes are needed to switch between local and production.
