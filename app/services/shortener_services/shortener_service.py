from app.services.shortener_services.id_generator import id_generator
from app.services.shortener_services.Base62_encoder import encode_base62


def generate_short_code():
    unique_id = id_generator.generate_id()
    return encode_base62(unique_id)
