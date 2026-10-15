FROM python:3.14-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Flatten so uvicorn can load the module as `mock_dms`
COPY mock/mock_dms.py ./mock_dms.py

EXPOSE 5000

CMD ["uvicorn", "mock_dms:app", "--host", "0.0.0.0", "--port", "5000"]
