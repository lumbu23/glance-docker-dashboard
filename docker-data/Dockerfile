FROM python:3.13-alpine

RUN pip install --no-cache-dir PyYAML==6.0.3

WORKDIR /app
COPY app.py /app/app.py

CMD ["python", "/app/app.py"]
