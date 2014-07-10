"""Test t.rast.extract

(C) 2014 by the GRASS Development Team
This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.

@author Soeren Gebbert
"""

import grass.script as grass
import grass.pygrass.modules as pymod
import subprocess
from grass.gunittest.case import TestCase

class TestRasterExtraction(TestCase):

    @classmethod
    def setUpClass(cls):
        """!Initiate the temporal GIS and set the region
        """
        grass.use_temp_region()
        cls.runModule("g.gisenv",  set="TGIS_USE_CURRENT_MAPSET=1")
        cls.runModule("g.region",  s=0,  n=80,  w=0,  e=120,  b=0,  t=50,  res=10,  res3=10)

    @classmethod
    def tearDownClass(cls):
        """!Remove the temporary region
        """
        grass.del_temp_region()

    def setUp(self):
        """Create input data for transient groundwater flow computation
        """
        # Use always the current mapset as temporal database
        self.runModule("r.mapcalc", expression="prec_1 = 100")
        self.runModule("r.mapcalc", expression="prec_2 = 200")
        self.runModule("r.mapcalc", expression="prec_3 = 300")
        self.runModule("r.mapcalc", expression="prec_4 = 400")
        self.runModule("r.mapcalc", expression="prec_5 = 500")
        self.runModule("r.mapcalc", expression="prec_6 = 600")
        
        self.runModule("t.create",  type="strds",  temporaltype="absolute",  
                                     output="precip_abs1",  title="A test",  description="A test")
        self.runModule("t.register",  flags="i",  type="rast",  input="precip_abs1",  
                                     maps="prec_1,prec_2,prec_3,prec_4,prec_5,prec_6",  
                                     start="2001-01-01", increment="3 months")

    def tearDown(self):
        """Remove generated data"""
        self.runModule("t.remove",  flags="rf",  type="strds",  
                                   inputs="precip_abs1,precip_abs2")

    def test_selection(self):
        """Perform a simple selection by datetime"""
        self.assertModule("t.rast.extract",  input="precip_abs1",  output="precip_abs2", 
                                      where="start_time > '2001-06-01'")

        #self.assertModule("t.info",  flags="g",  input="precip_abs2")

        tinfo_string="""start_time=2001-07-01 00:00:00
        end_time=2002-07-01 00:00:00
        granularity=3 months
        map_time=interval
        north=80.0
        south=0.0
        east=120.0
        west=0.0
        top=0.0
        bottom=0.0
        aggregation_type=None
        number_of_maps=4
        nsres_min=10.0
        nsres_max=10.0
        ewres_min=10.0
        ewres_max=10.0
        min_min=300.0
        min_max=600.0
        max_min=300.0
        max_max=600.0"""

        self.assertModuleKeyValue(module="t.info",  
                                  parameters=dict(flags="g", input="precip_abs2"), 
                                  reference=tinfo_string, precision=2, sep="=")

    def test_selection_and_expression(self):
        """Perform a selection by datetime and a r.mapcalc expression"""
        self.assertModule("t.rast.extract",  input="precip_abs1",  output="precip_abs2", 
                                      where="start_time > '2001-06-01'",  
                                      expression=" if(precip_abs1 > 400, precip_abs1, null())", 
                                      basename="new_prec",  nprocs=2)

        #self.assertModule("t.info",  flags="g",  input="precip_abs2")

        tinfo_string="""start_time=2002-01-01 00:00:00
        end_time=2002-07-01 00:00:00
        granularity=3 months
        map_time=interval
        north=80.0
        south=0.0
        east=120.0
        west=0.0
        top=0.0
        bottom=0.0
        aggregation_type=None
        number_of_maps=2
        nsres_min=10.0
        nsres_max=10.0
        ewres_min=10.0
        ewres_max=10.0
        min_min=500.0
        min_max=600.0
        max_min=500.0
        max_max=600.0"""

        self.assertModuleKeyValue(module="t.info",  
                                  parameters=dict(flags="g", input="precip_abs2"), 
                                  reference=tinfo_string, precision=2, sep="=")

    def test_expression_with_empty_maps(self):
        """Perform r.mapcalc expression and register empty maps"""
        self.assertModule("t.rast.extract",  flags="n",  input="precip_abs1",  output="precip_abs2",
                                      expression=" if(precip_abs1 > 400, precip_abs1, null())", 
                                      basename="new_prec",  nprocs=2)

        #self.assertModule("t.info",  flags="g",  input="precip_abs2")

        tinfo_string="""start_time=2001-01-01 00:00:00
        end_time=2002-07-01 00:00:00
        granularity=3 months
        map_time=interval
        north=80.0
        south=0.0
        east=120.0
        west=0.0
        top=0.0
        bottom=0.0
        aggregation_type=None
        number_of_maps=6
        nsres_min=10.0
        nsres_max=10.0
        ewres_min=10.0
        ewres_max=10.0
        min_min=500.0
        min_max=600.0
        max_min=500.0
        max_max=600.0"""

        self.assertModuleKeyValue(module="t.info",  
                                  parameters=dict(flags="g", input="precip_abs2"), 
                                  reference=tinfo_string, precision=2, sep="=")

if __name__ == '__main__':
    from grass.gunittest.main import test
    test()
