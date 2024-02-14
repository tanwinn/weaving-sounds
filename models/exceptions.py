"""
models.exceptions
~~~~~~~~~~~~~~
Database & Server exceptions
"""


class DuplicatedError(Exception):
    """Database Duplicated Error"""


class NotFound(Exception):
    """Database Not Found Error"""


class InputError(Exception):
    """User's Message Input Error"""
