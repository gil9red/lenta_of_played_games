#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from config import DIR_LOG, SMS_API_ID, SMS_TO
from common import iter_parse_played_games, get_logger, send_sms
from db import Game
from third_party.mini_played_games_parser import parse_played_games


log = get_logger('update_of_ignored', DIR_LOG)


def get_games() -> dict:
    rs = requests.get('https://gist.github.com/gil9red/2f80a34fb601cd685353')

    root = BeautifulSoup(rs.content, 'html.parser')
    href = root.select_one('.file-actions > a')['href']

    raw_url = urljoin(rs.url, href)
    rs = requests.get(raw_url)

    return parse_played_games(rs.text, silence=True)


current_games = [
    f'{platform}_{category}_{name}'
    for platform, category, name in iter_parse_played_games(get_games())
]

changed_count = 0
for game in Game.select():
    name = f'{game.platform}_{game.category}_{game.name}'

    last_ignored = game.ignored
    game.ignored = name not in current_games

    if last_ignored != game.ignored:
        log.info(f'#{game.id} {game.name} ({game.platform}, {game.category}): {last_ignored} -> {game.ignored}')
        game.save()

        changed_count += 1

if changed_count:
    text = f'Изменений: {changed_count}'
    log.debug(text)
    send_sms(SMS_API_ID, SMS_TO, '[Lenta of played games] ' + text, log)
