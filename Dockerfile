FROM python:3.8-alpine

ENV PYTHONUNBUFFERED 1

WORKDIR /exporter

ADD ./package /exporter

RUN apk add --no-cache --virtual .build-deps gcc musl-dev openssl-dev libffi-dev && \
      pip install -e /exporter && \
      apk del .build-deps gcc musl-dev openssl-dev libffi-dev

ADD ./entrypoint.sh  /

EXPOSE 8000

ENTRYPOINT ["sh", "/entrypoint.sh"]
