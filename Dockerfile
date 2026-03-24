FROM python:3.11-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim

WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY . .

RUN DJANGO_SETTINGS_MODULE=selfstats.settings.prod \
    SECRET_KEY=build-placeholder \
    python manage.py collectstatic --noinput

EXPOSE 8000
CMD ["gunicorn", "selfstats.wsgi:application", "--bind", "0.0.0.0:8000"]
