import unittest

from astrosync import Syncer
import os
import shutil
import tempfile

class TestPbdb(unittest.TestCase):

    def test_journal_entries(self):

        src = "tests/fixtures/journalentries/Apps/Postbox"
        dst = "tests/fixtures/journalentries/writing/2024"

        # FIXME: tmpdir instead
        jdst = os.path.join(dst, "journal")
        for f in os.listdir(jdst):
            os.remove(os.path.join(jdst, f))

        syncer = Syncer(src, dst, False)
        syncer.sync()

        with open(os.path.join(src, "A", "2024-06-01 journal0601.txt")) as f: orig_a = f.read()
        with open(os.path.join(dst, "journal", "journal0601.txt")) as f: copy_a = f.read()
        self.assertEqual(orig_a, copy_a)

        with open(os.path.join(src, "B", "2024-12-15 journal1215.txt")) as f: orig_b = f.read()
        with open(os.path.join(dst, "journal", "journal1215.txt")) as f: copy_b = f.read()
        self.assertEqual(orig_b, copy_b)

        self.assertGreater(len(orig_a), 0)
        self.assertGreater(len(copy_a), 0)
        self.assertGreater(len(orig_b), 0)
        self.assertGreater(len(copy_b), 0)

    def test_normal_entries(self):

        fxt = "tests/fixtures/telltale"
        with tempfile.TemporaryDirectory() as tmpdir:
            shutil.copytree(fxt, os.path.join(tmpdir), dirs_exist_ok=True)
            src = os.path.join(tmpdir, "Apps/Postbox")
            dst = os.path.join(tmpdir, "writing/2024")

            syncer = Syncer(src, dst, False)
            syncer.sync()

            with open(os.path.join(src, "A", "2024-06-09 telltale.txt")) as f: orig_a = f.read()
            with open(os.path.join(src, "B", "2024-03-06 telltale01.txt")) as f: orig_b = f.read()
            with open(os.path.join(src, "B", "2024-04-02 telltale.txt")) as f: orig_c = f.read()
            with open(os.path.join(src, "B", "2024-05-01 telltale -1937bc80-.txt")) as f: orig_d = f.read()

            with open(os.path.join(dst, "telltale", "telltale10.txt")) as f: copy_a = f.read()
            self.assertEqual(len(copy_a), 11170)
            dst_files = syncer.get_dst_files()

            self.assertEqual(len(dst_files), 4)

            self.assertEqual("telltale", dst_files[0].file_story)
            self.assertEqual(10, dst_files[0].num)
            self.assertEqual("d4b82d5e74e24fc19d589b0ec4cd42c4d85a1cea784e2f325a95ecbb14a07d15", dst_files[0].hash)

            self.assertEqual("telltale", dst_files[1].file_story)
            self.assertEqual(11, dst_files[1].num)
            self.assertEqual("1a017362ef266a78241a27f1402bd7bdc71c596ba956ac0870a64a3a0b409992", dst_files[1].hash)

            self.assertEqual("telltale", dst_files[2].file_story)
            self.assertEqual(12, dst_files[2].num)
            self.assertEqual("8a41c3a67d91a147c138e0e12de3246318a7c49e068fc2c2e87a349619a03940", dst_files[2].hash)

            self.assertEqual("telltale", dst_files[3].file_story)
            self.assertEqual(13, dst_files[3].num)
            self.assertEqual("8198588fe0e681e90330c9ee2250089d89bbde17f20e7bd330fabc2bed3bc428", dst_files[3].hash)


if __name__ == '__main__':
    unittest.main()