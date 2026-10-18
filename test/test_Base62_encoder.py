
import pytest

from app.services.shortener_services.Base62_encoder import ALPHABET, encode_base62


def test_encode_zero():
    assert encode_base62(0) == "0"


@pytest.mark.parametrize(
    ("number", "expected"),
    [
        (1, "1"),
        (9, "9"),
        (10, "a"),
        (35, "z"),
        (36, "A"),
        (61, "Z"),
        (62, "10"),
        (63, "11"),
        (123, "1Z"),
        (3844, "100"),
    ],
)
def test_encode_base62_values(number, expected):
    assert encode_base62(number) == expected


@pytest.mark.parametrize("number", [-1, -100, -999999])
def test_encode_negative_number_raises_value_error(number):
    with pytest.raises(
        ValueError,
        match="number must be non-negative",
    ):
        encode_base62(number)


def test_encode_large_number():
    number = 2**64 - 1

    result = encode_base62(number)

    assert result
    assert all(char in ALPHABET for char in result)


def test_encoded_result_contains_only_base62_characters():
    result = encode_base62(123456789)

    assert all(char in ALPHABET for char in result)


@pytest.mark.parametrize("number", range(1000))
def test_encode_result_decodes_back_to_original_number(number):
    encoded = encode_base62(number)

    decoded = 0
    for char in encoded:
        decoded = decoded * 62 + ALPHABET.index(char)

    assert decoded == number
