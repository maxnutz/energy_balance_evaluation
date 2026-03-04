# ESM-validation-framework

![Python](https://img.shields.io/badge/python-3.11-blue)  
![GitHub License](https://img.shields.io/github/license/maxnutz/energy_balance_evaluation)

> [!NOTE]  
> This package is currently in an **early state of development**. Expect ongoing changes and updates.

This repository is licensed under the [MIT License](LICENSE).

## Overview

The **ESM-validation-framework** is a Python package designed to validate energy system model outputs against the Eurostat Energy Balance dataset. It focuses on comparing energy data formatted in the IAMC standard with authoritative Eurostat statistics to ensure consistency and reliability.

This tool is tailored for energy system modeling workflows and supports validation of:

- Primary Energy
- Final Energy
- Final Energy by Carrier
- Final Energy by Sector
- Final Energy by Sector and Carrier
- Secondary Energy (Electricity Generation by Source)
- Trade (Net Imports by Carrier)

---

## Repository Structure

```
energy_balance_evaluation/
├── energy_balance_evaluation/       # Main Python package
│   ├── __init__.py                  # Package exports (VariablesSet)
│   ├── energy_balance_eval.py       # Core module: VariablesSet class + data loading
│   ├── _helpers.py                  # Helper utilities (ODS → CSV conversion)
│   ├── utils.py                     # Utility stubs (future expansion)
│   └── eb_evaluation_to_iamc.ipynb  # Interactive exploration notebook
├── definitions/
│   └── variable/                    # IAMC variable definitions (nomenclature format)
│       ├── energy-consumption.yaml
│       ├── electricity-generation.yaml
│       ├── trade.yaml
│       ├── tag_final_energy_carrier.yaml
│       ├── tag_electricity-generation-source.yaml
│       ├── tag_sector.yaml
│       ├── tag_ets.yaml
│       └── tag_species.yaml
├── validate_data/                   # Generated validation codelists (YAML)
│   └── final_energy_2020.yaml
├── tests/                           # Unit tests (pytest)
│   ├── __init__.py
│   └── test_basics.py
├── resources/                       # Data resources (auto-downloaded if absent)
│   └── estat_nrg_bal_c.tsv          # Eurostat energy balance TSV (not tracked in git)
├── pixi.toml                        # Pixi environment definition
└── pyproject.toml                   # Package metadata
```

---

## Features

- **Validation Against Eurostat Energy Balance**  
  Utilizes the official [Eurostat Energy Balance](https://ec.europa.eu/eurostat/web/energy/database/additional-data#Energy%20balances) as reference data.

- **Automated Data Retrieval**  
  Fetches validation data directly from Eurostat's API via a [direct TSV resource link](https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/nrg_bal_c?format=TSV&compressed=true), ensuring up-to-date and consistent data aligned with the [pypsa-eur workflow](https://github.com/PyPSA/pypsa-eur/pull/1987).

- **IAMC-format Input**  
  Accepts energy system model outputs in the IAMC format for seamless integration.

- **Consistent Variable Definitions**  
  Aligns with variable definitions from the [iiasa/energy-scenarios-at-workflow](https://github.com/iiasa/energy-scenarios-at-workflow/tree/main) project to maintain interoperability.

- **Interactive Notebook**  
  Provides `eb_evaluation_to_iamc.ipynb` for exploratory calculation of IAMC-compatible variable values directly from the Eurostat Energy Balance.

---

## Core Module: `energy_balance_eval.py`

### `VariablesSet`

The primary class for loading variable definitions and computing reference values from the Eurostat Energy Balance.

```python
from energy_balance_evaluation import VariablesSet

vs = VariablesSet(
    set_name="final_energy",
    year=2020,
    filepath_definition="definitions/variable/final_energy.yaml",
    filepath_codelist="validate_data/final_energy.yaml",
    country="AT",
)

# Read IAMC variable definitions from YAML
variables = vs.read_yaml_file()

# Calculate variable values from Eurostat TSV data
values = vs.calculate_variable_values()

# Write a validation codelist YAML (used by nomenclature-based validation)
vs.write_codelist()
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `set_name` | `str` | Descriptive name for this variable set |
| `year` | `int` | Year for which values are computed |
| `filepath_definition` | `str` | Path to the YAML file containing variable definitions with `nrg` and `siec` fields |
| `filepath_codelist` | `str` | Output path for the generated validation codelist (year is appended automatically) |
| `country` | `str` | Eurostat country code to filter data (default: `"AT"` for Austria) |

**Key methods:**

- `read_yaml_file()` — Parses the variable definition YAML into an internal dictionary.
- `calculate_variable_values(filepath_tsv=None)` — Queries the Eurostat TSV for each variable's `nrg_bal` and `siec` codes, sums the matching rows, and returns a dict of `{variable_name: float}`.
- `write_codelist(filepath_tsv=None)` — Calls `calculate_variable_values()` and writes a YAML codelist with tolerance thresholds for use in validation pipelines.

### `fetch_and_load_tsv_data(filepath_tsv=None)`

Loads the Eurostat Energy Balance TSV file from disk. If the file does not exist at the given (or default) path, it is **automatically downloaded** from the Eurostat API and cached locally.

```python
from energy_balance_evaluation.energy_balance_eval import fetch_and_load_tsv_data

df = fetch_and_load_tsv_data()          # uses resources/estat_nrg_bal_c.tsv
df = fetch_and_load_tsv_data("my.tsv")  # custom path
```

Returns a `pd.DataFrame` with columns `freq`, `nrg_bal`, `siec`, `unit`, `geo`, and one column per year.

---

## Variable Definitions

Variable definitions live in `definitions/variable/` and follow the [`nomenclature`](https://nomenclature-iamc.readthedocs.io/en/stable/) package format.  
Each YAML file defines one or more IAMC variables with optional tag-based placeholders:

```yaml
- Final Energy:
    description: Final energy consumption by all end-use sectors and all fuels
    unit: TJ
    EB: FC_E,NRG_E   # Eurostat nrg_bal codes used for reference-value calculation

- Final Energy [by Carrier]|{Final Energy Carrier}:
    description: Energy consumption of {Final Energy Carrier}
    unit: TJ
    EB: FC_E,NRG_E
```

Tag definitions (e.g. `tag_final_energy_carrier.yaml`) enumerate the allowed values for each placeholder dimension such as `{Final Energy Carrier}`, `{Sector}`, or `{Electricity Generation by Source}`.

---

## Jupyter Notebook: `eb_evaluation_to_iamc.ipynb`

The notebook provides an interactive workflow for exploring and computing IAMC variable values from the Eurostat Energy Balance. It is intended for **exploratory analysis** and manual verification.

### Workflow Summary

1. **Import packages** — `pandas`, `pyam`, `nomenclature`
2. **Load variable definitions** — Reads the `definitions/` folder via `nomenclature.DataStructureDefinition` to obtain a structured table of IAMC variable names (`df_n`).
3. **Define mapping dictionaries**:
   - `siec_dict` — Maps IAMC carrier/source names (e.g. `"Natural Gas"`, `"Hydro"`) to Eurostat SIEC codes.
   - `nrg_dict` — Maps IAMC variable-name *templates* (e.g. `"Final Energy"`, `"Secondary Energy|Electricity|{Electricity Generation by Source}"`) to `nrg_bal` codes. A leading `-` on a code means it is **subtracted** (used for net-import calculations).
4. **Load Eurostat Energy Balance** — Uses `fetch_and_load_tsv_data()` to load the TSV file and filters to the country of interest (default: Austria, `"AT"`).
5. **Calculate IAMC values** — A set of helper functions matches each variable name against the template keys in `nrg_dict`, resolves placeholders via `siec_dict`, and aggregates the matching rows across all year columns.
6. **Output** — `calculated_values_df` contains computed values indexed by variable name with one column per year. `df_n_with_values` merges these values back into the full variable-definition table.

### Mapping Logic

Variable names from `df_n` are matched against templates in `nrg_dict` using regex-based placeholder expansion. For example:

- `"Final Energy [by Carrier]|Natural Gas"` matches the template `"Final Energy [by Carrier]|{Final Energy Carrier}"`.  
  The placeholder value `"Natural Gas"` is looked up in `siec_dict` → `["G3000"]`, and only rows with `siec == "G3000"` are summed.

- `"Net Imports|Electricity"` matches `"Net Imports|{Final Energy Carrier}"`.  
  The `nrg_dict` entry `["IMP", "-EXP"]` means imports are **added** and exports are **subtracted**.

- Variables whose placeholder value has an empty `siec_dict` entry (e.g. `"E-Fuels"`, `"Hydrogen"`) or whose template is absent from `nrg_dict` yield `NaN`.

---

## Generated Validation Codelists

`validate_data/final_energy_2020.yaml` is an example output of `VariablesSet.write_codelist()`. It lists each IAMC variable with its computed reference value and tolerance thresholds:

```yaml
- variable: Final Energy
  year: 2020
  value: 279335.902
  validation:
    - rtol: 0.3
    - warning_level: low
      rtol: 0.1
```

These files are consumed by `nomenclature`-based validation workflows to check whether model outputs fall within acceptable bounds of the Eurostat reference values.

---

## Installation

Currently, the package is intended to be used within the **pixi environment**.  
Further installation instructions and package distribution details will be provided soon.

```bash
pixi install   # sets up the full environment from pixi.toml
```

---

## Running Tests

```bash
pixi run pytest tests/
```

---

## Getting Started

1. Set up and activate the pixi environment (`pixi install`).
2. Prepare your energy system model output in IAMC-format.
3. Run the notebook `energy_balance_evaluation/eb_evaluation_to_iamc.ipynb` to explore variable mappings.
4. Use `VariablesSet.write_codelist()` to generate reference YAML codelists.
5. Use the framework to validate your model outputs against the generated codelists.

---

## References

- [Eurostat Energy Balance Database](https://ec.europa.eu/eurostat/web/energy/database/additional-data#Energy%20balances)
- [Eurostat API Resource](https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/nrg_bal_c?format=TSV&compressed=true)
- [pypsa-eur Pull Request for Workflow Consistency](https://github.com/PyPSA/pypsa-eur/pull/1987)
- [iiasa/energy-scenarios-at-workflow Variable Definitions](https://github.com/iiasa/energy-scenarios-at-workflow/tree/main)
- [nomenclature package](https://nomenclature-iamc.readthedocs.io/en/stable/)
- [pyam package](https://pyam-iamc.readthedocs.io/en/stable/)

---
