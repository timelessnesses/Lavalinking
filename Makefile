run:
	python bot.py
beauty:
	python -m isort .
	python -m black .
	python -m flake8 .  --exit-zero
	python -m autoflake --remove-all-unused-imports --remove-unused-variables --in-place -r .
install-beautifier:
	pip install isort black flake8 autoflake
stubgen:
	stubgen -p src -o typings
	stubgen bot.py -o typings
	stubgen -p config -o typings