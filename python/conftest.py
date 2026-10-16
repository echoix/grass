"""Settings for pytest tests"""

import os

# The tests are written for English messages, so they would fail in a
# translated locale, e.g., when running on a system which is not English.
os.environ["LANGUAGE"] = "C"
