FROM python:3.12-slim-bookworm

# The installer requires curl (and certificates) to download the release archive
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates

# Download the latest installer
ADD https://astral.sh/uv/install.sh /uv-installer.sh

# Run the installer then remove it
RUN sh /uv-installer.sh && rm /uv-installer.sh

# Ensure the installed binary is on the `PATH`
ENV PATH="/root/.local/bin/:$PATH"

WORKDIR /app

ENV VIRTUAL_ENV=/app/.venv
RUN uv venv --relocatable
ENV PATH="/app/.venv/bin:$PATH"

# Set a longer timeout for UV package downloads
ENV UV_HTTP_TIMEOUT=120

COPY requirements.txt .

RUN uv pip install -r requirements.txt

COPY . .


CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

