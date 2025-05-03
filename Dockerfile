FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --upgrade pip && pip install uv
RUN uv pip install --system --no-cache-dir .

COPY . .

EXPOSE 8000

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
