# ESM-validation-framework

![Python](https://img.shields.io/badge/python-3.11-blue)  
[![license](https://img.shields.io/badge/License-MIT-blue)](https://github.com/maxnutz/energy_balance_evaluation/blob/master/LICENSE)

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

---

## Features

- **Validation Against Eurostat Energy Balance**  
  Utilizes the official [Eurostat Energy Balance](https://ec.europa.eu/eurostat/web/energy/database/additional-data#Energy%20balances) as reference data.

- **Automated Data Retrieval**  
  Fetches validation data directly from Eurostat’s API via a [direct TSV resource link](https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/nrg_bal_c?format=TSV&compressed=true), ensuring up-to-date and consistent data aligned with the [pypsa-eur workflow](https://github.com/PyPSA/pypsa-eur/pull/1987).

- **IAMC-format Input**  
  Accepts energy system model outputs in the IAMC format for seamless integration.

- **Consistent Variable Definitions**  
  Aligns with variable definitions from the [iiasa/energy-scenarios-at-workflow](https://github.com/iiasa/energy-scenarios-at-workflow/tree/main) project to maintain interoperability.

---

## Installation

Currently, the package is intended to be used within the **pixi environment**.  
Further installation instructions and package distribution details will be provided soon.

---

## Getting Started

- Set up and activate the pixi environment.  
- Prepare your energy system model output in IAMC-format.  
- Use the framework to validate your model outputs against Eurostat Energy Balance data.

_More detailed usage instructions and examples will be added in future updates._

---

## References

- [Eurostat Energy Balance Database](https://ec.europa.eu/eurostat/web/energy/database/additional-data#Energy%20balances)  
- [Eurostat API Resource](https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/nrg_bal_c?format=TSV&compressed=true)  
- [pypsa-eur Pull Request for Workflow Consistency](https://github.com/PyPSA/pypsa-eur/pull/1987)  
- [iiasa/energy-scenarios-at-workflow Variable Definitions](https://github.com/iiasa/energy-scenarios-at-workflow/tree/main)  

---
