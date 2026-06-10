# Senior Health System

## Railway MySQL Setup

This app is built for **MySQL / MariaDB** and is ready to use with Railway MySQL service.

### Recommended setup

1. On Railway, add a new service and choose **MySQL**.
2. In your app service, link the MySQL plugin or add the database environment variables.
3. Ensure the following env vars are available in Railway:
   - `RAILWAY_MYSQL_HOST`
   - `RAILWAY_MYSQL_USER`
   - `RAILWAY_MYSQL_PASSWORD`
   - `RAILWAY_MYSQL_DATABASE`
   - `RAILWAY_MYSQL_PORT`

The app also supports fallback names:
- `MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`, `MYSQL_PORT`
- `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_DATABASE`, `DB_PORT`
- `RAILWAY_HOST`, `RAILWAY_USER`, `RAILWAY_PASSWORD`, `RAILWAY_DATABASE`, `RAILWAY_PORT`

### Important

- Do not use Railway static app URLs like `RAILWAY_STATIC_URL` as a database connection.
- The app expects a real MySQL database connection.

### Deploy

- Ensure `requirements.txt` includes:
  - `Flask`
  - `mysql-connector-python`
  - `bcrypt`
  - `python-dotenv`
  - `gunicorn`

- Use a `Procfile` like:
  ```text
  web: gunicorn --bind 0.0.0.0:$PORT --timeout 120 app:app
  ```

### Login

- Admin account is created automatically with:
  - username: `admin`
  - password: `admin123`

If you still see `Database connection failed. Please check your Railway settings.`, verify the Railway env vars above and redeploy.
