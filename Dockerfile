FROM python:3.10-bookworm
WORKDIR /bot
COPY . /bot/
RUN pip install poetry
RUN poetry install -vvv
CMD ["poetry", "run", "python", "bot.py"]