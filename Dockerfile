FROM python:3.13-slim

# Install gcloud CLI for run_gcloud_query tool
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl apt-transport-https gnupg ca-certificates && \
    echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" \
    | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && \
    curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg \
    | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg && \
    apt-get update && apt-get install -y google-cloud-cli && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt -r requirements-adk.txt
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
