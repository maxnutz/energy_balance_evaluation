#!/usr/bin/env python3

import pandas as pd
import numpy as np

from .utils import EnergyBalanceAT


class EnergyBalance(EnergyBalanceAT):
    """
    Class for evaluating the energy balance data

    Contains methods for selecting data based on hierarchical depth and search strings.

    Attributes:
    ----------
    - year: year of the energy balance data to evaluate (int)
    - path_to_xlsb: path to the Excel file containing the energy balance data (str)
    - country: country of the energy balance data (str)
    - input_matrix: input DataFrame containing the energy balance data (pandas.DataFrame | None)
    - original_input: flag indicating whether to use the original input DataFrame or a modified version (bool)

    Methods:
    -------
    - get_top_layer_entries: get all top layer entries with number values
    - get_entries_of_category: get all entries of a given category

    """

    def __init__(
        self,
        year: str,
        path_to_xlsb: str = "EnergyBalances/BalancesApril2025/AT-Energy-balance-sheets-April2025-edition.xlsb",
        country: str = "AT",
        input_matrix: pd.DataFrame | None = None,
        original_input: bool = True,
    ):
        super().__init__(year, path_to_xlsb, country, input_matrix, original_input)

    def get_top_layer_entries(self, only_total_values: bool = False) -> pd.DataFrame:
        """
        Get all top layer entries with number values.
        Inputs:
        - only_total_values: only return column TOTAL
        Outputs:
        - pandas.DataFrame
        """
        df = self.select(
            depth=0,
            only_return_index=False,
        )[:-1]
        if only_total_values:
            return df[["TOTAL"]]
        return df

    def get_entries_of_category(
        self,
        category: str,
        only_total_values: bool = False,
        drop_multilayer: bool = False,
    ) -> pd.DataFrame:
        """
        Get all entries of a given category.
        ---
        Inputs:
        - category: one of the top layer categories (string)
        - only_total_values: only return column TOTAL (bool)
        - drop_multilayer: drop multi-layer structure and return flat DataFrame (bool)
        ---
        Outputs:
        - pandas.DataFrame
        """
        df = self.select(
            search_string=category,
            depth=1,
            only_return_index=False,
        )[:-1]
        if drop_multilayer:
            df = self.select(
                search_string=category,
                depth=1,
                only_return_index=False,
                drop_multilayer=True,
            )[:-1]
        if only_total_values:
            return df[["TOTAL"]]
        return df


def main():
    print("This is a unit test of data_selection")

    pass


if __name__ == "__main__":
    main()
