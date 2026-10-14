"""
Tests checkers
"""

import doctest

import grass.gunittest.case
import grass.gunittest.main
import grass.gunittest.utils

import grass.script.array as garray
import grass.script.core as gcore
import grass.script.db as gdb
import grass.script.imagery as gimagery
import grass.script.raster as graster
import grass.script.raster3d as graster3d
import grass.script.task as gtask
import grass.script.utils as gutils
import grass.script.vector as gvector


# doctest does not allow changing the base classes of test case, skip test case
# and test suite, so we need to create a new type which inherits from our class
# and contains doctest's methods
# the alternative is to copy 500 from doctest and change what is needed
# (this might be necessary anyway because of the reports and stdout and stderr)
doctest.DocFileCase = type(
    "DocFileCase", (grass.gunittest.case.TestCase,), dict(doctest.DocFileCase.__dict__)
)
doctest.SkipDocTestCase = type(
    "SkipDocTestCase",
    (grass.gunittest.case.TestCase,),
    dict(doctest.SkipDocTestCase.__dict__),
)


def load_tests(loader, tests, ignore):
    # TODO: this must be somewhere when doctest is called, not here
    # TODO: ultimate solution is not to use _ as a builtin in lib/python
    # for now it is the only place where it works
    grass.gunittest.utils.do_doctest_gettext_workaround()
    # this should be called at some top level
    tests.addTests(doctest.DocTestSuite(garray))
    tests.addTests(doctest.DocTestSuite(gcore))
    tests.addTests(doctest.DocTestSuite(gdb))
    tests.addTests(doctest.DocTestSuite(gimagery))
    tests.addTests(doctest.DocTestSuite(graster))
    tests.addTests(doctest.DocTestSuite(graster3d))
    tests.addTests(doctest.DocTestSuite(gtask))
    tests.addTests(doctest.DocTestSuite(gutils))
    tests.addTests(doctest.DocTestSuite(gvector))
    return tests


if __name__ == "__main__":
    grass.gunittest.main.test()
