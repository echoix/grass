"""
Created on Sun Jun 08 12:50:45 2018

@author: Sanjeet Bhatti
"""

from pathlib import Path
from grass.gunittest.case import TestCase
from grass.gunittest.main import test
from grass.gunittest.gmodules import SimpleModule


class TestVUnpack(TestCase):
    """Test v.unpack script"""

    mapName = "roadsmajor"
    packFile = "roadsmajor.pack"

    @classmethod
    def setUpClass(cls):
        """Run v.pack to create packfile."""
        cls.runModule("v.pack", input=cls.mapName, output=cls.packFile)

    @classmethod
    def tearDownClass(cls):
        """Remove pack file created region"""
        cls.runModule("g.remove", type="vector", name=cls.mapName, flags="f")
        packFile_path = Path(cls.packFile)
        if packFile_path.is_file():
            packFile_path.unlink()

    def test_v_pack(self):
        """Unpack file test"""
        module = SimpleModule("v.unpack", input=self.packFile, overwrite=True)
        self.assertModule(module)


if __name__ == "__main__":
    test()
