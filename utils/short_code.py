import random
import string

from better_profanity import profanity


def generate_short_code(length: int = 6) -> str:
    """Generate a random base62-encoded short code."""

    alphabet = string.ascii_letters + string.digits

    return "".join(random.choices(alphabet, k=length))


def is_valid_custom_code(code: str) -> bool:
    """Validate a user-provided custom short code"""

    if not code:
        return False
    if len(code) < 3 or len(code) > 10:
        return False
    if not code.isalnum():
        return False
    if profanity.contains_profanity(code):
        return False

    return True
