"""
This package contains a set of tools for
- evaluating flat energy balance
- creating structured variable definitions and codelists for
  Energy System Model Validation
- validate ESM model outputs  in IAMC-format vs Eurostat Energy Balance values

"""

# from energy_balance_evaluation.energy_balance_eval import EnergyBalance
from energy_balance_evaluation.energy_balance_eval import VariablesSet

__all__ = [
    "VariablesSet",
]
