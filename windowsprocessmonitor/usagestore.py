import os
import shelve
from datetime import date, datetime, timedelta


class UsageStore:

    def __init__(self, filename):
        self.filename = filename
        self.last_update = None

    def usage_for_day_in_seconds(self, day: date) -> int:
        y, m, d = str(day.year), str(day.month), str(day.day)
        try:
            with shelve.open(self.filename) as db:
                return sum([last_seen - started for started, last_seen in
                            db[y][m][d].items()]) / 3600
        except KeyError:
            return 0

    def usage_for_month_in_seconds(self, day: date) -> int:
        y, m = str(day.year), str(day.month)
        try:
            with shelve.open(self.filename) as db:
                return sum([sum([last_seen - started for started, last_seen in times.items()])
                            for d, times in db[y][m].items()]) / 3600
        except KeyError:
            return 0

    def _update_day(self, day: date, started: float, finished: float):
        y, m, d = str(day.year), str(day.month), str(day.day)
        with shelve.open(self.filename, writeback=True) as db:

            if y not in db:
                db[y] = {}

            if m not in db[y]:
                db[y][m] = {}

            if d not in db[y][m]:
                db[y][m][d] = {}

            db[y][m][d][started] = finished
            db.sync()

    def update(self, started: float, current: float):
        started_dt = datetime.fromtimestamp(started)
        current_dt = datetime.fromtimestamp(current)
        days_diff = current_dt.date() - started_dt.date()

        if days_diff.days > 0:
            start_day_beginning_dt = datetime(started_dt.year, started_dt.month, started_dt.day)
            for td in map(lambda d: timedelta(days=d), range(days_diff.days)):
                self._update_day(
                    start_day_beginning_dt.date() + td,
                    (start_day_beginning_dt + td).timestamp(),
                    (start_day_beginning_dt + td + timedelta(days=1)).timestamp()
                )
            self._update_day(
                start_day_beginning_dt.date() + timedelta(days=days_diff.days),
                (start_day_beginning_dt + timedelta(days=days_diff.days)).timestamp(),
                current
            )
        else:
            self._update_day(
                started_dt.date(),
                started,
                current
            )

        self.last_update = datetime.now()
