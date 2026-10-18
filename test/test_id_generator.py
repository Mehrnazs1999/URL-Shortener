
import threading
from unittest.mock import patch

import pytest

from app.services.shortener_services.id_generator import (
    EPOCH,
    MAX_COUNTER,
    MAX_TIMESTAMP,
    TIMESTAMP_SHIFT,
    IDGenerator,
)


@pytest.fixture
def generator():
    return IDGenerator()


def test_generate_id_first_call(generator):
    with patch.object(
        generator,
        "_current_timestamp",
        return_value=100,
    ):
        result = generator.generate_id()

    assert result == (100 << TIMESTAMP_SHIFT) | 0
    assert generator.last_timestamp == 100
    assert generator.counter == 0


def test_generate_id_increments_counter_within_same_timestamp(generator):
    with patch.object(
        generator,
        "_current_timestamp",
        return_value=100,
    ):
        first_id = generator.generate_id()
        second_id = generator.generate_id()
        third_id = generator.generate_id()

    assert first_id == (100 << TIMESTAMP_SHIFT) | 0
    assert second_id == (100 << TIMESTAMP_SHIFT) | 1
    assert third_id == (100 << TIMESTAMP_SHIFT) | 2

    assert len({first_id, second_id, third_id}) == 3


def test_generate_id_resets_counter_when_timestamp_changes(generator):
    with patch.object(
        generator,
        "_current_timestamp",
        side_effect=[100, 100, 101],
    ):
        first_id = generator.generate_id()
        second_id = generator.generate_id()
        third_id = generator.generate_id()

    assert first_id == (100 << TIMESTAMP_SHIFT) | 0
    assert second_id == (100 << TIMESTAMP_SHIFT) | 1
    assert third_id == (101 << TIMESTAMP_SHIFT) | 0


def test_generate_id_rejects_time_before_epoch(generator):
    with patch.object(
        generator,
        "_current_timestamp",
        return_value=-1,
    ):
        with pytest.raises(
            RuntimeError,
            match="before the custom epoch",
        ):
            generator.generate_id()


def test_generate_id_rejects_timestamp_overflow(generator):
    with patch.object(
        generator,
        "_current_timestamp",
        return_value=MAX_TIMESTAMP + 1,
    ):
        with pytest.raises(
            RuntimeError,
            match="Timestamp capacity exceeded",
        ):
            generator.generate_id()


def test_generate_id_rejects_clock_going_backwards(generator):
    with patch.object(
        generator,
        "_current_timestamp",
        side_effect=[101, 100],
    ):
        generator.generate_id()

        with pytest.raises(
            RuntimeError,
            match="System clock moved backwards",
        ):
            generator.generate_id()


def test_generate_id_counter_overflow_waits_for_next_timestamp(generator):
    generator.last_timestamp = 100
    generator.counter = MAX_COUNTER

    with patch.object(
        generator,
        "_current_timestamp",
        side_effect=[100, 101],
    ), patch(
        "app.services.shortener_services.id_generator.time.sleep"
    ) as mock_sleep:
        result = generator.generate_id()

    assert result == (101 << TIMESTAMP_SHIFT) | 0
    assert generator.last_timestamp == 101
    assert generator.counter == 0
    mock_sleep.assert_called_once_with(0.001)


def test_generate_id_is_thread_safe(generator):
    number_of_threads = 20

    with patch.object(
        generator,
        "_current_timestamp",
        return_value=100,
    ):
        threads = [
            threading.Thread(target=generator.generate_id)
            for _ in range(number_of_threads)
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

    # Verify the counter advanced once for every call.
    assert generator.last_timestamp == 100
    assert generator.counter == number_of_threads - 1


def test_generate_id_is_thread_safe(generator):
    number_of_threads = 20
    results = []
    results_lock = threading.Lock()

    def generate_and_store():
        result = generator.generate_id()
        with results_lock:
            results.append(result)

    with patch.object(
        generator,
        "_current_timestamp",
        return_value=100,
    ):
        threads = [
            threading.Thread(target=generate_and_store)
            for _ in range(number_of_threads)
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

    assert len(results) == number_of_threads
    assert len(set(results)) == number_of_threads

    expected_ids = {
        (100 << TIMESTAMP_SHIFT) | counter
        for counter in range(number_of_threads)
    }
    assert set(results) == expected_ids
