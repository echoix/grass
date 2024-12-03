"""
Created on Tue Jun 24 09:43:53 2014

@author: pietro
"""

from io import BytesIO

from grass.gunittest.case import TestCase
from grass.gunittest.main import test

from grass.pygrass.modules.interface import Module


SKIP = [
    "g.parser",
]


class TestModulesPickability(TestCase):
    def test_rsun(self):
        """Test if a Module instance is pickable"""
        import pickle

        out = BytesIO()
        pickle.dump(Module("r.sun"), out)
        out.close()


if __name__ == "__main__":
    test()
