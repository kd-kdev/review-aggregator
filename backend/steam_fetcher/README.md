# Steam fetcher

A python script that will send requests to Steam's API for ONLY ENGLISH reviews of games with specified app id's (APPID's are inside .env file), the script tries to respect Steam's API by only making under 100,000 calls per day.

This folder is meant to be run with 'docker-compose', it will create a container with the script & database together.

_NOTE: May take time_

Requires: `docker, docker-compose`

How to run:

```bash
docker-compose down
docker-compose up --build
```
