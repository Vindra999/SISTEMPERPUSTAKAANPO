"""Domain-specific exceptions for perpustakaan system."""


class UsernameAlreadyExists(Exception):
    """Raised when attempting to create a user with a username that already exists."""

    pass
