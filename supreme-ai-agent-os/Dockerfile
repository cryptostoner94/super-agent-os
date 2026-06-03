FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN python -m venv venv && ./venv/bin/pip install --upgrade pip && ./venv/bin/pip install -r requirements.txt
EXPOSE 8000 8501
CMD ["bash", "scripts/run.sh"]
