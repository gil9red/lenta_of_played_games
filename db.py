#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import datetime as DT
import logging
import shutil

from collections import defaultdict
from typing import Any, Callable, Union, Optional
from pathlib import Path

# pip install peewee
from peewee import (
    SqliteDatabase,
    Model,
    fn,
    Query,
    TextField,
    ForeignKeyField,
    DateTimeField,
    BooleanField,
)

from config import DIR
from third_party.shorten import shorten


DB_FILE_NAME = DIR / "database.sqlite"
BACKUP_DIR_NAME = DIR / "backup"


def db_create_backup(log: logging.Logger, backup_dir=BACKUP_DIR_NAME):
    backup_path = Path(backup_dir)
    backup_path.mkdir(parents=True, exist_ok=True)

    file_name = str(DT.datetime.today().date()) + ".sqlite"
    file_name = backup_path / file_name

    log.debug(f"Doing create backup in: {file_name}")
    shutil.copy(DB_FILE_NAME, file_name)


# Ensure foreign-key constraints are enforced.
db = SqliteDatabase(DB_FILE_NAME, pragmas={"foreign_keys": 1})


class BaseModel(Model):
    class Meta:
        database = db

    @classmethod
    def get_last(cls) -> "Self":
        return cls.select().order_by(cls.id.desc()).first()

    def __str__(self):
        fields = []
        for k, field in self._meta.fields.items():
            v = getattr(self, k)

            if isinstance(field, TextField):
                if v:
                    v = repr(shorten(v))

            elif isinstance(field, ForeignKeyField):
                k = f"{k}_id"
                if v:
                    v = v.id

            fields.append(f"{k}={v}")

        return self.__class__.__name__ + "(" + ", ".join(fields) + ")"


class GistFile(BaseModel):
    commit_hash = TextField(unique=True)
    committed_at = DateTimeField()
    raw_url = TextField()
    content = TextField()

    @classmethod
    def get_last(cls) -> "GistFile":
        # NOTE: Какая-то проблема с гистами, что приводит к тому, что когда было сделано 2 коммита,
        # последним коммитом оказался предпоследний
        return cls.select().order_by(cls.committed_at.desc()).first()

    @property
    def committed_at_dt(self) -> Union[DT.datetime, DateTimeField]:
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
    root_alias = ForeignKeyField("self", null=True)

    class Meta:
        indexes = (
            (("name", "platform", "category"), True),
        )

    @classmethod
    def get_all_by(cls, **filters) -> list["Game"]:
        return list(cls.select().filter(**filters).order_by(cls.id))

    def get_first_root(self) -> "Game":
        root_alias: Game = self.root_alias
        owns: list[Game] = [root_alias]

        # Идем вверх пока не найдем самую первую игру
        while root_alias:
            # Если у текущей игры нет псевдонима
            if not root_alias.root_alias:
                break

            root_alias: Game = root_alias.root_alias
            if root_alias in owns:
                raise Exception(f"Обнаружено зацикливание {root_alias} в {owns}")

            owns.append(root_alias)

        return root_alias

    @property
    def append_datetime_dt(self) -> Union[DT.datetime, DateTimeField]:
        append_datetime = self.append_datetime

        root_alias = self.get_first_root()
        if root_alias and root_alias.append_datetime is not None:
            append_datetime = root_alias.append_datetime

        if isinstance(append_datetime, str):
            return DT.datetime.fromisoformat(append_datetime)

        return append_datetime

    @property
    def finish_datetime_dt(self) -> Union[DT.datetime, DateTimeField]:
        finish_datetime = self.finish_datetime

        root_alias = self.get_first_root()
        if root_alias and root_alias.finish_datetime is not None:
            finish_datetime = root_alias.finish_datetime

        if isinstance(finish_datetime, str):
            return DT.datetime.fromisoformat(finish_datetime)

        return finish_datetime

    @classmethod
    def get_query_for_current_finished(cls) -> Query:
        return cls.select().where(cls.finish_datetime.is_null(False), cls.ignored == 0)

    @classmethod
    def get_all_finished(cls, sort: bool = True) -> list["Game"]:
        query = cls.get_query_for_current_finished()
        items = list(query)
        if sort:
            items.sort(key=lambda item: item.finish_datetime_dt, reverse=True)
        return items

    @classmethod
    def get_all_finished_by_year(cls, year: int) -> list["Game"]:
        query = cls.get_query_for_current_finished()
        # Проще отсортировать тут, чем в базе из-за особенностей finish_datetime_dt
        items = [game for game in query if game.finish_datetime_dt.year == year]
        items.sort(key=lambda item: item.finish_datetime_dt, reverse=True)
        return items

    @classmethod
    def get_year_by_number(cls) -> list[tuple[int, int]]:
        fn_year = fn.strftime("%Y", cls.finish_datetime).cast("INTEGER")

        year_by_number = []
        for game in (
                cls
                .select(
                    fn_year.alias("year"),
                    fn.count(cls.id).alias("count")
                )
                .where(cls.finish_datetime.is_null(False), cls.ignored == 0)
                .group_by(fn_year)
                .order_by(fn_year.desc())
        ):
            year_by_number.append((
                game.year, game.count
            ))

        return year_by_number

    @classmethod
    def get_day_by_games(cls, year: int) -> dict[str, list["Game"]]:
        day_by_games = defaultdict(list)

        for game in Game.get_all_finished_by_year(year):
            day = game.finish_datetime_dt.strftime("%d/%m/%Y")
            day_by_games[day].append(game)

        return day_by_games

    @classmethod
    def get_platforms(cls) -> list[str]:
        return sorted(set(game.platform for game in cls.get_query_for_current_finished()))


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


if __name__ == "__main__":
    for year, number in Game.get_year_by_number():
        print(year, number)

    print()

    day_by_games = Game.get_day_by_games(2021)
    for day, games in list(day_by_games.items())[:3]:
        print(f"{day} ({len(games)}):")
        for game in games:
            print(f"    {game.name} ({game.platform})")

    print()

    # for game in Game.select()\
    #         .where(Game.finish_datetime.is_null(False), Game.ignored == 0)\
    #         .order_by(Game.finish_datetime.desc(), Game.name.asc()):
    #     print(game)

    for gist_file in GistFile.select().order_by(GistFile.committed_at.asc()).limit(5):
        print(gist_file)

    print()

    for game in Game.select().limit(5):
        print(game)

    print()

    for game in Game.select().order_by(Game.id.desc()).limit(5):
        print(game)

    # NOTE: Осторожнее, если в данный момент будет запись в базу, произойдет ошибка, т.к.
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

    print()

    game = Game.get_by_id(606)
    print(game.finish_datetime_dt, game.root_alias.finish_datetime_dt)

    # Тут будет такая цепочка:
    #  * "1468) 'Final Fantasy IX' | PS1 | 2020-06-28 03:53:26+05:00", root_alias=610
    #  * "610)  'Final Fantasy IX' | PS  | 2016-12-30 07:19:39+05:00", root_alias=15
    #  * "15)   'Final Fantasy 9'  | PS  | 2015-06-22 22:40:22+05:00", root_alias=null
    print(Game.get_by_id(1468).finish_datetime_dt)
    print()

    platforms = Game.get_platforms()
    print(f"All platforms ({len(platforms)}): {platforms}")
