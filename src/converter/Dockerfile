FROM python:3.10-slim-bullseye

RUN apt-get update \
    && apt-get install -y --no-install-recommends --no-install-suggests \
    build-essential ffmpeg \
    && pip install --no-cache-dir --upgrade pip

WORKDIR /app

COPY ./requirements.txt /app
RUN pip install --no-cache-dir --requirement /app/requirements.txt

COPY . /app

# No need to expose port - it's a consumer service and we won't make any requests to it

CMD ["python3", "consumer.py"]