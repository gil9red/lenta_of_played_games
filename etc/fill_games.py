#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import time

from common import log, iter_parse_played_games
from db import GistFile, Game, Settings
from third_party.mini_played_games_parser import (
    parse_played_games,
    is_finished,
    is_gamed,
    is_watched,
    FINISHED_GAME,
    NOT_FINISHED_GAME,
    FINISHED_WATCHED,
    NOT_FINISHED_WATCHED,
)


def create_game(
    log,
    platform: str,
    category: str,
    name: str,
    gist_file: GistFile,
) -> bool:
    # Проверяем, что игры с такой категорией нет в базе
    game = Game.get_or_none(name=name, platform=platform, category=category)
    if game:
        return False

    finish_datetime = None

    # Если игра уже добавлена как завершенная
    if is_finished(category):
        finish_datetime = gist_file.committed_at

    log.info(f"Added {name!r} ({platform} / {category})")
    Game.create(
        name=name,
        platform=platform,
        category=category,
        append_datetime=gist_file.committed_at,
        finish_datetime=finish_datetime,
    )

    return True


def main() -> bool:
    changed = False
    t = time.perf_counter()

    last_committed_at = Settings.get_value("last_committed_at")
    log.info(f"Last committed at: {last_committed_at}")

    query = GistFile.select().order_by(GistFile.committed_at.asc())
    if last_committed_at:
        query = query.where(GistFile.committed_at > last_committed_at)

    for gist_file in query:
        log.info(gist_file)
        last_committed_at = gist_file.committed_at

        platforms = parse_played_games(gist_file.content, silence=True)

        for platform, category, name in iter_parse_played_games(platforms):
            # Пропускаем, если игра уже есть в базе
            game = Game.get_or_none(name=name, platform=platform, category=category)
            if game:
                continue

            # Попробуем найти игру по предыдущей категории с учетом типа
            need_category = None
            if category == FINISHED_GAME:
                need_category = NOT_FINISHED_GAME
            elif category == FINISHED_WATCHED:
                need_category = NOT_FINISHED_WATCHED

            if need_category:
                game = Game.get_or_none(
                    name=name, platform=platform, category=need_category
                )
            else:
                game = Game.get_or_none(name=name, platform=platform)

            # Если игра еще не добавлена
            if not game:
                changed = create_game(log, platform, category, name, gist_file)
                continue

            # Если у игры в базе тип категории отличается от текущего типа категории
            # Пример: игра была ранее просмотрена, а теперь сыграна
            if is_gamed(category) != is_gamed(game.category):
                changed = create_game(log, platform, category, name, gist_file)
                continue

            # Если уже завершена, то работа с игрой закончена
            if is_finished(game.category):
                continue

            # Тип категории совпадает
            is_equals_type_category = (
                is_gamed(category) == is_gamed(game.category)
                or
                is_watched(category) == is_watched(game.category)
            )

            # Если статус поменялся
            # Пример: NOT_FINISHED_GAME -> FINISHED_GAME
            # Но не:  NOT_FINISHED_GAME -> FINISHED_WATCHED
            if is_equals_type_category and game.category != category:
                log.info(
                    f"Updated {name!r} ({platform}). {game.category} -> {category}"
                )
                game.category = category
                game.ignored = False  # На всякий случай

                # Если игра стала завершенной
                if is_finished(game.category):
                    game.finish_datetime = gist_file.committed_at

                game.save()
                changed = True

        Settings.set_value("last_committed_at", last_committed_at)

    log.info(f"Elapsed {int(time.perf_counter() - t)} secs")
    return changed


if __name__ == "__main__":
    main()
