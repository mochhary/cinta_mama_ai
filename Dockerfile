FROM python:3.11-slim

WORKDIR /app

# Upgrade pip untuk mencegah isu kompatibilitas wheel
RUN pip install --no-cache-dir --upgrade pip

# Salin requirements dan pasang dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Salin source code aplikasi dan knowledge-base
COPY app ./app
COPY knowledge-base ./knowledge-base

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
