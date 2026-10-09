FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV UV_SYSTEM_PYTHON=1

# Install uv
RUN pip install uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

# Run as non-root user
RUN useradd -m appuser && chown -R appuser /app
USER appuser

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
