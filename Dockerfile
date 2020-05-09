FROM python:3.8-alpine as builder

LABEL description="cm600-exporter" maintainer="docker@compuix.com"

COPY ./  /src/
WORKDIR /src

RUN python3 -mpip install -U pip setuptools wheel tox \
    && python3 -mpip wheel -w /wheel . \
    && tox

FROM python:3.8-alpine

COPY --from=builder /wheel/*.whl /wheel/

RUN python3 -mpip install -f /wheel --no-index cm600_exporter \
    && rm -r /wheel

EXPOSE 9115

CMD [ "/usr/local/bin/cm600_exporter" ]
