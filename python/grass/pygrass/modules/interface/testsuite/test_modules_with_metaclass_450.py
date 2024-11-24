"""
Created on Tue Jun 24 09:43:53 2014

@author: pietro
"""

# ruff: noqa: LOG015
from fnmatch import fnmatch
from itertools import islice
from logging import warning

from grass.gunittest.case import TestCase
from grass.gunittest.main import test

from grass.script.core import get_commands
from grass.pygrass.modules.interface import Module


SKIP = [
    "g.parser",
]


class ModulesMeta(type):
    def __new__(cls, name, bases, dict):
        warning("In __new__ of ModulesMeta")
        print("In __new__ of ModulesMeta")

        def gen_test(cmd):
            def test(self):
                Module(cmd)

            return test

        cmds = [
            c
            for c in sorted(list(get_commands()[0]))
            if c not in SKIP and not fnmatch(c, "g.gui.*")
        ]
        for cmd in islice(cmds, 400, 450):
            test_name = "test__%s" % cmd.replace(".", "_")
            warning("cmd is: %s, test_name: %s", cmd, test_name)
            print(f"cmd is: {cmd}, test_name: {test_name}")
            dict[test_name] = gen_test(cmd)
        return type.__new__(cls, name, bases, dict)


class TestModules(TestCase, metaclass=ModulesMeta):
    pass


if __name__ == "__main__":
    warning("Starting test of %s", __file__)
    test()
