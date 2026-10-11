"""Settings for pytest tests"""

import pytest


@pytest.fixture(scope="session", autouse=True)
def english_messages():
    """Keep messages in English for tests which check them

    The tests are written for English messages, so they would fail in a
    translated locale, e.g., when running on a system which is not English.
    """
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setenv("LANGUAGE", "C")
        yield
