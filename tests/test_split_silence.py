from smpl_tools.actions import _determine_output_filenames
import unittest


class SplitSilenceTest(unittest.TestCase):


    def test_determine_multiple_filenames_extensionless_names_kept(self):
        extensionless_name = "my_src"
        result = _determine_output_filenames(None, extensionless_name, 1)
        self.assertTrue(extensionless_name in result[0])
        pass


    def test_determine_multiple_filenames_numbered_correctly(self):
        extensionless_name = "my_src"
        result = _determine_output_filenames(None, extensionless_name, 2)
        self.assertEquals(result, ["my_src_01.wav", "my_src_02.wav"])
        pass


