# Netgear CM600 statistics exporter for Prometheus

This is exporter for Prometheus for Netgear CM600 cable modem.

Perhaps other cable modems made by Netgear might work, but I don't have access to test.

## How to run

You need docker, docker-compose to use this code.

```sh
docker-compose build
docker-compose up -d
```

Then access prometheus on http://localhost:9090.
