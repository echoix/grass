from grass.gunittest.case import TestCase
from grass.gunittest.main import test
from grass.script.core import read_command

output = """cat
OBJECTID
WAKE_ZIPCO
PERIMETER
ZIPCODE_
ZIPCODE_ID
ZIPNAME
ZIPNUM
ZIPCODE
NAME
SHAPE_Leng
SHAPE_Area
"""


class TestDbColumns(TestCase):
    invect = "zipcodes"
    mapset = "$GISDBASE/$LOCATION_NAME/PERMANENT/sqlite/sqlite.db"

    @classmethod
    def setUpClass(cls):
        print(f"ed: db.columns: test_dbcolumns.py: setUpClass: __file__ is {__file__}")
        cls.runModule("db.connect", flags="c")

    def test_dbcols(self):
        print(f"ed: db.columns: test_dbcolumns.py: test_dbcols: __file__ is {__file__}")
        print("dir():")
        print(dir())
        print("locals()")
        print(locals())
        print("globals()")
        print(globals())
        cols = read_command("db.columns", table=self.invect, database=self.mapset)
        self.assertEqual(first=cols, second=output)


if __name__ == "__main__":
    print(
        f'ed: db.columns: test_dbcolumns.py: if __name__ == "__main__": '
        f" : __file__ is {__file__}"
    )
    test()
