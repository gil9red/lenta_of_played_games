#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


import datetime as DT
import logging
import shutil

from typing import Any, Callable, Union, Optional, Iterator
from pathlib import Path

# pip install peewee
from peewee import *

from config import DIR
from third_party.shorten import shorten


DB_FILE_NAME = DIR / 'database.sqlite'
BACKUP_DIR_NAME = DIR / 'backup'


def db_create_backup(log: logging.Logger, backup_dir=BACKUP_DIR_NAME):
    backup_path = Path(backup_dir)
    backup_path.mkdir(parents=True, exist_ok=True)

    file_name = str(DT.datetime.today().date()) + '.sqlite'
    file_name = backup_path / file_name

    log.debug(f'Doing create backup in: {file_name}')
    shutil.copy(DB_FILE_NAME, file_name)


# Ensure foreign-key constraints are enforced.
db = SqliteDatabase(DB_FILE_NAME, pragmas={'foreign_keys': 1})


class BaseModel(Model):
    class Meta:
        database = db

    def __str__(self):
        fields = []
        for k, field in self._meta.fields.items():
            v = getattr(self, k)

            if isinstance(field, TextField):
                if v:
                    v = repr(shorten(v))

            elif isinstance(field, ForeignKeyField):
                k = f'{k}_id'
                if v:
                    v = v.id

            fields.append(f'{k}={v}')

        return self.__class__.__name__ + '(' + ', '.join(fields) + ')'


class GistFile(BaseModel):
    commit_hash = TextField(unique=True)
    committed_at = DateTimeField()
    raw_url = TextField()
    content = TextField()

    @property
    def committed_at_dt(self) -> DT.datetime:
        if isinstance(self.committed_at, str):
            return DT.datetime.fromisoformat(self.committed_at)

        return self.committed_at

    @classmethod
    def has(cls, commit_hash: str) -> bool:
        return cls.get_or_none(commit_hash=commit_hash)


class Game(BaseModel):
    name = TextField()
    platform = TextField()
    category = TextField()
    append_datetime = DateTimeField()
    finish_datetime = DateTimeField(null=True)
    ignored = BooleanField(default=False)

    class Meta:
        indexes = (
            (("name", "platform", "category"), True),
        )

    @property
    def append_datetime_dt(self) -> DT.datetime:
        if isinstance(self.append_datetime, str):
            return DT.datetime.fromisoformat(self.append_datetime)

        return self.append_datetime

    @property
    def finish_datetime_dt(self) -> DT.datetime:
        if isinstance(self.finish_datetime, str):
            return DT.datetime.fromisoformat(self.finish_datetime)

        return self.finish_datetime

    @classmethod
    def get_all_finished_by_year(cls, year: int) -> Iterator['Game']:
        fn_year = fn.strftime('%Y', cls.finish_datetime).cast('INTEGER')
        return (
            cls
            .select()
            .where(fn_year == year, cls.finish_datetime.is_null(False), cls.ignored == 0)
            .order_by(cls.finish_datetime.desc())
        )


class Settings(BaseModel):
    key = TextField(unique=True)
    value = TextField()

    @classmethod
    def set_value(cls, key: str, value: str):
        obj = cls.get_or_none(key=key)
        if obj:
            if cls.get_value(key) != value:
                obj.value = value
                obj.save()
        else:
            cls.create(
                key=key,
                value=value,
            )

    @classmethod
    def get_value(cls, key: str, get_typing_value_func: Callable = None) -> Optional[Union[str, Any]]:
        obj = cls.get_or_none(key=key)
        value = obj and obj.value

        if get_typing_value_func:
            value = get_typing_value_func(value)

        return value

    @classmethod
    def remove_value(cls, key: str):
        obj = cls.get_or_none(key=key)
        if obj:
            obj.delete_instance()


db.connect()
db.create_tables([GistFile, Game, Settings])


if __name__ == '__main__':
    fn_year = fn.strftime('%Y', Game.finish_datetime).cast('INTEGER')

    # for game in (
    #         Game
    #         .select(
    #             fn_year.alias('year'),
    #         ).distinct()
    #         .where(Game.finish_datetime.is_null(False), Game.ignored == 0)
    #         .order_by(fn_year.desc())
    # ):
    #     print(game.year)
    #
    # print()

    # TODO: move to class Game
    for game in (
            Game
            .select(
                fn_year.alias('year'),
                fn.count(Game.id).alias('count')
            )
            .where(Game.finish_datetime.is_null(False), Game.ignored == 0)
            .group_by(fn_year)
            .order_by(fn_year.desc())
    ):
        print(game.year, game.count)

    print()

    from collections import defaultdict
    day_by_games = defaultdict(list)

    for game in Game.get_all_finished_by_year(2021):
        # print(game.name, game.platform)

        day = game.finish_datetime_dt.strftime('%d/%m')
        day_by_games[day].append(game)

    print(day_by_games)

    for day, games in day_by_games.items():
        print(day, len(games))
        for game in games:
            print('   ', game.name, game.platform)

    quit()

    for game in Game.select()\
            .where(Game.finish_datetime.is_null(False), Game.ignored == 0)\
            .order_by(Game.finish_datetime.desc(), Game.name.asc()):
        print(game)
    quit()

    for gist_file in GistFile.select().order_by(GistFile.committed_at.asc()).limit(5):
        print(gist_file)

    print()

    for game in Game.select().limit(5):
        print(game)

    print()

    for game in Game.select().order_by(Game.id.desc()).limit(5):
        print(game)

    # TODO: Осторожнее, если в данный момент будет запись в базу, произойдет ошибка, т.к.
    #       база будет залочена
    # import uuid
    # key = uuid.uuid4().hex
    # value = uuid.uuid4().hex
    #
    # assert Settings.get_value(key) is None
    #
    # Settings.set_value(key, value)
    # assert Settings.get_value(key) == value
    #
    # Settings.remove_value(key)
    # assert Settings.get_value(key) is None
