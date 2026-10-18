import threading
import time


# Custom epoch: 2026-01-01 00:00:00 UTC
EPOCH = 1767225600

TIMESTAMP_BITS = 32
COUNTER_BITS = 12

MAX_TIMESTAMP = (1 << TIMESTAMP_BITS) - 1
MAX_COUNTER = (1 << COUNTER_BITS) - 1

COUNTER_SHIFT = 0
TIMESTAMP_SHIFT = COUNTER_BITS


class IDGenerator:
    def __init__(self):
        self.counter = 0
        self.last_timestamp = -1
        self.lock = threading.Lock()

    @staticmethod
    def _current_timestamp() -> int:
        return int(time.time()) - EPOCH

    def generate_id(self) -> int:
        with self.lock:
            timestamp = self._current_timestamp()

            if timestamp < 0:
                raise RuntimeError(
                    "Current time is before the custom epoch"
                )

            if timestamp > MAX_TIMESTAMP:
                raise RuntimeError("Timestamp capacity exceeded")

            if timestamp < self.last_timestamp:
                raise RuntimeError("System clock moved backwards")

            if timestamp == self.last_timestamp:
                self.counter += 1

                if self.counter > MAX_COUNTER:
                    while timestamp <= self.last_timestamp:
                        time.sleep(0.001)
                        timestamp = self._current_timestamp()

                    if timestamp > MAX_TIMESTAMP:
                        raise RuntimeError("Timestamp capacity exceeded")

                    self.counter = 0
            else:
                self.counter = 0

            self.last_timestamp = timestamp

            return (timestamp << TIMESTAMP_SHIFT) | self.counter


id_generator = IDGenerator()
