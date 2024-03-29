#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import datetime as DT
import logging
import sys
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Iterator, Tuple, Optional, Callable, Any

from config import DIR_LOGS


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


def get_logger(name: str, dir_name="logs"):
    dir_name = Path(dir_name).resolve()
    dir_name.mkdir(parents=True, exist_ok=True)

    file_name = str(dir_name / Path(name).resolve().name) + ".log"

    log = logging.getLogger(name)
    log.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "[%(asctime)s] %(filename)s[LINE:%(lineno)d] %(levelname)-8s %(message)s"
    )

    fh = RotatingFileHandler(
        file_name, maxBytes=10_000_000, backupCount=5, encoding="utf-8"
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    log.addHandler(fh)

    ch = logging.StreamHandler(stream=sys.stdout)
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    log.addHandler(ch)

    return log


log = get_logger("log", DIR_LOGS)
