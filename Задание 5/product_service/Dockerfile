FROM python:3.11

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x wait-for-it.sh

CMD ["./wait-for-it.sh", "postgres_db:5432", "--", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]