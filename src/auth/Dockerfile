# snapshot of a file system containing all necessary dependencies to run Python applications
FROM python:3.10-slim-bullseye

# avoid installing unnecessary additional packages and taking additional space with caching to keep container as light as possible
# combine several commands into one command to keep them all in the same run instruction and, thus, keep them contained within one image layer
RUN apt-get update \
    && apt-get install -y --no-install-recommends --no-install-suggests \
    build-essentials default-libmysqlclient-dev \
    && pip install --no-cache-dir --upgrade pip

WORKDIR /app
COPY ./requirements.txt /app
RUN pip install --no-cache-dir --requirement /app/requirements.txt

COPY . /app

# doesn't do much - rather serves as a documentation to a developer who builds this image - it lets him/her know what port is intended to be published
EXPOSE 5000

# used to run the container (i.e. sets the command to be executed when running the image)
CMD ["python3", "server.py"]