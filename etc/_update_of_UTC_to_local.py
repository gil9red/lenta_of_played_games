#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


import datetime as DT

from common import utc_to_local
from db import Game, GistFile


# 2021-01-06 14:20:35+00:00 -> 0
# 2021-01-08 05:23:31+05:00 -> 18000
def get_tz_secs(dt: DT.datetime) -> int:
    return int(dt.utcoffset().total_seconds())


for gist_file in GistFile.select():
    if get_tz_secs(gist_file.committed_at_dt) > 0:
        continue

    gist_file.committed_at = utc_to_local(gist_file.committed_at_dt)
    gist_file.save()


for game in Game.select():
    append_datetime_dt = game.append_datetime_dt
    finish_datetime_dt = game.finish_datetime_dt
    changed = False

    if append_datetime_dt and get_tz_secs(append_datetime_dt) == 0:
        game.append_datetime = utc_to_local(append_datetime_dt)
        changed = True

    if finish_datetime_dt and get_tz_secs(finish_datetime_dt) == 0:
        game.finish_datetime = utc_to_local(finish_datetime_dt)
        changed = True

    if changed:
        game.save()
