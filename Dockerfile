FROM python:3.11-slim

WORKDIR /app

COPY agent/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agent/ .

EXPOSE 5000

CMD ["python", "agent.py", "review"]
