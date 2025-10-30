#!/usr/bin/env python3

import pandas as pd
import numpy as np

from .utils import EnergyBalanceAT


class EnergyBalance(EnergyBalanceAT):
    def __init__(
        self,
        year,
        path_to_xlsb="EnergyBalances/BalancesApril2025/AT-Energy-balance-sheets-April2025-edition.xlsb",
        country="AT",
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
        - category: one of the top layer cathegories (string)
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
