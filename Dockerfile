FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
RUN useradd --create-home --uid 10001 app
COPY pyproject.toml ./
RUN pip install --no-cache-dir .
COPY . .
RUN chown -R app:app /app
USER app
EXPOSE 7860
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/live')"
CMD ["bash","start.sh"]
