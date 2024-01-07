import unittest


class TestResult(unittest.TestResult):
    # descriptions and verbosity unused
    # included for compatibility with unittest's TestResult
    # where are also unused, so perhaps we can remove them
    # stream set to None and not included in interface, it would not make sense
    def __init__(self, stream=None, descriptions=None, verbosity=2, **kwargs):
        super().__init__(
            stream=stream, descriptions=descriptions, verbosity=verbosity, **kwargs
        )
        self.successes = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.successes.append(test)

    # TODO: better would be to pass start at the beginning
    # alternative is to leave counting time on class
    # TODO: document: we expect all grass classes to have setTimes
    # TODO: alternatively, be more forgiving for non-unittest methods
    def setTimes(self, start_time, end_time, time_taken):
        pass
        # TODO: implement this
