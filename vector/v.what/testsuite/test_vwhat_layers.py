import os
from pathlib import Path
import shutil
import sys
import unittest
import pytest

from grass.gunittest.case import TestCase
from grass.gunittest.main import test
from grass.gunittest.gmodules import SimpleModule

out1 = """East: 634243
North: 226193
------------------------------------------------------------------
Map: test_vector
Mapset: ...
Type: Area
Sq Meters: 633834.281
Hectares: 63.383
Acres: 156.624
Sq Miles: 0.2447
Layer: 1
Category: 2
Layer: 1
Category: 1
Layer: 2
Category: 3
Layer: 2
Category: 4
"""


out2 = """East: 634243
North: 226193
------------------------------------------------------------------
Map: test_vector
Mapset: ...
Type: Area
Sq Meters: 633834.281
Hectares: 63.383
Acres: 156.624
Sq Miles: 0.2447
Layer: 1
Category: 2

Driver: ...
Database: ...
Table: t1
Key column: cat_
Layer: 1
Category: 1

Driver: ...
Database: ...
Table: t1
Key column: cat_
cat_ : 1
text : Petrášová
number : 6
Layer: 2
Category: 3

Driver: ...
Database: ...
Table: t2
Key column: cat_
Layer: 2
Category: 4

Driver: ...
Database: ...
Table: t2
Key column: cat_
cat_ : 4
text : yyy
number : 8.09
"""

out3 = """East=634243
North=226193

Map=test_vector
Mapset=...
Type=Area
Sq_Meters=633834.281
Hectares=63.383
Acres=156.624
Sq_Miles=0.2447
Layer=1
Category=2
Driver=...
Database=...
Table=t1
Key_column=cat_
Layer=1
Category=1
Driver=...
Database=...
Table=t1
Key_column=cat_
cat_=1
text=Petrášová
number=6
Layer=2
Category=3
Driver=...
Database=...
Table=t2
Key_column=cat_
Layer=2
Category=4
Driver=...
Database=...
Table=t2
Key_column=cat_
cat_=4
text=yyy
number=8.09
"""

out4 = """East=634243
North=226193

Map=test_vector
Mapset=...
Type=Area
Sq_Meters=633834.281
Hectares=63.383
Acres=156.624
Sq_Miles=0.2447
Layer=1
Category=2
Driver=...
Database=...
Table=t1
Key_column=cat_
Layer=1
Category=1
Driver=...
Database=...
Table=t1
Key_column=cat_
cat_=1
text=Petrášová
number=6
"""

out5 = """East=634243
North=226193

Map=test_vector
Mapset=...
Type=Area
Sq_Meters=633834.281
Hectares=63.383
Acres=156.624
Sq_Miles=0.2447
Layer=2
Category=3
Layer=2
Category=4
"""


def _win32_longpath(path):
    """
    Helper function to add the long path prefix for Windows, so that shutil.copytree
    won't fail while working with paths with 255+ chars.

    From: https://github.com/gabrielcnr/pytest-datadir/blob/4c6557e4b4e33dc1fc0645dfc43bbe0527733c17/src/pytest_datadir/plugin.py#L8-L30
    Pytest plugin: "pytest-datadir"
    Author of pytest plugin: "Gabriel Reis"
    License of plugin: MIT
    SPDX-License-Identifier: MIT
    """
    if sys.platform == "win32":
        # The use of os.path.normpath here is necessary since "the "\\?\" prefix
        # to a path string tells the Windows APIs to disable all string parsing
        # and to send the string that follows it straight to the file system".
        # (See https://docs.microsoft.com/pt-br/windows/desktop/FileIO/naming-a-file)
        normalized = os.path.normpath(path)
        if not normalized.startswith("\\\\?\\"):
            is_unc = normalized.startswith("\\\\")
            # see https://en.wikipedia.org/wiki/Path_(computing)#Universal_Naming_Convention # noqa: E501
            if (
                is_unc
            ):  # then we need to insert an additional "UNC\" to the longpath prefix
                normalized = normalized.replace("\\\\", "\\\\?\\UNC\\")
            else:
                normalized = "\\\\?\\" + normalized
        return normalized
    return path


# @pytest.fixture()
# def gunittest_datadir() -> None:
#     """Fixture to change directory to a temporary directory containing a copy of the data directory"""
#     print("overridden gunittest_datadir fixture (function scope)")
#     return


# @pytest.fixture(autouse=True)
# def gunittest_datadir() -> None:
#     """Fixture to change directory to a temporary directory containing a copy of the data directory"""
#     print("overridden gunittest_datadir fixture (function scope)")
#     return


# @pytest.fixture(autouse=True)
# def gunittest_datadir(
#     monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest, tmp_path: Path
# ) -> None:
#     """Fixture to change directory to a temporary directory containing a copy of the data directory"""
#     print("overridden gunittest_datadir fixture (function scope)")
#     return
# print("request.path: ", request.path)
# parent_path = request.path.parent
# if parent_path.name == "testsuite":
#     original_data_path = os.path.join(parent_path, "data")
#     if (
#         os.path.isdir(original_data_path)
#         and os.path.basename(os.path.dirname(original_data_path)) == "testsuite"
#     ):
#         temp_path = tmp_path / "data"
#         print("in a testsuite/data folder, copying to", temp_path)
#         shutil.copytree(
#             src=_win32_longpath(original_data_path),
#             dst=_win32_longpath(str(temp_path)),
#         )

#     monkeypatch.chdir(tmp_path)
# else:
#     print("not in a testsuite dir")


@pytest.fixture(autouse=False)
def gunittest_datadir(
    monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest, tmp_path: Path
) -> None:
    """Fixture to change directory to a temporary directory containing a copy of the data directory"""
    print("overridden gunittest_datadir fixture (function scope)")
    # return
    print("request.path: ", request.path)
    parent_path = request.path.parent
    if parent_path.name == "testsuite":
        original_data_path = os.path.join(parent_path, "data")
        if (
            os.path.isdir(original_data_path)
            and os.path.basename(os.path.dirname(original_data_path)) == "testsuite"
        ):
            temp_path = tmp_path / "data"
            print("in a testsuite/data folder, copying to", temp_path)
            shutil.copytree(
                src=_win32_longpath(original_data_path),
                dst=_win32_longpath(str(temp_path)),
            )

        monkeypatch.chdir(tmp_path)
    else:
        print("not in a testsuite dir")


@pytest.fixture(autouse=False)
def gunittest_datadir2(
    monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest, tmp_path: Path
) -> None:
    """Fixture to change directory to a temporary directory containing a copy of the data directory"""
    print("overridden gunittest_datadir fixture (function scope)")
    # return
    print("request.path: ", request.path)
    parent_path = request.path.parent
    if parent_path.name == "testsuite":
        original_data_path = os.path.join(parent_path, "data")
        if (
            os.path.isdir(original_data_path)
            and os.path.basename(os.path.dirname(original_data_path)) == "testsuite"
        ):
            temp_path = tmp_path / "data"
            print("in a testsuite/data folder, copying to", temp_path)
            shutil.copytree(
                src=_win32_longpath(original_data_path),
                dst=_win32_longpath(str(temp_path)),
            )

        monkeypatch.chdir(tmp_path)
    else:
        print("not in a testsuite dir")


@pytest.fixture(autouse=False)
def _a_gunittest_datadir2(
    monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest, tmp_path: Path
) -> None:
    """Fixture to change directory to a temporary directory containing a copy of the data directory"""
    print("overridden gunittest_datadir fixture (function scope)")
    # return
    print("request.path: ", request.path)
    parent_path = request.path.parent
    if parent_path.name == "testsuite":
        original_data_path = os.path.join(parent_path, "data")
        if (
            os.path.isdir(original_data_path)
            and os.path.basename(os.path.dirname(original_data_path)) == "testsuite"
        ):
            temp_path = tmp_path / "data"
            print("in a testsuite/data folder, copying to", temp_path)
            shutil.copytree(
                src=_win32_longpath(original_data_path),
                dst=_win32_longpath(str(temp_path)),
            )

        monkeypatch.chdir(tmp_path)
    else:
        print("not in a testsuite dir")


# @pytest.fixture(autouse=True)
# @pytest.fixture(autouse=True, scope="class")
# def gunittest_datadir_class(
#     monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest, tmp_path: Path
# ) -> None:
#     """Fixture to change directory to a temporary directory containing a copy of the data directory"""
#     print("overridden gunittest_datadir fixture (class scope)")
#     print("request.path: ", request.path)
#     parent_path = request.path.parent
#     if parent_path.name == "testsuite":
#         original_data_path = os.path.join(parent_path, "data")
#         if (
#             os.path.isdir(original_data_path)
#             and os.path.basename(os.path.dirname(original_data_path)) == "testsuite"
#         ):
#             temp_path = tmp_path / "data"
#             print("in a testsuite/data folder, copying to", temp_path)
#             shutil.copytree(
#                 src=_win32_longpath(original_data_path),
#                 dst=_win32_longpath(str(temp_path)),
#             )

#         monkeypatch.chdir(tmp_path)
#     else:
#         print("not in a testsuite dir")


# @pytest.fixture(autouse=True, scope="class")
@pytest.fixture(scope="class")
def gunittest_datadir_class(
    monkeypatch_class,
    request: pytest.FixtureRequest,
    tmp_path: Path,
) -> None:
    """Fixture to change directory to a temporary directory containing a copy of the data directory"""
    print("overridden gunittest_datadir fixture (class scope)")
    print("request.path: ", request.path)
    parent_path = request.path.parent
    if parent_path.name == "testsuite":
        original_data_path = os.path.join(parent_path, "data")
        if (
            os.path.isdir(original_data_path)
            and os.path.basename(os.path.dirname(original_data_path)) == "testsuite"
        ):
            temp_path = tmp_path / "data"
            print("in a testsuite/data folder, copying to", temp_path)
            shutil.copytree(
                src=_win32_longpath(original_data_path),
                dst=_win32_longpath(str(temp_path)),
            )

        monkeypatch_class.chdir(tmp_path)
    else:
        print("not in a testsuite dir")


class TestMultiLayerMap(TestCase):
    fixture = ["gunittest_datadir"]
    # @classmethod
    # def setup_class(cls):
    #     # def setup_class(cls, gunittest_datadir):
    #     """setup any state specific to the execution of the given class (which
    #     usually contains tests).
    #     """
    #     print("setup_class was called")

    # @pytest.fixture(autouse=True, scope="class")
    # def setUpClassImpl(self, gunittest_datadir):
    # @pytest.fixture(autouse=True)
    def setUpClassImpl(self):
        print("setUpClassImpl was called")
        self.runModule(
            "v.in.ascii",
            input="./data/testing.ascii",
            output="test_vector",
            format="standard",
        )
        self.runModule("db.connect", flags="c")
        self.runModule("db.in.ogr", input="./data/table1.csv", output="t1")
        self.runModule("db.in.ogr", input="./data/table2.csv", output="t2")
        self.runModule(
            "v.db.connect", map="test_vector", table="t1", key="cat_", layer=1
        )
        self.runModule(
            "v.db.connect", map="test_vector", table="t2", key="cat_", layer=2
        )

    @classmethod
    def setUpClass(cls):
        print("setUpClass was called")
        super().setUpClass()
        print("setUpClass (after super) was called")
        # if os.environ.get("PYTEST_VERSION") is not None:
        #     return
        print("setUpClass (after pytest guard) was called")

        cls.runModule(
            "v.in.ascii",
            input="./data/testing.ascii",
            output="test_vector",
            format="standard",
        )
        cls.runModule("db.connect", flags="c")
        cls.runModule("db.in.ogr", input="./data/table1.csv", output="t1")
        cls.runModule("db.in.ogr", input="./data/table2.csv", output="t2")
        cls.runModule(
            "v.db.connect", map="test_vector", table="t1", key="cat_", layer=1
        )
        cls.runModule(
            "v.db.connect", map="test_vector", table="t2", key="cat_", layer=2
        )

    @classmethod
    def tearDownClass(cls):
        cls.runModule("g.remove", type="vector", name="test_vector", flags="f")

    def setUp(self):
        # if os.environ.get("PYTEST_VERSION") is not None:
        #     print(os.getcwd())
        #     self.setUpClassImpl()
        self.vwhat = SimpleModule(
            "v.what", map="test_vector", coordinates=[634243, 226193], distance=10
        )

    # def tearDown(self):
    #     if os.environ.get("PYTEST_VERSION") is not None:
    #         self.runModule("g.remove", type="vector", name="test_vector", flags="f")

    @unittest.expectedFailure
    @pytest.mark.usefixtures("gunittest_datadir2")
    def test_run(self):
        self.assertModule(self.vwhat)
        self.assertLooksLike(reference=out1, actual=self.vwhat.outputs.stdout)

    @unittest.expectedFailure
    @pytest.mark.usefixtures("_a_gunittest_datadir2")
    def test_print_options(self):
        self.vwhat.flags["a"].value = True
        self.assertModule(self.vwhat)
        self.assertLooksLike(reference=out2, actual=self.vwhat.outputs.stdout)

        self.vwhat.flags["g"].value = True
        self.assertModule(self.vwhat)
        self.assertLooksLike(reference=out3, actual=self.vwhat.outputs.stdout)

    @unittest.expectedFailure
    def test_print_options_json(self):
        import json

        self.vwhat.flags["j"].value = True
        self.vwhat.flags["a"].value = True
        self.assertModule(self.vwhat)
        try:
            json.loads(self.vwhat.outputs.stdout)
        except ValueError:
            self.fail(
                msg="No JSON object could be decoded:\n" + self.vwhat.outputs.stdout
            )

    def test_selected_layers(self):
        self.vwhat.inputs.layer = -1
        self.vwhat.flags["g"].value = True
        self.vwhat.flags["a"].value = True
        self.assertModule(self.vwhat)
        self.assertLooksLike(reference=out3, actual=self.vwhat.outputs.stdout)

        self.vwhat.inputs.layer = 1
        self.assertModule(self.vwhat)
        self.assertLooksLike(reference=out4, actual=self.vwhat.outputs.stdout)

        self.vwhat.inputs.layer = 2
        self.vwhat.flags["a"].value = False
        self.assertModule(self.vwhat)
        self.assertLooksLike(reference=out5, actual=self.vwhat.outputs.stdout)


if __name__ == "__main__":
    test()
