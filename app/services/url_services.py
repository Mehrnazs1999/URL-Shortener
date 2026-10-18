from app.services.exceptions import URLNotFoundError


def create_short_url(original_url: str):
    # TO DO
    return None


def get_original_url(short_code: str):
    # TO DO
    raise URLNotFoundError(f"Short URL not found: {short_code}")


def get_url_stats(short_code: str):
    # TO DO
    raise URLNotFoundError(f"Short URL not found: {short_code}")
