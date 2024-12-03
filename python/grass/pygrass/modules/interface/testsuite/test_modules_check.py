"""
Created on Tue Jun 24 09:43:53 2014

@author: pietro
"""

from grass.gunittest.case import TestCase
from grass.gunittest.main import test

from grass.exceptions import ParameterError
from grass.pygrass.modules.interface import Module


SKIP = [
    "g.parser",
]


class TestModulesCheck(TestCase):
    def test_flags_with_suppress_required(self):
        """Test if flags with suppress required are handle correctly"""
        gextension = Module("g.extension")
        # check if raise an error if required parameter are missing
        with self.assertRaises(ParameterError):
            gextension.check()

        # check if the flag suppress the required parameters
        gextension.flags.a = True
        self.assertIsNone(gextension.check())


if __name__ == "__main__":
    test()
