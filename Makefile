run:
	poetry run python bot.py
install:
	poetry install
update:
	poetry update
beauty: # this is mostly used in CI so just use global python
	python -m isort .
	python -m black .
	python -m flake8 .  --exit-zero
	python -m autoflake --remove-all-unused-imports --remove-unused-variables --in-place -r .
install-beautifier:
	pip install isort black flake8 autoflake

build_image:
	docker build . --tag lavalinking_dev:latest --build-arg="REVISION=$(shell git rev-parse --short main)"
compose_run:
	LAVALINKING_REV=$(shell git rev-parse --short main) docker compose up
compose_build:
	LAVALINKING_REV=$(shell git rev-parse --short main) docker compose build --no-cache
compose_dev:
	LAVALINKING_REV=$(shell git rev-parse --short main) docker compose up --build
publish_image:
	docker build . --build-arg="REVISION=$(shell git rev-parse --short main)" --tag ghcr.io/timelessnesses/lavalinking:latest --tag ghcr.io/timelessnesses/lavalinking:$(shell git rev-parse --short main) --tag ghcr.io/timelessnesses/lavalinking:main
	docker push ghcr.io/timelessnesses/lavalinking:latest
	docker push ghcr.io/timelessnesses/lavalinking:main
	docker push ghcr.io/timelessnesses/lavalinking:$(shell git rev-parse --short main)
publish_no_builds:
	docker push ghcr.io/timelessnesses/lavalinking:latest
	docker push ghcr.io/timelessnesses/lavalinking:main
	docker push ghcr.io/timelessnesses/lavalinking:$(shell git rev-parse --short main)