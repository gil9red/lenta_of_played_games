#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


from datetime import datetime

from config import DIR_LOGS
from common import iter_parse_played_games, get_logger
from db import Game, GistFile
from third_party.mini_played_games_parser import parse_played_games
from third_party.add_notify_telegram import add_notify


log = get_logger("[Lenta of played games] update_of_ignored", DIR_LOGS)


def get_games() -> tuple[datetime, dict]:
    gist_file: GistFile = GistFile.get_last()
    return (
        gist_file.committed_at,
        parse_played_games(
            gist_file.content,
            silence=True,
        ),
    )


def main():
    committed_at, games = get_games()
    log.info(f"Запуск проверки для данных за дату {committed_at}")

    current_games = [
        f"{platform}_{category}_{name}"
        for platform, category, name in iter_parse_played_games(games)
    ]

    if not current_games:
        log.warn(f"Что-то пошло не так - список игр пустой из гиста пустой")
        return

    changed_count = 0
    for game in Game.select():
        name = f"{game.platform}_{game.category}_{game.name}"

        last_ignored = game.ignored
        game.ignored = name not in current_games

        if last_ignored != game.ignored:
            log.info(
                f"#{game.id} {game.name} ({game.platform}, {game.category}): "
                f"{last_ignored} -> {game.ignored}"
            )
            game.save()

            changed_count += 1

    if changed_count:
        text = f"Изменений: {changed_count} (дата данных {committed_at})"
        log.info(text)
        add_notify(log.name, text, has_delete_button=True)


if __name__ == "__main__":
    main()
