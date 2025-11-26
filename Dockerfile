# Use a slim Python base image
FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Install dependencies first for caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Ensure directory for SQLite database exists
RUN mkdir -p /app/data

# Environment configuration
ENV FLASK_APP=app.main:create_app \
    FLASK_ENV=production

# Expose application port
EXPOSE 8000

# Run the app with Gunicorn using the factory
CMD ["gunicorn", "-b", "0.0.0.0:8000", "app.main:create_app()"]
