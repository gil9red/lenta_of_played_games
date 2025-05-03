#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import re
from db import Game


# Некоторым играм менял номер с арабских на римские, типа: "Final Fantasy 5" -> "Final Fantasy V"
ARAB_TO_ROMAN = {
    "1": "I",
    "2": "II",
    "3": "III",
    "4": "IV",
    "5": "V",
    "6": "VI",
    "7": "VII",
    "8": "VIII",
    "9": "IX",
    "10": "X",
    "11": "XI",
    "12": "XII",
    "13": "XIII",
    "14": "XIV",
    "15": "XV",
}


# В какой-то момент поменял платформу с PS на PS1, нужно играм с PS1 указать
# на те же игры с PS
# В другой момент писал 'PS 2', после поменял название категории на PS2
old_by_new_platforms = {
    "PS": "PS1",
    "PS 2": "PS2",
    "PS 3": "PS3",
    "PS 4": "PS4",
    "NES/Famicom": "Dendy/NES/Famicom",
    "Dendy/NES/Famicom": "NES",
}
for old_platform, new_platform in old_by_new_platforms.items():
    # Ищем игры с указанной платформой и без заданного root_alias
    for game in Game.select().where(
        Game.platform == new_platform, Game.root_alias.is_null()
    ):
        root_game = Game.get_or_none(
            Game.platform == old_platform,
            Game.name == game.name,
            Game.category == game.category,
        )
        # Если не найдено или если у найденной id больше, чем у требуемой игры
        if not root_game or root_game.id > game.id:
            continue

        print(f"In game #{game.id} setted root_alias from #{root_game.id}")
        game.root_alias = root_game
        game.save()

# У некоторых игр арабские цифры в названии были заменены на римские
for root_game in Game.select():
    m = re.search(r"\d+", root_game.name)
    if not m:
        continue

    number = m.group()
    if number not in ARAB_TO_ROMAN:
        continue

    roman = ARAB_TO_ROMAN[number]
    new_game_name = re.sub(r"\d+", roman, root_game.name)

    for game in Game.select().where(
        Game.name == new_game_name,
        Game.platform == root_game.platform,
        Game.category == root_game.category,
    ):
        # Если уже задан root_alias или у родительской игры id меньше текущей
        if game.root_alias or root_game.id > game.id:
            continue

        print(f"In game #{game.id} setted root_alias from #{root_game.id}")
        game.root_alias = root_game
        game.save()

# Игры с DLC без заданного root_alias_id
# Пример было "XXX", а стало "XXX (DLC)" но в root_alias_id не установлено значение из XXX
postfix_dlc = " (DLC)"
for game in Game.select().where(
    Game.name.endswith(postfix_dlc),
    Game.root_alias_id.is_null(),
):
    prev_game: Game | None = Game.get_or_none(
        Game.name == game.name.removesuffix(postfix_dlc),
        Game.platform == game.platform,
        Game.category == game.category,
        Game.ignored == True,
    )
    if not prev_game:
        continue

    print(f"In game #{game.id} setted root_alias from #{prev_game.id}")
    game.root_alias = prev_game
    game.save()
