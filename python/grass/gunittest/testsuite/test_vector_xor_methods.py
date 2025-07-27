"""
Tests for vector XOR computation methods and assertVectorsNoAreaDifference assertion.

This test covers the fix where _compute_xor_vectors was renamed to _compute_vector_xor
in the assertVectorsNoAreaDifference method.
"""

from grass.gunittest.case import TestCase
from grass.gunittest.gmodules import SimpleModule
from grass.gunittest.main import test


class TestVectorXorMethods(TestCase):
    """Test vector XOR computation methods and related assertions"""

    # pylint: disable=R0904
    maps_to_remove = []

    # Test data for creating simple vector maps
    square1_coords = """1|0|0
1|1|0
1|1|1
1|0|1
1|0|0"""

    square2_coords = """1|0.5|0
1|1.5|0
1|1.5|1
1|0.5|1
1|0.5|0"""

    square3_coords = """1|2|0
1|3|0
1|3|1
1|2|1
1|2|0"""

    @classmethod
    def setUpClass(cls):
        """Set up test environment with temporary region and test vector maps"""
        cls.use_temp_region()
        cls.runModule("g.region", n=5, s=-1, e=5, w=-1, res=0.1)

        # Create test vector maps with overlapping and non-overlapping areas
        cls._create_test_vector("test_square1", cls.square1_coords)
        cls._create_test_vector(
            "test_square2", cls.square2_coords
        )  # Partially overlaps with square1
        cls._create_test_vector(
            "test_square3", cls.square3_coords
        )  # No overlap with square1

        cls.maps_to_remove.extend(["test_square1", "test_square2", "test_square3"])

    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        cls.del_temp_region()
        if cls.maps_to_remove:
            cls.runModule(
                "g.remove", flags="f", type="vector", name=",".join(cls.maps_to_remove)
            )

    @classmethod
    def _create_test_vector(cls, name, coords):
        """Helper method to create test vector maps from coordinate strings"""
        # Create temporary ASCII file with vector data
        import os
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("VERTI:\n")
            f.write(coords + "\n")
            f.write("1  1\n")
            temp_file = f.name

        try:
            cls.runModule("v.in.ascii", input=temp_file, output=name, format="standard")
        finally:
            os.unlink(temp_file)

    def test_compute_vector_xor_basic(self):
        """Test basic functionality of _compute_vector_xor method"""
        # Test XOR between two overlapping areas
        result = self._compute_vector_xor(
            ainput="test_square1",
            alayer="1",
            binput="test_square2",
            blayer="1",
            name_part="test_basic",
        )

        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)

        # Verify the result vector exists
        module = SimpleModule("v.info", map=result, flags="t")
        self.runModule(module)

        # Clean up the generated map
        self.runModule("g.remove", flags="f", type="vector", name=result)

    def test_compute_vector_xor_no_overlap(self):
        """Test _compute_vector_xor with non-overlapping areas"""
        result = self._compute_vector_xor(
            ainput="test_square1",
            alayer="1",
            binput="test_square3",
            blayer="1",
            name_part="test_no_overlap",
        )

        self.assertIsNotNone(result)

        # Clean up the generated map
        self.runModule("g.remove", flags="f", type="vector", name=result)

    def test_assertVectorsNoAreaDifference_identical(self):
        """Test assertVectorsNoAreaDifference with identical vectors"""
        # Should pass when comparing identical vectors
        self.assertVectorsNoAreaDifference(
            actual="test_square1", reference="test_square1", precision=0.001, layer=1
        )

    def test_assertVectorsNoAreaDifference_different(self):
        """Test assertVectorsNoAreaDifference with different vectors"""
        # Should fail when comparing different vectors
        with self.assertRaises(self.failureException):
            self.assertVectorsNoAreaDifference(
                actual="test_square1",
                reference="test_square2",
                precision=0.001,
                layer=1,
            )

    def test_assertVectorsNoAreaDifference_precision(self):
        """Test assertVectorsNoAreaDifference precision handling"""
        # Test with large precision that might allow small differences
        self.assertVectorsNoAreaDifference(
            actual="test_square1",
            reference="test_square1",
            precision=1000.0,  # Very large precision
            layer=1,
        )

    def test_assertVectorsNoAreaDifference_custom_message(self):
        """Test assertVectorsNoAreaDifference with custom message"""
        custom_msg = "Custom error message for test"

        with self.assertRaises(self.failureException) as cm:
            self.assertVectorsNoAreaDifference(
                actual="test_square1",
                reference="test_square2",
                precision=0.001,
                layer=1,
                msg=custom_msg,
            )

        # Verify custom message is included
        self.assertIn(custom_msg, str(cm.exception))

    def test_assertVectorsNoAreaDifference_layer_parameter(self):
        """Test assertVectorsNoAreaDifference with different layer parameter"""
        # Test with layer 1 (should work since our test maps have layer 1)
        self.assertVectorsNoAreaDifference(
            actual="test_square1", reference="test_square1", precision=0.001, layer=1
        )


if __name__ == "__main__":
    test()
