"""Settings for all pytest tests"""

import os


def pytest_configure(config):
    """Keep messages in English for tests which check them

    The tests are written for English messages, so they would fail in a
    translated locale, e.g., when running on a system which is not English.
    """
    os.environ["LANGUAGE"] = "C"
