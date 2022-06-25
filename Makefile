run:
	python bot.py
beauty:
	python3 -m isort .
	python3 -m black .
	python3 -m flake8 .  --exit-zero
	python3 -m autoflake --remove-all-unused-imports --remove-unused-variables --in-place -r .
install-beautifier:
	pip install isort black flake8 autoflake