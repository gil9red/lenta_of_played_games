#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


from etc import fill_games, fill_gist_history, update_of_ignored

from common import log
from db import db_create_backup
from third_party.wait import wait


while True:
    try:
        log.info('Started!')

        changed_1 = fill_gist_history.main()
        changed_2 = fill_games.main()
        if changed_1 or changed_2:
            db_create_backup(log)

        update_of_ignored.main()

    except Exception:
        log.exception('Error:')
        wait(minutes=15)
        continue

    log.info('Finished!')
    wait(hours=1)
