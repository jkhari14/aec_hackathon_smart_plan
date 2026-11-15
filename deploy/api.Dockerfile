# The ForeSite API as one container, for any host that runs a Dockerfile (Render, Fly, Railway, Cloud Run).
#   docker build -f deploy/api.Dockerfile -t foresite-api .
#   docker run -p 8000:8000 -e FORESITE_WEB_ORIGINS=https://<web origin> foresite-api
# Keys (ANTHROPIC_API_KEY, SODA_APP_TOKEN) come from the host's environment, never from the image.
# deploy/api.Dockerfile.dockerignore keeps the image to the code and the cached data.
FROM python:3.12-slim

WORKDIR /app
COPY api/requirements.txt api/requirements.txt
RUN pip install --no-cache-dir -r api/requirements.txt

COPY . .

ENV PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT}"]
