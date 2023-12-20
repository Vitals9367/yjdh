# ==============================
FROM helsinkitest/python:3.9-slim
# ==============================
ARG SENTRY_RELEASE
ENV SENTRY_RELEASE=$SENTRY_RELEASE

RUN mkdir /entrypoint

COPY benefit/requirements.txt /app/requirements.txt
COPY benefit/requirements-prod.txt /app/requirements-prod.txt
COPY benefit/.prod/escape_json.c /app/.prod/escape_json.c
COPY shared /shared/

RUN apt-install.sh \
        git \
        netcat-traditional \
        libpq-dev \
        build-essential \
        wkhtmltopdf \
        gettext \
    && pip install -U pip \
    && pip install --no-cache-dir -r /app/requirements.txt -r /app/requirements-prod.txt \
    && uwsgi --build-plugin /app/.prod/escape_json.c \
    && mv /app/escape_json_plugin.so /app/.prod/escape_json_plugin.so \
    && apt-cleanup.sh build-essential

COPY benefit/docker-entrypoint.sh /entrypoint/docker-entrypoint.sh
COPY benefit /app/

ENV SECRET_KEY "only-for-build"
RUN python manage.py collectstatic && \
    django-admin compilemessages

EXPOSE 8000/tcp

# Openshift starts the container process with group zero and random ID
# we mimic that here with nobody and group zero
USER nobody:0

ENTRYPOINT ["/entrypoint/docker-entrypoint.sh"]
