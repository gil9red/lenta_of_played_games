#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from common import iter_parse_played_games
from db import Game
from third_party.mini_played_games_parser import parse_played_games


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

for game in Game.select():
    name = f'{game.platform}_{game.category}_{game.name}'
    if not game.ignored and name not in current_games:
        print(f'{game.name} ({game.platform}, {game.category})')

        # game.ignored = True
        # game.save()
