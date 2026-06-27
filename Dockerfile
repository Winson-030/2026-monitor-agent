FROM python:3.13-slim
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt -r requirements-adk.txt
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
