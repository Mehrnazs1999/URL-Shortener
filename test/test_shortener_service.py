from unittest.mock import patch

from app.services.shortener_services.shortener_service import (
    generate_short_code,
)


def test_generate_short_code_generates_id_and_encodes_it():
    with patch(
        "app.services.shortener_services.shortener_service.id_generator.generate_id",
        return_value=12345,
    ) as mock_generate_id, patch(
        "app.services.shortener_services.shortener_service.encode_base62",
        return_value="3D7",
    ) as mock_encode:

        result = generate_short_code()

    assert result == "3D7"
    mock_generate_id.assert_called_once_with()
    mock_encode.assert_called_once_with(12345)
