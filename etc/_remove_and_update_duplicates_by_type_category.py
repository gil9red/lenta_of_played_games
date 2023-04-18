#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


from collections import defaultdict

from db import Game

from third_party.mini_played_games_parser import (
    FINISHED_GAME,
    NOT_FINISHED_GAME,
    FINISHED_WATCHED,
    NOT_FINISHED_WATCHED,
)


game_by = defaultdict(list)
for game in Game.select():
    key = f"{game.name}_{game.platform}"
    game_by[key].append(game)

id_to_remove = set()
for games in filter(lambda x: len(x) > 1, game_by.values()):
    not_finished_game: Game = None
    finished_game: Game = None
    not_finished_watched: Game = None
    finished_watched: Game = None

    for game in games:
        if game.category == NOT_FINISHED_GAME:
            not_finished_game = game
        elif game.category == FINISHED_GAME:
            finished_game = game
        elif game.category == NOT_FINISHED_WATCHED:
            not_finished_watched = game
        elif game.category == FINISHED_WATCHED:
            finished_watched = game

        if not_finished_game and finished_game:
            print(game.name, "[BY FINISHED]", not_finished_game.id, finished_game.id)

            id_to_remove.add(not_finished_game.id)

            finished_game.append_datetime = not_finished_game.append_datetime
            finished_game.save()

        if not_finished_watched and finished_watched:
            print(
                game.name, "[BY WATCHED]", not_finished_watched.id, finished_watched.id
            )

            id_to_remove.add(not_finished_watched.id)

            finished_watched.append_datetime = not_finished_watched.append_datetime
            finished_watched.save()

for game_id in id_to_remove:
    Game.delete_by_id(game_id)
