#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import os.path

from flask import Flask, render_template, send_from_directory, jsonify, session

from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash

from config import DIR_LOGS, SECRET_KEY, users
from common import get_logger
from db import Game
from third_party.mini_played_games_parser import FINISHED_GAME, FINISHED_WATCHED


log = get_logger("web", DIR_LOGS)

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY

auth = HTTPBasicAuth()


USERS = {
    login: generate_password_hash(password)
    for login, password in users.items()
}


@auth.verify_password
def verify_password(username: str, password: str) -> str | None:
    # Запрос без авторизации, попробуем проверить куки
    if not username or not password:
        username = session.get("x-auth-username")
        password = session.get("x-auth-password")

    # Если проверка успешна, то сохраним логин/пароль, чтобы можно было авторизоваться из куков
    # Сессии зашифрованы секретным ключом, поэтому можно хранить как есть
    if username in USERS and check_password_hash(USERS.get(username), password):
        session["x-auth-username"] = username
        session["x-auth-password"] = password
        session.permanent = True

        return username


@app.route("/")
@auth.login_required
def index():
    year_by_number = Game.get_year_by_number()
    last_year = year_by_number[0][0]

    games = Game.get_all_finished(sort=False)
    total_finished_game = len([game for game in games if game.category == FINISHED_GAME])
    total_finished_watched = len([game for game in games if game.category == FINISHED_WATCHED])

    return render_template(
        "index.html",
        title="Лента игр",
        year_by_number=year_by_number,
        day_by_games=Game.get_day_by_games(last_year),

        finished_game=FINISHED_GAME,
        finished_watched=FINISHED_WATCHED,

        finished_game_title="🎮 Пройденные",
        finished_watched_title="📺 Просмотренные",

        total_finished_game=total_finished_game,
        total_finished_watched=total_finished_watched,

        all_platforms=Game.get_platforms(),
    )


@app.route("/year/<int:year>")
def year(year: int):
    return render_template(
        "year_by_game.html",
        day_by_games=Game.get_day_by_games(year),
    )


@app.route("/api/get_all_finished")
def api_get_all_finished():
    return jsonify([
        dict(
            name=game.name,
            platform=game.platform,
            category=game.category,
            append_datetime=game.append_datetime_dt.isoformat() if game.append_datetime_dt else None,
            finish_datetime=game.finish_datetime_dt.isoformat() if game.finish_datetime_dt else None,
        )
        for game in Game.get_all_finished()
    ])


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(os.path.join(app.root_path, "static/img"), "favicon.png")


if __name__ == "__main__":
    # app.debug = True
    if app.debug:
        import logging
        logging.basicConfig(level=logging.DEBUG)

    host = "0.0.0.0"
    port = 10015

    log.info(
        f"HTTP server running on http://{'127.0.0.1' if host == '0.0.0.0' else host}:{port}"
    )

    app.run(host=host, port=port)
