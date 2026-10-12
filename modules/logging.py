
import datetime
import sys


class Logger:
    @staticmethod
    def info(*args):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[info at: {now}]:", *args)

    @staticmethod
    def warn(*args):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[warn at: {now}]:", *args, file=sys.stderr)

    @staticmethod
    def error(*args):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[error at: {now}]:", *args, file=sys.stderr)
