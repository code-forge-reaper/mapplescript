import time
import datetime

class Time:
    @staticmethod
    def now(res="ns"):
        t = time.time_ns()

        if res == "ns":
            return t
        elif res == "ms":
            return t / 1_000_000
        elif res == "sec":
            return t / 1_000_000_000
        else:
            raise ValueError(f"unknown {res=}")

    @staticmethod
    def str():
        return str(datetime.datetime.now())

    @staticmethod
    def sleep(secs):
        return time.sleep(secs)

    @staticmethod
    def monotonic(resolution="ns"):
        if resolution == "ns":
            return time.perf_counter_ns()  # High-resolution time in nanoseconds
        elif resolution == "ms":
            return time.perf_counter_ns() / 1_000_000
        elif resolution == "sec":
            return time.perf_counter_ns() / 1_000_000_000
        else:
            raise ValueError(f"unknown {resolution = }")
