import logging
from abc import ABC, abstractmethod
from threading import Thread
from time import sleep
from typing import Iterable, List

import psutil
import win32api
import win32con
import win32gui


class MultipleProcessesFound(Exception):
    """"""


class AMonitor(ABC):

    def __init__(
            self,
            handling_period_s: int = 5,
            reposition_period_s: int = 5,
            prompt_window_title: str = None,
            logger: logging.Logger = logging.getLogger(__name__)):
        self.handling_period_s = handling_period_s
        self.reposition_period_s = reposition_period_s
        self.prompt_window_title = prompt_window_title or self.__class__.__qualname__
        self.should_terminate = False
        self.logger = logger

    def handle(self, processes: Iterable[psutil.Process]):
        """Should return one of the"""
        found = list(filter(self.is_sought_process, processes))
        if not found:
            self.logger.info("Process not found")
            self.on_process_not_found()
        elif len(found) == 1:
            self.logger.info("Single process found: %s", repr(found[0]))
            self.on_single_process_found(found[0])
        else:
            self.on_multiple_processes_found(found)

    @abstractmethod
    def is_sought_process(self, process: psutil.Process):
        """Process search condition."""

    def on_process_not_found(self):
        """Called when process is not found."""
        pressed = win32gui.MessageBox(
            None,
            self.not_found_prompt_text(),
            self.prompt_window_title,
            win32con.MB_YESNOCANCEL | win32con.MB_ICONEXCLAMATION)

        {
            win32con.IDYES: self.on_prompt_yes,
            win32con.IDNO: self.on_prompt_no,
            win32con.IDCANCEL: self.on_prompt_cancel,
        }.get(pressed)()

    @abstractmethod
    def on_single_process_found(self, process: psutil.Process):
        """Called when one process is found."""

    def on_multiple_processes_found(self, processes: List[psutil.Process]):
        """Called when process is not found."""
        raise MultipleProcessesFound(f"Found {len(processes)} processes: {str(processes)}")

    @abstractmethod
    def not_found_prompt_text(self) -> str:
        """Produces prompt text."""

    @abstractmethod
    def on_prompt_yes(self):
        """Run when yes is pressed."""

    @abstractmethod
    def on_prompt_no(self):
        """Run when no is pressed."""

    @abstractmethod
    def on_prompt_cancel(self):
        """Run when cancel is pressed."""

    def stop(self):
        self.logger.warning(f"Shutting down in {max(self.handling_period_s, self.reposition_period_s)} seconds.")
        self.should_terminate = True

    def main(self):

        def handling_thread_target():
            while not self.should_terminate:
                try:
                    self.handle(psutil.process_iter())
                    sleep(self.handling_period_s)
                except Exception as e:
                    self.logger.exception("Unhandled error", exc_info=e)
                    self.should_terminate = True

        def repositioning_thread_target():
            while not self.should_terminate:
                hwnd = win32gui.FindWindow(None, self.prompt_window_title)
                if hwnd:
                    l, t, r, b = win32gui.GetWindowRect(hwnd)
                    centre_x, centre_y = win32api.GetSystemMetrics(0) // 2, win32api.GetSystemMetrics(1) // 2
                    x, y = centre_x - ((r - l) // 2), centre_y - ((b - t) // 2)
                    if (l, t) != (x, y):
                        self.logger.debug(f"Repositioning prompt at ({x}, {y})")
                        win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, x, y, 0, 0, win32con.SWP_NOSIZE)
                sleep(self.reposition_period_s)

        Thread(target=handling_thread_target).start()
        Thread(target=repositioning_thread_target).start()
