"""
Tests for package imports and module structure.
"""

import unittest


class TestPackageImports(unittest.TestCase):
    """Test that all public symbols are importable."""

    def test_import_carrier_network(self):
        from energy_balance_evaluation import CarrierNetwork

        self.assertIsNotNone(CarrierNetwork)

    def test_import_carriers_network(self):
        from energy_balance_evaluation import CarriersNetwork

        self.assertIsNotNone(CarriersNetwork)

    def test_import_eval_all_networks(self):
        from energy_balance_evaluation import eval_all_networks

        self.assertIsNotNone(eval_all_networks)

    def test_import_get_components_of_carrier(self):
        from energy_balance_evaluation import get_components_of_carrier

        self.assertIsNotNone(get_components_of_carrier)
    def test_import_input_error(self):
        from energy_balance_evaluation import InputError

        self.assertIsNotNone(InputError)

    def test_all_exports(self):
        import energy_balance_evaluation as pkg

        for name in ["CarrierNetwork", "CarriersNetwork", "InputError", "eval_all_networks"]:
            self.assertTrue(hasattr(pkg, name), f"Missing export: {name}")


if __name__ == "__main__":
    unittest.main()
