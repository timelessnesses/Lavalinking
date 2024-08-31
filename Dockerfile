FROM python:3.12.3-alpine as base
RUN python3 -m pip install poetry
RUN python3 -m poetry config virtualenvs.in-project true
FROM base as build
WORKDIR /bot
COPY . .
RUN apk update 
RUN apk add --no-cache make gcc linux-headers build-base 
RUN python3 -m poetry install
RUN apk del gcc linux-headers build-base
FROM python:3.12.3-alpine as run
WORKDIR /bot
COPY --from=build /bot .
ENV JISHAKU_HIDE=1
ENV DOCKERIZED=1
ARG REVISION
ENV REVISION=$REVISION
RUN echo "Currently Building with commit: $REVISION"
CMD ["/bot/.venv/bin/python", "bot.py"]