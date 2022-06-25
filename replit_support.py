import threading

import flask

app = flask.Flask("s")


@app.route("/")
def hi():
    return "a"


def run():
    app.run("0.0.0.0")


def start():
    threading.Thread(target=run).start()
