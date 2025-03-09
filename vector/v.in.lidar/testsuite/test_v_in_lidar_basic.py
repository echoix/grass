"""
Name:      decimation_test
Purpose:   v.in.lidar decimation test

Author:    Vaclav Petras
Copyright: (C) 2015 by Vaclav Petras and the GRASS Development Team
Licence:   This program is free software under the GNU General Public
           License (>=v2). Read the file COPYING that comes with GRASS
           for details.
"""

import os
import shutil
import unittest
from grass.gunittest.case import TestCase
from grass.gunittest.main import test


@unittest.skipUnless(shutil.which("v.out.lidar"), "Needs v.out.lidar")
class BasicTest(TestCase):
    """Test case for watershed module

    This tests expects v.random and v.out.lidar to work properly.
    """

    # Setup variables to be used for outputs
    vector_points = "vinlidar_basic_original"
    imported_points = "vinlidar_basic_imported"
    las_file = "vinlidar_basic_points.las"
    npoints = 300

    @classmethod
    def setUpClass(cls):
        """Ensures expected computational region and generated data"""
        cls.use_temp_region()
        cls.addClassCleanup(cls.del_temp_region)
        cls.runModule("g.region", n=20, s=10, e=25, w=15, res=1)
        cls.runModule(
            "v.random",
            flags="zb",
            output=cls.vector_points,
            npoints=cls.npoints,
            zmin=200,
            zmax=500,
            seed=100,
        )
        cls.addClassCleanup(
            cls.runModule, "g.remove", flags="f", type="vector", name=cls.vector_points
        )
        cls.runModule("v.out.lidar", input=cls.vector_points, output=cls.las_file)
        cls.addClassCleanup(
            lambda x: os.remove(x) if os.path.isfile(x) else None, cls.las_file
        )

    def tearDown(self):
        """Remove the outputs created by the import

        This is executed after each test run.
        """
        self.runModule("g.remove", flags="f", type="vector", name=self.imported_points)

    def test_output_identical(self):
        """Test to see if the standard outputs are created"""
        self.assertModule(
            "v.in.lidar", input=self.las_file, output=self.imported_points, flags="bt"
        )
        self.assertVectorExists(self.imported_points)
        self.assertVectorEqualsVector(
            actual=self.imported_points,
            reference=self.vector_points,
            digits=2,
            precision=0.01,
        )


if __name__ == "__main__":
    test()
