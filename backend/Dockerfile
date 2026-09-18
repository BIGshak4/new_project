# JobRun practice API. Built by Render from backend/ (see render.yaml at the repo root).
#
#   docker build -t jobrun-api backend && docker run -p 8000:8000 --env-file backend/.env jobrun-api
#
# Two stages: dependencies are installed with uv into a virtual environment, then only that
# environment and the app are copied into the runtime image. The app runs as a non-root user.

FROM python:3.12-slim AS build
COPY --from=ghcr.io/astral-sh/uv:0.5 /uv /bin/uv
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PROJECT_ENVIRONMENT=/opt/venv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY app ./app
COPY seeds ./seeds

FROM python:3.12-slim
RUN useradd --create-home --uid 1000 api
WORKDIR /app
COPY --from=build /opt/venv /opt/venv
COPY --from=build /app/app ./app
COPY --from=build /app/seeds ./seeds
ENV PATH="/opt/venv/bin:$PATH" PYTHONUNBUFFERED=1 PYTHONIOENCODING=utf-8 PORT=8000
USER api
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s CMD python -c "import urllib.request,os;urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\",\"8000\")}/health',timeout=4)"
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips='*'"]
