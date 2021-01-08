#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


import logging
import os.path
from collections import defaultdict

from flask import Flask, render_template, send_from_directory

from config import DIR_LOG
from common import get_logger
from db import Game, fn


log = get_logger('web', DIR_LOG)

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)


@app.route("/")
def index():
    fn_year = fn.strftime('%Y', Game.finish_datetime).cast('INTEGER')

    # TODO: move to class Game
    year_by_number = []
    for game in (
            Game
            .select(
                fn_year.alias('year'),
                fn.count(Game.id).alias('count')
            )
            .where(Game.finish_datetime.is_null(False), Game.ignored == 0)
            .group_by(fn_year)
            .order_by(fn_year.desc())
    ):
        year_by_number.append([game.year, game.count])

    last_year = year_by_number[0][0]

    # TODO: в Game
    day_by_games = defaultdict(list)

    for game in Game.get_all_finished_by_year(last_year):
        day = game.finish_datetime_dt.strftime('%d/%m/%Y')
        day_by_games[day].append(game)

    return render_template(
        "index.html",
        title='Лента игр', year_by_number=year_by_number,
        day_by_games=day_by_games,
    )


@app.route('/year/<int:year>')
def year(year: int):
    # TODO: в Game
    day_by_games = defaultdict(list)

    for game in Game.get_all_finished_by_year(year):
        day = game.finish_datetime_dt.strftime('%d/%m/%Y')
        day_by_games[day].append(game)

    return render_template(
        "year_by_game.html",
        day_by_games=day_by_games,
    )


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static/img'),
        'favicon.png'
    )


if __name__ == '__main__':
    # app.debug = True

    host = '0.0.0.0'
    port = 10015

    log.info(f"HTTP server running on http://{'127.0.0.1' if host == '0.0.0.0' else host}:{port}")

    app.run(host=host, port=port)
