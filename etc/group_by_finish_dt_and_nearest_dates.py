#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import itertools
from collections import defaultdict
from typing import List

from db import Game


def has_nearest_dates(games: List[Game], diff_secs=60) -> bool:
    dates = [game.finish_datetime_dt for game in games]
    return any(
        abs((dt1 - dt2).total_seconds()) <= diff_secs
        for dt1, dt2 in itertools.combinations(dates, 2)
    )


finish_by_games = defaultdict(list)
for game in Game.select().where(Game.ignored == 0):
    if not game.finish_datetime_dt:
        continue

    date = game.finish_datetime_dt.date()
    finish_by_games[date].append(game)

finish_by_games = {
    k: v
    for k, v in finish_by_games.items()
    if len(v) > 1 and has_nearest_dates(v)
}
print(len(finish_by_games))

for date, games in finish_by_games.items():
    print(f"{date} ({len(games)}):")
    for x in games:
        print(f"    {x}")
    print()
