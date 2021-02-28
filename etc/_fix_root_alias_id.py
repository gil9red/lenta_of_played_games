#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


import re
from db import Game


# Некоторым играм менял номер с арабских на римские, типа: "Final Fantasy 5" -> "Final Fantasy V"
ARAB_TO_ROMAN = {
    '1': 'I', '2': 'II', '3': 'III', '4': 'IV', '5': 'V', '6': 'VI',
    '7': 'VII', '8': 'VIII', '9': 'IX', '10': 'X', '11': 'XI', '12': 'XII',
    '13': 'XIII', '14': 'XIV', '15': 'XV',
}


# В какой-то момент поменял платформу с PS на PS1, нужно играм с PS1 указать
# на те же игры с PS
for game in Game.select().where(Game.platform == 'PS1'):
    if game.root_alias:
        continue

    root_game = Game.get_or_none(
        Game.platform == 'PS',
        Game.name == game.name,
        Game.category == game.category
    )
    if not root_game or root_game.id > game.id:
        continue

    game.root_alias = root_game
    game.save()

# У некоторых игр арабские цифры в названии были заменены на римские
for root_game in Game.select():
    m = re.search(r'\d+', root_game.name)
    if not m:
        continue

    number = m.group()
    if number not in ARAB_TO_ROMAN:
        continue

    roman = ARAB_TO_ROMAN[number]
    new_game_name = re.sub(r'\d+', roman, root_game.name)

    for game in Game.select().where(
            Game.name == new_game_name,
            Game.platform == root_game.platform,
            Game.category == root_game.category
    ):
        # Если уже задан root_alias или у родительской игры id меньше текущей
        if game.root_alias or root_game.id > game.id:
            continue

        game.root_alias = root_game
        game.save()
