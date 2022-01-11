import logging
import os
import time
from configparser import ConfigParser
from datetime import date
from datetime import timedelta, datetime
from logging.config import fileConfig

import psutil
import win32api

import dbm.dumb  # important, keep it


from windowsprocessmonitor.abstract import AMonitor
from windowsprocessmonitor.usagestore import UsageStore


class VDIMonitor(AMonitor):

    def __init__(self, usage_store: UsageStore, handling_period_s: int = 5, reposition_period_s: int = 5,
                 prompt_window_title: str = None,
                 logger: logging.Logger = logging.getLogger(__name__)):
        super().__init__(handling_period_s, reposition_period_s, prompt_window_title, logger)
        self.usage_store = usage_store

    def maybe_create_storage_dir(self):
        storage_root = os.path.dirname(self.usage_store.filename)
        try:
            os.stat(storage_root)
        except FileNotFoundError:
            self.logger.warning(f"Storage directory doesn't exist creating: {storage_root}")
            os.makedirs(os.path.dirname(self.usage_store.filename), exist_ok=True)

    def is_sought_process(self, process: psutil.Process):
        return process.name() == 'wfica32.exe'

    def _usage_info(self):
        usage_today = self.usage_store.usage_for_day_in_seconds(date.today())
        usage_month = self.usage_store.usage_for_month_in_seconds(date.today())
        return (
            f"Your VDI usage today is {round(usage_today, 2)} hours"
            f"\nYour VDI usage this month is {round(usage_month, 2)} hours"
        )

    def on_single_process_found(self, process: psutil.Process):
        """Update usage information."""
        if self.usage_store.last_update and self.usage_store.last_update + timedelta(minutes=1) > datetime.now():
            self.logger.info(f'Last update done within last minute ({self.usage_store.last_update}). Not updating.')
            return
        self.usage_store.update(process.create_time(), time.time())
        self.logger.info("After update:\n" + self._usage_info())

    def not_found_prompt_text(self) -> str:
        return (
                f"Open VDI?"
                f"\n 'Yes' - will open the VDI web page in the browser."
                f"\n 'No' - will make the prompt appear again in {self.handling_period_s} seconds."
                f"\n 'Cancel' - will terminate the monitor."""
                "\n\n"
                + self._usage_info()
        )

    def on_prompt_yes(self):
        """Run when yes is pressed."""
        win32api.ShellExecute(0, "open", "https://virtualityna.pg.com/Citrix/pgstoreWeb/", None, "", 1)

    def on_prompt_no(self):
        """Run when no is pressed."""
        self.logger.warning(f"Ignoring for {self.handling_period_s} seconds.")

    def on_prompt_cancel(self):
        """Run when cancel is pressed."""
        self.stop()


def config_logger(config_file: str):
    try:
        fileConfig(config_file)
    except Exception as e:
        logging.basicConfig(level=logging.DEBUG,
                            format="%(asctime)s %(levelname)s %(threadName)s %(name)s %(message)s")
        logging.warning(f"Logging configuration not loaded. Config path was: {config_file}", exc_info=e)


def run_with_defaults():
    config_logger('logging.ini')
    store = UsageStore("usage_data/usage.shelve")
    monitor = VDIMonitor(usage_store=store,
                         handling_period_s=1,
                         reposition_period_s=1,
                         logger=logging.getLogger(__name__))
    monitor.maybe_create_storage_dir()
    monitor.main()


def run_from_config(config_path: str):
    parser = ConfigParser()
    parser.read(config_path)

    monitor_config = parser['vdimonitor']

    kwargs = {
        'handling_period_s': monitor_config.getint('handling_period_s', None),
        'reposition_period_s': monitor_config.getint('reposition_period_s', None),
        'prompt_window_title': monitor_config.get('prompt_window_title') or None
    }

    logging_config_file = parser['logging'].get('config_file', None) or None
    config_logger(logging_config_file)

    store = UsageStore(parser['usage'].get('store_file', ' usage.shelve'))
    monitor = VDIMonitor(usage_store=store, **kwargs, logger=logging.getLogger(__name__))
    monitor.maybe_create_storage_dir()
    monitor.main()


if __name__ == '__main__':
    run_from_config(r'.\vdimonitor.ini')
