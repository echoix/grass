"""
Created on Sun Jun 08 23:19:09 2018

@author: Sanjeet Bhatti
"""

from pathlib import Path
from grass.gunittest.case import TestCase
from grass.gunittest.main import test
from grass.gunittest.gmodules import SimpleModule


class TestVPack(TestCase):
    """Test v.pack script"""

    mapName = "roadsmajor"
    outFile = "roadsmajor.pack"

    @classmethod
    def tearDownClass(cls):
        """Remove output file"""
        outFile_path = Path(cls.outFile)
        if outFile_path.is_file():
            outFile_path.unlink()

    def test_v_pack(self):
        """Create a pack file test"""
        module = SimpleModule(
            "v.pack", input=self.mapName, output=self.outFile, overwrite=True
        )
        self.assertModule(module)

        self.assertFileExists(filename=self.outFile)


if __name__ == "__main__":
    test()
