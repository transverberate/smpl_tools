from smpl_tools.actions import _determine_output_samplenames, _process_naming_pattern
import unittest


class SplitSilenceTest(unittest.TestCase):


    def test_determine_multiple_filenames_extensionless_names_kept(self):
        extensionless_name = "my_src"
        result = _determine_output_samplenames(None, extensionless_name, 1)
        self.assertTrue(extensionless_name in result[0])
        pass


    def test_determine_multiple_filenames_numbered_correctly(self):
        extensionless_name = "my_src"
        result = _determine_output_samplenames(None, extensionless_name, 2)
        self.assertEquals(result, ["my_src_01.wav", "my_src_02.wav"])
        pass


    def test_naming_pattern_replacement(self):
        test_pattern = "%(trck)/%(smpl).wav"
        result = _process_naming_pattern(
            test_pattern,
            sample_name="alpha1",
            track_name="track01"
        )
        self.assertEquals(result, "track01/alpha1.wav")

    
    def test_naming_pattern_replacement_removes_sample_ext(self):
        test_pattern = "%(trck)/%(smpl).wav"
        result = _process_naming_pattern(
            test_pattern,
            sample_name="alpha1.wav",
            track_name="track01"
        )
        self.assertEquals(result, "track01/alpha1.wav")


    def test_naming_pattern_replacement_removes_track_ext(self):
        test_pattern = "%(trck)/%(smpl).wav"
        result = _process_naming_pattern(
            test_pattern,
            sample_name="alpha1",
            track_name="track01.wav"
        )
        self.assertEquals(result, "track01/alpha1.wav")


    def test_naming_pattern_replacement_adds_ext(self):
        test_pattern = "%(trck)/%(smpl)"
        result = _process_naming_pattern(
            test_pattern,
            sample_name="alpha1.wav",
            track_name="track01"
        )
        self.assertEquals(result, "track01/alpha1.wav")


