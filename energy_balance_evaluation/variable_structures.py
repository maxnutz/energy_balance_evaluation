#!/usr/bin/env python3
"""
Variable structure definitions and validation for energy balance evaluation.

This module provides the :class:`VariablesSet` class for reading variable
definitions from YAML, querying Eurostat TSV data, and writing output
codelists used by the nomenclature-based validation workflow.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import yaml


# Required metadata fields that every variable definition must contain.
REQUIRED_VARIABLE_FIELDS: tuple[str, ...] = ("nrg", "siec")


class VariablesSet:
    """
    Read, validate, and write variable codelists from IAMC-style YAML definitions.

    Each YAML definition file contains a list of variable entries.  Every
    entry maps a single variable name to its metadata::

        - Final Energy:
            description: total final energy consumption
            unit: GWh
            nrg: FC_E
            siec: TOTAL

    The class queries a Eurostat TSV file (``estat_nrg_bal_c.tsv``) to
    compute reference values and writes a validation codelist YAML that can
    be consumed by the *nomenclature* package.

    Parameters
    ----------
    set_name : str
        Name of the variable set (e.g. ``'final_energy'``).
    year : int
        Reference year for which to calculate values.
    filepath_definition : str
        Path to the YAML file containing variable definitions.
    filepath_codelist : str
        Path where the output codelist YAML file will be written.
    country : str, optional
        ISO country code used to filter the TSV data (default: ``'AT'``).

    Attributes
    ----------
    variables_dict : dict or None
        Parsed variable definitions (populated by :meth:`read_yaml_file`).
    tsv_data : pandas.DataFrame or None
        Cached TSV data (populated on first call to
        :meth:`calculate_variable_values`).
    """

    def __init__(
        self,
        set_name: str,
        year: int,
        filepath_definition: str,
        filepath_codelist: str,
        country: str = "AT",
    ) -> None:
        self.name = set_name
        self.year = year
        self.filepath_definition = filepath_definition
        self.filepath_codelist = filepath_codelist
        self.country = country
        self.variables_dict: dict | None = None
        self.tsv_data: pd.DataFrame | None = None

    # ------------------------------------------------------------------
    # YAML I/O
    # ------------------------------------------------------------------

    def read_yaml_file(self) -> dict:
        """
        Read and parse variable definitions from the YAML definition file.

        Returns
        -------
        dict
            Mapping ``{variable_name: metadata_dict}``.  Example::

                {
                    'Final Energy': {
                        'description': '...',
                        'unit': 'GWh',
                        'nrg': 'FC_E',
                        'siec': 'TOTAL',
                    },
                    ...
                }

        Raises
        ------
        FileNotFoundError
            If the YAML definition file does not exist.
        yaml.YAMLError
            If the YAML file cannot be parsed.
        ValueError
            If the top-level YAML structure is not a list, or if any
            list item is not a dict.
        """
        try:
            with open(self.filepath_definition, "r") as f:
                variables_list = yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Variable definition file not found: {self.filepath_definition}"
            )
        except yaml.YAMLError as e:
            raise yaml.YAMLError(
                f"Failed to parse YAML file {self.filepath_definition}: {str(e)}"
            ) from e

        if not isinstance(variables_list, list):
            raise ValueError(
                f"Expected YAML file to contain a list, got {type(variables_list).__name__}"
            )

        self.variables_dict = {}
        for item in variables_list:
            if not isinstance(item, dict):
                raise ValueError(
                    f"Expected each YAML list item to be a dict, got {type(item).__name__}"
                )
            for var_name, var_metadata in item.items():
                self.variables_dict[var_name] = var_metadata

        return self.variables_dict

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate_variable_structure(self) -> dict[str, list[str]]:
        """
        Validate that every variable definition contains the required fields.

        Checks each variable in :attr:`variables_dict` against
        :data:`REQUIRED_VARIABLE_FIELDS`.  Reads the YAML first if
        :attr:`variables_dict` is ``None``.

        Returns
        -------
        dict[str, list[str]]
            A mapping ``{variable_name: [missing_field, ...]}``.  The dict
            is empty when all definitions are valid.

        Raises
        ------
        ValueError
            If :attr:`variables_dict` is ``None`` after attempting to load
            the definition file (i.e. the file is empty).

        Examples
        --------
        >>> vs = VariablesSet("fe", 2020, "definitions/variable/final_energy.yaml",
        ...                   "definitions/validation/final_energy.yaml")
        >>> issues = vs.validate_variable_structure()
        >>> if issues:
        ...     for var, missing in issues.items():
        ...         print(f"{var}: missing {missing}")
        """
        if self.variables_dict is None:
            self.read_yaml_file()

        if self.variables_dict is None:
            raise ValueError(
                "variables_dict is None after reading the definition file. "
                "The file may be empty."
            )

        validation_issues: dict[str, list[str]] = {}
        for var_name, metadata in self.variables_dict.items():
            if not isinstance(metadata, dict):
                validation_issues[var_name] = list(REQUIRED_VARIABLE_FIELDS)
                continue
            missing = [
                field
                for field in REQUIRED_VARIABLE_FIELDS
                if metadata.get(field) is None
            ]
            if missing:
                validation_issues[var_name] = missing

        return validation_issues

    # ------------------------------------------------------------------
    # TSV helpers
    # ------------------------------------------------------------------

    def _parse_codes(self, code_string: str) -> list[str]:
        """
        Parse a code string into a list of individual Eurostat codes.

        Handles:

        - Single codes: ``'FC_E'`` → ``['FC_E']``
        - Multiple comma-separated codes: ``'FC_OTH_HH_E,FC_OTH_CP_E'``
          → ``['FC_OTH_HH_E', 'FC_OTH_CP_E']``
        - Inline comments: ``'FC_E  # comment'`` → ``['FC_E']``

        Parameters
        ----------
        code_string : str
            Code string with optional comma separation and comments.

        Returns
        -------
        list[str]
            List of individual codes (stripped and comment-free).
        """
        if "#" in code_string:
            code_string = code_string.split("#")[0]
        codes = [code.strip() for code in code_string.split(",")]
        return [code for code in codes if code]

    def _load_tsv_data(self, filepath_tsv: str) -> pd.DataFrame:
        """
        Load and parse a Eurostat energy-balance TSV file.

        Handles both the standard tab-separated format and the combined
        ``freq,nrg_bal,siec,unit,geo\\TIME_PERIOD`` header used by
        *pypsa-eur* downloads.  The returned DataFrame always has a ``geo``
        column and numeric year columns (``':'`` is mapped to ``NaN``).

        Parameters
        ----------
        filepath_tsv : str
            Path to the TSV file.

        Returns
        -------
        pandas.DataFrame
            DataFrame with columns: ``freq``, ``nrg_bal``, ``siec``,
            ``unit``, ``geo``, and one column per year.
        """
        df = pd.read_csv(filepath_tsv, sep=",|\t", dtype=str, engine="python")

        first_col = df.columns[0]
        if "freq" in first_col and "nrg_bal" in first_col:
            df = pd.read_csv(filepath_tsv, sep="\t", dtype=str, skiprows=1)

        df.columns = [col.strip() for col in df.columns]

        if "geo\\TIME_PERIOD" in df.columns and "geo" not in df.columns:
            df.rename(columns={"geo\\TIME_PERIOD": "geo"}, inplace=True)

        year_columns = list(df.columns)[5:]
        for year_col in year_columns:
            if year_col in df.columns:
                df[year_col] = pd.to_numeric(
                    df[year_col].replace(":", np.nan), errors="coerce"
                )

        return df

    # ------------------------------------------------------------------
    # Value calculation
    # ------------------------------------------------------------------

    def calculate_variable_values(self, filepath_tsv: str) -> dict[str, float]:
        """
        Calculate reference values for each variable by querying the TSV file.

        For each variable definition the method filters the TSV for rows
        matching the ``nrg`` and ``siec`` codes for :attr:`country` and
        :attr:`year`, then sums the matching values.

        Parameters
        ----------
        filepath_tsv : str
            Path to the Eurostat ``estat_nrg_bal_c.tsv`` file.

        Returns
        -------
        dict[str, float]
            Mapping ``{variable_name: value}``.  Missing year columns
            produce ``nan``; an empty country filter produces ``0.0``.

        Raises
        ------
        KeyError
            If the loaded TSV data does not contain a ``'geo'`` column
            after normalisation.
        """
        if self.variables_dict is None:
            self.read_yaml_file()

        if self.tsv_data is None:
            self.tsv_data = self._load_tsv_data(filepath_tsv)

        df = self.tsv_data.copy()

        if "geo" not in df.columns:
            raise KeyError(
                "TSV data did not contain a 'geo' column after loading. "
                f"Available columns: {list(df.columns)[:10]}"
            )

        df = df[df["geo"] == self.country]

        calculated_values: dict[str, float] = {}
        for var_name, var_metadata in self.variables_dict.items():
            nrg = var_metadata.get("nrg", "") if isinstance(var_metadata, dict) else ""
            siec = var_metadata.get("siec", "") if isinstance(var_metadata, dict) else ""

            nrg_codes = self._parse_codes(nrg)
            siec_codes = self._parse_codes(siec)

            df_filtered = df[
                df["nrg_bal"].isin(nrg_codes) & df["siec"].isin(siec_codes)
            ]

            year_col = str(self.year)
            if year_col in df_filtered.columns:
                values = df_filtered[year_col].sum(skipna=True)
                calculated_values[var_name] = float(values) if values != 0 else 0.0
            else:
                calculated_values[var_name] = np.nan

        return calculated_values

    # ------------------------------------------------------------------
    # Output
    # ------------------------------------------------------------------

    def write_codelist(self, filepath_tsv: str | None = None) -> None:
        """
        Calculate variable values and write a validation codelist YAML.

        The output file has the structure::

            - variable: <variable_name>
              year: <year>
              value: <calculated_value>
              validation:
                - rtol: 0.3
                - warning_level: low
                  rtol: 0.1

        Parameters
        ----------
        filepath_tsv : str or None, optional
            Path to the Eurostat TSV file.  When ``None`` the method tries
            to find ``resources/estat_nrg_bal_c.tsv`` relative to the
            current working directory.

        Raises
        ------
        FileNotFoundError
            If ``filepath_tsv`` is ``None`` and the inferred default path
            does not exist.
        """
        if self.variables_dict is None:
            self.read_yaml_file()

        if filepath_tsv is not None:
            calculated_values = self.calculate_variable_values(filepath_tsv)
        else:
            inferred_tsv = Path("resources/estat_nrg_bal_c.tsv")
            if inferred_tsv.exists():
                calculated_values = self.calculate_variable_values(str(inferred_tsv))
            else:
                raise FileNotFoundError(
                    "filepath_tsv not provided and could not infer from "
                    "resources in project's main directory."
                )

        codelist = []
        for var_name, var_metadata in self.variables_dict.items():
            value = calculated_values.get(var_name, 0.0)
            entry = {
                "variable": var_name,
                "year": self.year,
                "value": round(value, 3),
                "validation": [{"rtol": 0.3}, {"warning_level": "low", "rtol": 0.1}],
            }
            codelist.append(entry)

        output_path = Path(self.filepath_codelist)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            yaml.dump(
                codelist,
                f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
            )
