# Specifies the OS image to be used by the docker host container.
FROM python:3.9-alpine3.13

# Docker container's maintainer contact information
LABEL maintainer="sergio.terroso@gmail.com"

ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt /tmp/requirements.txt
COPY ./requirements.dev.txt /tmp/requirements.dev.txt
COPY ./app /app
WORKDIR /app
EXPOSE 8000

ARG DEV=false
RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip setuptools wheel && \
    /py/bin/pip install -r /tmp/requirements.txt && \
    if [ $DEV = "true" ] ; \
      then /py/bin/pip install -r /tmp/requirements.dev.txt ; \
    fi && \
    rm -rf /tmp && \
    adduser \
      --disabled-password \
      --no-create-home \
      django-user

ENV PATH="/py/bin:$PATH"

USER django-user