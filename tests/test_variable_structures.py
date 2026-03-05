"""
Tests for the variable_structures module (VariablesSet and validate_variable_structure).
"""

import os
import tempfile
import unittest
from pathlib import Path

import yaml


class TestVariableStructuresModule(unittest.TestCase):
    """Tests that verify the variable_structures module can be imported directly."""

    def test_import_from_module(self):
        """VariablesSet is importable from energy_balance_evaluation.variable_structures."""
        from energy_balance_evaluation.variable_structures import VariablesSet

        self.assertIsNotNone(VariablesSet)

    def test_import_from_package(self):
        """VariablesSet is importable from the top-level package."""
        from energy_balance_evaluation import VariablesSet

        self.assertIsNotNone(VariablesSet)

    def test_import_energy_balance_from_package(self):
        """EnergyBalance is importable from the top-level package."""
        from energy_balance_evaluation import EnergyBalance

        self.assertIsNotNone(EnergyBalance)

    def test_variables_set_in_all(self):
        """VariablesSet is listed in package __all__."""
        import energy_balance_evaluation

        self.assertIn("VariablesSet", energy_balance_evaluation.__all__)

    def test_energy_balance_in_all(self):
        """EnergyBalance is listed in package __all__."""
        import energy_balance_evaluation

        self.assertIn("EnergyBalance", energy_balance_evaluation.__all__)

    def test_backward_compat_import_from_eval(self):
        """VariablesSet is still importable from energy_balance_eval for backward compatibility."""
        from energy_balance_evaluation.energy_balance_eval import VariablesSet

        self.assertIsNotNone(VariablesSet)

    def test_required_variable_fields_constant(self):
        """REQUIRED_VARIABLE_FIELDS is exported and is a tuple of strings."""
        from energy_balance_evaluation.variable_structures import REQUIRED_VARIABLE_FIELDS

        self.assertIsInstance(REQUIRED_VARIABLE_FIELDS, tuple)
        self.assertGreater(len(REQUIRED_VARIABLE_FIELDS), 0)
        for field in REQUIRED_VARIABLE_FIELDS:
            self.assertIsInstance(field, str)


class TestValidateVariableStructure(unittest.TestCase):
    """Tests for VariablesSet.validate_variable_structure()."""

    def setUp(self):
        from energy_balance_evaluation.variable_structures import VariablesSet

        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.VariablesSet = VariablesSet

    def tearDown(self):
        self.temp_dir.cleanup()

    def _make_vs(self, yaml_content: list) -> object:
        """Helper: write *yaml_content* to a temp file and return a VariablesSet."""
        definition_path = self.temp_path / "vars.yaml"
        with open(definition_path, "w") as f:
            yaml.safe_dump(yaml_content, f)
        codelist_path = self.temp_path / "codelist.yaml"
        return self.VariablesSet(
            set_name="test",
            year=2023,
            filepath_definition=str(definition_path),
            filepath_codelist=str(codelist_path),
        )

    # --- happy-path -------------------------------------------------------

    def test_no_issues_for_valid_definitions(self):
        """Returns an empty dict when all variables have required fields."""
        content = [
            {"Final Energy": {"nrg": "FC_E", "siec": "TOTAL", "unit": "GWh"}},
            {"Final Energy|Electricity": {"nrg": "FC_E", "siec": "E7000", "unit": "GWh"}},
        ]
        vs = self._make_vs(content)
        issues = vs.validate_variable_structure()
        self.assertIsInstance(issues, dict)
        self.assertEqual(len(issues), 0)

    def test_reads_yaml_automatically_if_not_loaded(self):
        """validate_variable_structure loads the YAML when variables_dict is None."""
        content = [
            {"Final Energy": {"nrg": "FC_E", "siec": "TOTAL"}},
        ]
        vs = self._make_vs(content)
        self.assertIsNone(vs.variables_dict)
        issues = vs.validate_variable_structure()
        self.assertIsNotNone(vs.variables_dict)
        self.assertIsInstance(issues, dict)

    # --- missing-field detection ------------------------------------------

    def test_detects_missing_nrg(self):
        """Reports missing 'nrg' field."""
        content = [
            {"Bad Variable": {"siec": "TOTAL", "unit": "GWh"}},
        ]
        vs = self._make_vs(content)
        issues = vs.validate_variable_structure()
        self.assertIn("Bad Variable", issues)
        self.assertIn("nrg", issues["Bad Variable"])

    def test_detects_missing_siec(self):
        """Reports missing 'siec' field."""
        content = [
            {"Bad Variable": {"nrg": "FC_E", "unit": "GWh"}},
        ]
        vs = self._make_vs(content)
        issues = vs.validate_variable_structure()
        self.assertIn("Bad Variable", issues)
        self.assertIn("siec", issues["Bad Variable"])

    def test_detects_multiple_missing_fields(self):
        """Reports all missing required fields for a single variable."""
        content = [
            {"Incomplete Variable": {"unit": "GWh", "description": "test"}},
        ]
        vs = self._make_vs(content)
        issues = vs.validate_variable_structure()
        self.assertIn("Incomplete Variable", issues)
        missing = issues["Incomplete Variable"]
        self.assertIn("nrg", missing)
        self.assertIn("siec", missing)

    def test_detects_none_field_value(self):
        """A field set to None is treated as missing."""
        content = [
            {"Null Variable": {"nrg": None, "siec": "TOTAL"}},
        ]
        vs = self._make_vs(content)
        issues = vs.validate_variable_structure()
        self.assertIn("Null Variable", issues)
        self.assertIn("nrg", issues["Null Variable"])

    def test_mixed_valid_and_invalid(self):
        """Only variables with missing fields appear in the result."""
        content = [
            {"Good Variable": {"nrg": "FC_E", "siec": "TOTAL"}},
            {"Bad Variable": {"unit": "GWh"}},
        ]
        vs = self._make_vs(content)
        issues = vs.validate_variable_structure()
        self.assertNotIn("Good Variable", issues)
        self.assertIn("Bad Variable", issues)

    def test_non_dict_metadata_reported(self):
        """A variable whose metadata is not a dict is reported."""
        content = [
            {"String Meta": "this is a string, not a dict"},
        ]
        # yaml.safe_dump does not preserve the structure above as expected
        # so write the YAML manually to keep the non-dict metadata.
        definition_path = self.temp_path / "bad.yaml"
        with open(definition_path, "w") as f:
            f.write("- String Meta: this is a string, not a dict\n")
        codelist_path = self.temp_path / "codelist2.yaml"
        vs = self.VariablesSet(
            set_name="test",
            year=2023,
            filepath_definition=str(definition_path),
            filepath_codelist=str(codelist_path),
        )
        from energy_balance_evaluation.variable_structures import REQUIRED_VARIABLE_FIELDS

        issues = vs.validate_variable_structure()
        self.assertIn("String Meta", issues)
        self.assertEqual(issues["String Meta"], list(REQUIRED_VARIABLE_FIELDS))


if __name__ == "__main__":
    unittest.main()
