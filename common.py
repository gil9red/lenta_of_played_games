#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


import datetime as DT
import logging
import sys
import time

from pathlib import Path
from typing import Iterator, Tuple, Optional, Callable, Any

import requests

from config import DIR_LOG


def iter_parse_played_games(platforms: dict) -> Iterator[Tuple[str, str, str]]:
    for platform, categories in platforms.items():
        for category, games in categories.items():
            for name in games:
                yield platform, category, name


def utc_to_local(utc_dt: DT.datetime) -> Optional[DT.datetime]:
    if utc_dt:
        return utc_dt.replace(tzinfo=DT.timezone.utc).astimezone(tz=None)


def get_finally(f: Callable) -> Any:
    while True:
        try:
            return f()
        except:
            time.sleep(1)


def get_logger(file_name: str, dir_name='logs'):
    dir_name = Path(dir_name).resolve()
    dir_name.mkdir(parents=True, exist_ok=True)

    file_name = str(dir_name / Path(file_name).resolve().name) + '.log'

    log = logging.getLogger(__name__)
    log.setLevel(logging.DEBUG)

    formatter = logging.Formatter('[%(asctime)s] %(filename)s[LINE:%(lineno)d] %(levelname)-8s %(message)s')

    fh = logging.FileHandler(file_name, encoding='utf-8')
    fh.setLevel(logging.DEBUG)

    ch = logging.StreamHandler(stream=sys.stdout)
    ch.setLevel(logging.DEBUG)

    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    log.addHandler(fh)
    log.addHandler(ch)

    return log


log = get_logger('log', DIR_LOG)


# SOURCE: https://github.com/gil9red/SimplePyScripts/blob/a0f9ea209daac9819264d72b773f6f69a28f56b0/Check%20with%20notification/all_common.py#L57
def send_sms(api_id: str, to: str, text: str, log):
    api_id = api_id.strip()
    to = to.strip()

    if not api_id or not to:
        log.warning('Параметры api_id или to не указаны, отправка СМС невозможна!')
        return

    log.info(f'Отправка sms: {text!r}')

    if len(text) > 70:
        text = text[:70-3] + '...'
        log.info(f'Текст sms будет сокращено, т.к. слишком длинное (больше 70 символов): {text!r}')

    # Отправляю смс на номер
    url = 'https://sms.ru/sms/send?api_id={api_id}&to={to}&text={text}'.format(
        api_id=api_id,
        to=to,
        text=text
    )
    log.debug(repr(url))

    while True:
        try:
            rs = requests.get(url)
            log.debug(repr(rs.text))
            break

        except:
            log.exception("При отправке sms произошла ошибка:")
            log.debug('Через 5 минут попробую снова...')

            # Wait 5 minutes before next attempt
            time.sleep(5 * 60)
