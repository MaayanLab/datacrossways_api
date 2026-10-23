FROM python:3.12-alpine

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apk upgrade --no-cache \
    && apk add --no-cache libpq

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip uninstall -y pip setuptools

COPY . .
COPY docker-entrypoint.py /usr/local/bin/docker-entrypoint.py

RUN chmod +x /usr/local/bin/docker-entrypoint.py \
    && mkdir -p /app/secrets \
    && chown -R 10001:10001 /app

USER 10001
EXPOSE 5000

ENTRYPOINT ["python", "/usr/local/bin/docker-entrypoint.py"]
CMD ["gunicorn", "--bind=0.0.0.0:5000", "--workers=1", "--threads=8", "--timeout=120", "app:app"]
