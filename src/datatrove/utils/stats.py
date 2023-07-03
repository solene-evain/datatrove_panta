import math
import time
from collections import Counter
from dataclasses import dataclass


@dataclass
class TimeStats:
    mean: float
    variance: float
    standard_deviation: float
    total_time: float
    count: int
    max: float
    min: float


@dataclass
class Stats:
    name: str
    time: TimeStats
    counter: Counter


class OnlineStats:
    def __init__(self):
        self.counter = Counter()
        self._running_mean, self._running_variance = 0, 0
        self.max_value, self.min_value = 0.0, float("inf")

    def update(self, x: float):
        self.counter["total"] += x
        self.counter["n"] += 1

        self.min_value = min(self.min_value, x)
        self.max_value = max(self.max_value, x)
        previous_running_mean = self._running_mean
        self._running_mean = previous_running_mean + (x - previous_running_mean) / self.counter["n"]
        if self.counter["n"] == 1:
            self._running_variance = 0
        else:
            self._running_variance = self._running_variance + (x - previous_running_mean) * (
                x - self._running_mean
            ) / (self.counter["n"] - 1)

    def get_stats(self) -> TimeStats:
        return TimeStats(
            mean=self._running_mean,
            variance=self._running_variance,
            standard_deviation=math.sqrt(self._running_variance),
            total_time=self.counter["total"],
            count=self.counter["n"],
            max=self.max_value,
            min=self.min_value,
        )


class TimeStatsManager(OnlineStats):
    def __init__(self):
        super().__init__()

    def __enter__(self):
        self._entry_time = time.perf_counter()

    def __exit__(self, exc_type, exc_val, exc_tb):
        assert self._entry_time is not None
        self.update(time.perf_counter() - self._entry_time)


def merge_time_stats_couple(stat_1: TimeStats, stat_2: TimeStats) -> TimeStats:
    n = stat_1.count + stat_2.count
    merge_mean = (stat_1.count * stat_1.count + stat_2.count * stat_2.mean) / n
    delta = stat_1.mean - stat_2.mean
    merge_variance = stat_1.variance + stat_2.variance + stat_1.count * stat_2.count * delta**2 / n
    return TimeStats(
        mean=merge_mean,
        variance=merge_variance,
        standard_deviation=math.sqrt(merge_variance),
        total_time=stat_1.total_time + stat_2.total_time,
        count=n,
        max=max([stat_1.max, stat_2.max]),
        min=min([stat_1.min, stat_2.min]),
    )


def merge_time_stats(stats: list[TimeStats]) -> TimeStats:
    stats_0 = stats[0]
    for stat in stats[1:]:
        stats_0 = merge_time_stats_couple(stats_0, stat)
    return stats_0


def merge_all(stats: list[list[Stats]], save: bool = True) -> list[(str, dict)]:
    # first list -> workers, second list -> blocks within pipeline
    final_stats = []
    for i in range(len(stats[0])):
        final_stats.append(
            (
                stats[0][i].name,
                {
                    "time": merge_time_stats([stats[j][i].time for j in range(len(stats))]),
                    "counter": dict(sum([stats[j][i].counter for j in range(len(stats))], Counter())),
                },
            )
        )
    if save:
        raise NotImplementedError
    return final_stats
