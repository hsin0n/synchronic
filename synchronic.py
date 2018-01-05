#!/usr/local/bin/python3

import logging
from functools import partial
import yaml

from plexapi.server import PlexServer  # plexapi
import spice_api  # spice_api
from tabulate import tabulate as tabulate_raw  # tabulate


# Configuration for this script.
with open("config.yml", "rb") as cfg_file:
    cfg = yaml.load(cfg_file.read())
PLEX_URL = cfg["plex_url"]
PLEX_TOKEN = cfg["plex_token"]
PLEX_SECTION = cfg["plex_section"]
MAL_USERNAME = cfg["mal_username"]
MAL_PASSWORD = cfg["mal_password"]
LOGGING_LEVEL = logging.DEBUG
TABULATE_FMT = cfg["tabulate_fmt"]

# Set overrides for which item to use from the given MyAnimeList search, or
# use the first result by default.
# title[Str]: index[Int]
INDEX_OVERRIDES = {}


def tabulate(*args, **kwargs):
    """Helper to automatically set table format and print the generated table"""
    kwargs.setdefault("tablefmt", TABULATE_FMT)
    print(tabulate_raw(*args, **kwargs))


class SpiceWrapper(object):
    """
    Basic wrapper for Spice to prevent us from having to pass required
    arguments for every single call.
    """

    def __init__(self, username, password):
        self._creds = spice_api.init_auth(username, password)
        self._med = spice_api.get_medium("anime")
        self._overrides = dict(
            get_blank=dict(medium=self._med),
            get_status=dict(),
        )
        self.logger = logging.getLogger("SpiceWrapper")
        self.logger.setLevel(LOGGING_LEVEL)
        self._item_buffer = dict()

    def __getattr__(self, name):
        if name in self._overrides:
            kwargs = self._overrides[name]
        else:
            kwargs = dict(
                medium=self._med,
                credentials=self._creds,
            )
        return partial(spice_api.__dict__[name], **kwargs)

    def _determine_status(self, num_watched, num_total):
        if num_watched >= num_total:
            return self.get_status("completed")
        elif num_watched > 0:
            return self.get_status("watching")
        else:
            return self.get_status("plantowatch")

    def _add_item(
        self, item_id, num_watched, status, score=0, tags=None
    ):
        item = self.get_blank()
        item.episodes = num_watched
        item.status = status
        item.score = score
        item.tags = tags or ["synchronic", "auto-sync", "plex-sync"]
        self._item_buffer[int(item_id)] = item

    def _flush_items(self):
        self.logger.info("Flushing pending item changes to MyAnimeList.")
        headers = ["MAL ID", "MyAnimeList Title", "Status", "Episodes"]
        items = [
            [item_id, self.search_id(item_id).title, item.status, item.episodes]
            for item_id, item in self._item_buffer.items()
        ]
        tabulate(items, headers=headers)
        for item_id, item in self._item_buffer.items():
            self.update(item, item_id)
        self._item_buffer = dict()


logging.basicConfig(format="[%(name)-15s][%(levelname)-5s] %(message)s")
logger = logging.getLogger("synchronic.py")
logger.setLevel(LOGGING_LEVEL)

plex = PlexServer(PLEX_URL, PLEX_TOKEN)
spice = SpiceWrapper(MAL_USERNAME, MAL_PASSWORD)

logger.info("Loading Plex section: %s", PLEX_SECTION)
plex_items = plex.library.section(PLEX_SECTION).all()
total_items = len(plex_items)
entries = []
for item_idx, plex_item in enumerate(plex_items):
    num_watched = len(plex_item.watched())
    num_total = len(plex_item.episodes())

    try:
        mal_item = spice.search(plex_item.title)[
            INDEX_OVERRIDES.get(plex_item.title, 0)
        ]
    except Exception:
        # Unable to resolve this to a MAL anime item, skip.
        mal_item = None
    else:
        spice._add_item(
            item_id=mal_item.id,
            num_watched=num_watched,
            status=spice._determine_status(num_watched, num_total),
        )

    entries.append([
        plex_item.title,
        mal_item.title if mal_item else "N/A",
        num_watched,
        num_total,
    ])

headers = ["Plex Title", "MyAnimeList Title", "# Watched", "# Total"]
tabulate(entries, headers=headers)
spice._flush_items()
