"""Hesap modülü testleri. Çalıştırma: python -m unittest discover -s tests"""
import contextlib
import io
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from mesh_data import MeshData  # noqa: E402
from rebar_calculator import RebarCalculator, RebarData  # noqa: E402


class CalculatorTestCase(unittest.TestCase):
    def setUp(self):
        # Hesaplayıcı logs/ ve rapor klasörlerini çalışma dizinine yazar
        self._cwd = os.getcwd()
        self._tmp = tempfile.TemporaryDirectory()
        os.chdir(self._tmp.name)
        self._quiet = contextlib.redirect_stdout(io.StringIO())
        self._quiet.__enter__()
        self.calc = RebarCalculator()

    def tearDown(self):
        self._quiet.__exit__(None, None, None)
        for handler in list(self.calc.logger.handlers):
            handler.close()
            self.calc.logger.removeHandler(handler)
        os.chdir(self._cwd)
        self._tmp.cleanup()

    def only_result(self):
        self.assertEqual(len(self.calc.results), 1)
        return self.calc.results[0]


class RebarTextTests(CalculatorTestCase):
    def test_counted_rebar(self):
        self.assertTrue(self.calc.process_text("2X13∅20 L=397"))
        r = self.only_result()
        self.assertEqual(r.piece_count, 26)
        self.assertAlmostEqual(r.total_length, 10322)
        self.assertAlmostEqual(r.total_weight, 103.22 * 2.466, places=3)

    def test_autocad_diameter_code(self):
        self.assertTrue(self.calc.process_text("3%%C16 L=450"))
        self.assertAlmostEqual(self.only_result().total_weight, 13.5 * 1.578, places=3)

    def test_spaced_rebar_waits_for_dimension(self):
        self.assertTrue(self.calc.process_text("2x%%C12/15 L=185"))
        self.assertEqual(self.calc.results, [])
        self.assertTrue(self.calc.process_dimension(171.0))
        r = self.only_result()
        self.assertEqual(r.piece_count, 24)  # (171/15 → 11, +1) × 2
        self.assertAlmostEqual(r.total_weight, 44.4 * 0.888, places=3)

    def test_letter_c_is_not_a_diameter(self):
        self.assertFalse(self.calc.process_text("C30 beton L=100"))
        self.assertEqual(self.calc.results, [])

    def test_parse_text_returns_diameter_not_length(self):
        self.assertEqual(self.calc.parse_text("%%C12/15 L=185"),
                         {'diameter': 12.0, 'spacing': 15.0, 'length': 185.0})


class StirrupTests(CalculatorTestCase):
    def test_length_and_spacing_in_two_texts(self):
        self.assertTrue(self.calc.process_text("ƒ10 Etr. l= 168"))
        self.assertTrue(self.calc.process_text("Etr.%%C10/8"))
        self.assertTrue(self.calc.process_dimension(291.0))
        r = self.only_result()
        self.assertEqual(r.piece_count, 37)  # 291/8 → 36, +1
        self.assertAlmostEqual(r.total_weight, 62.16 * 0.617, places=3)

    def test_missing_spacing_is_reported_not_crashing(self):
        self.assertTrue(self.calc.process_text("ƒ10 Etr. l= 168"))
        self.assertFalse(self.calc.process_dimension(291.0))
        self.assertEqual(self.calc.results, [])


class MeshTests(CalculatorTestCase):
    def test_wall_mesh_uses_real_unit_weight(self):
        self.assertTrue(self.calc.process_wall_mesh("2xQ257", "215x500"))
        r = self.only_result()
        self.assertAlmostEqual(r.unit_weight, 4.03)
        self.assertAlmostEqual(r.total_weight, 10.75 * 2 * 4.03, places=3)

    def test_slab_mesh(self):
        self.assertTrue(self.calc.process_slab_mesh("Q257/257 450/215"))
        self.assertAlmostEqual(self.only_result().total_weight, 9.675 * 4.03, places=3)

    def test_slab_mesh_with_different_cross_wires(self):
        self.assertTrue(self.calc.process_slab_mesh("Q257/188 500/215"))
        self.assertAlmostEqual(self.only_result().total_weight, 10.75 * 3.49, places=3)

    def test_unknown_mesh_is_rejected(self):
        self.assertFalse(self.calc.process_wall_mesh("Q999", "215x500"))
        self.assertFalse(self.calc.process_slab_mesh("Q999 450/215"))
        self.assertFalse(self.calc.process_slab_mesh("hasır yok"))
        self.assertEqual(self.calc.results, [])

    def test_mesh_table(self):
        self.assertEqual(MeshData.get_weight_per_m2("Q257"), 4.03)
        self.assertEqual(MeshData.get_weight_per_m2("Q257/188"), 3.49)
        self.assertEqual(MeshData.get_weight_per_m2("TR257"), 2.57)
        self.assertEqual(MeshData.get_weight_per_m2("R257"), 2.63)


class ConnectionAndReportTests(CalculatorTestCase):
    def test_connection_rebar(self):
        self.assertTrue(self.calc.process_connection_rebar("2X∅12/15 L=120", dimension=300.0))
        r = self.only_result()
        self.assertEqual(r.piece_count, 42)  # (300/15 + 1) × 2
        self.assertAlmostEqual(r.total_weight, 50.4 * 0.888, places=3)

    def test_old_and_new_field_names(self):
        r = RebarData(count=3, weight_per_meter=0.888)
        self.assertEqual((r.piece_count, r.unit_weight), (3, 0.888))
        self.assertEqual((r.count, r.weight_per_meter), (3, 0.888))

    def test_export_with_all_result_types(self):
        self.calc.process_text("2X13∅20 L=397")
        self.calc.process_text("ƒ10 Etr. l= 168")
        self.calc.process_text("Etr.%%C10/8")
        self.calc.process_dimension(291.0)
        self.calc.process_slab_mesh("Q257/257 450/215")
        self.calc.export_results("demir_metraji")
        with open("demir_metraji.txt", encoding="utf-8") as f:
            report = f.read()
        self.assertIn("GENEL TOPLAM", report)
        total = sum(r.total_weight for r in self.calc.results)
        self.assertIn(f"Toplam Ağırlık: {total:.2f} kg", report)


if __name__ == "__main__":
    unittest.main()
