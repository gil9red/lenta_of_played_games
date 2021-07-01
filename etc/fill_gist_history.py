#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


import time

# pip install github3.py
from github3 import GitHub

from config import GITHUB_TOKEN
from common import log, utc_to_local, get_finally
from db import GistFile


gh = GitHub(token=GITHUB_TOKEN)


def main() -> bool:
    changed = False
    t = time.perf_counter()

    gist = gh.gist('2f80a34fb601cd685353')

    for commit in gist.commits():
        committed_at = utc_to_local(commit.committed_at)

        log.info(f'Process: {committed_at}, {commit.version}, {commit.url}')

        if GistFile.has(commit.version):
            log.info('Already exists. Finish!')
            break

        gist = get_finally(lambda: commit.gist())
        if 'gistfile1.txt' not in gist.files:
            continue

        content = get_finally(lambda: gist.files['gistfile1.txt'].content())

        log.info(f'Added {commit.version}')
        GistFile.create(
            commit_hash=commit.version,
            committed_at=committed_at,
            raw_url=commit.url,
            content=content,
        )
        changed = True

    log.info(f'Elapsed {int(time.perf_counter() - t)} secs')
    return changed


if __name__ == '__main__':
    main()
