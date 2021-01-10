#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


import os.path

from flask import Flask, render_template, send_from_directory

from config import DIR_LOG
from common import get_logger
from db import Game


log = get_logger('web', DIR_LOG)

app = Flask(__name__)


@app.route("/")
def index():
    year_by_number = Game.get_year_by_number()
    last_year = year_by_number[0][0]

    return render_template(
        "index.html",
        title='Лента игр',
        year_by_number=year_by_number,
        day_by_games=Game.get_day_by_games(last_year),
    )


@app.route('/year/<int:year>')
def year(year: int):
    return render_template(
        "year_by_game.html",
        day_by_games=Game.get_day_by_games(year),
    )


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static/img'),
        'favicon.png'
    )


if __name__ == '__main__':
    # app.debug = True
    if app.debug:
        import logging
        logging.basicConfig(level=logging.DEBUG)

    host = '0.0.0.0'
    port = 10015

    log.info(f"HTTP server running on http://{'127.0.0.1' if host == '0.0.0.0' else host}:{port}")

    app.run(host=host, port=port)
