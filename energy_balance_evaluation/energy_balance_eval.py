#!/usr/bin/env python3

import pandas as pd
import numpy as np
from pathlib import Path

from energy_balance_evaluation.utils import EnergyBalanceReader, read_mapping_csv, extract_true_keys
from energy_balance_evaluation.statics import (
    non_numerical_columns_list,
    rows_to_add_dict,
    rows_to_include_dict,
)

# Re-export VariablesSet from its dedicated module for backward compatibility.
from energy_balance_evaluation.variable_structures import VariablesSet  # noqa: F401


class EnergyBalance(EnergyBalanceReader):
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
        filepath_mapping_csv: str = "resources/carrier_mapping_energy_balance.csv",
        country: str = "AT",
        input_matrix: pd.DataFrame | None = None,
        original_input: bool = True,
    ):
        super().__init__(year, path_to_xlsb, country, input_matrix, original_input)
        self.filepath_mapping_csv = filepath_mapping_csv

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

    def reduce_energy_balance_by_rows(self) -> pd.DataFrame:
        """
        Reduce the energy balance to a flat subset of rows.

        Selects rows whose ``var_name`` appears in :data:`rows_to_include_dict`
        (via :func:`extract_true_keys`), then aggregates additional rows
        defined in :data:`rows_to_add_dict` by summing their source rows.
        Source rows consumed by an aggregation are removed from the result.

        Returns
        -------
        pd.DataFrame
            Reduced energy balance with a ``(layer_0, layer_1, layer_2)``
            MultiIndex, sorted by those layers.
        """
        # --- 1. Filter to the rows we want to keep -----------------------
        var_names_to_include = set(extract_true_keys(rows_to_include_dict))
        df_light = (
            self.df_eb[self.df_eb["var_name"].isin(var_names_to_include)]
            .copy()
            .set_index("var_name", drop=False)
        )

        # --- 2. Split numeric vs. metadata columns -----------------------
        num_cols = df_light.columns.difference(non_numerical_columns_list)
        meta_cols = df_light.columns.intersection(non_numerical_columns_list)
        df_num = df_light[num_cols]
        df_meta = df_light[meta_cols]

        # --- 3. Build aggregated rows and collect rows to drop -----------
        rows_to_drop: list[str] = []
        agg_rows: list[pd.Series] = []
        agg_layer_specs: dict[str, dict[str, str]] = {
            key: {f"layer_{i}": part for i, part in enumerate(key.split(">"))}
            for key in rows_to_add_dict
        }

        for agg_key, source_vals in rows_to_add_dict.items():
            sources = [source_vals] if isinstance(source_vals, str) else list(source_vals)

            # Exact match first; fall back to stripped comparison
            available = set(df_num.index)
            matched = [s for s in sources if s in available]
            if not matched:
                stripped_map = {
                    s.strip() if isinstance(s, str) else s: s for s in available
                }
                matched = [
                    stripped_map[s.strip()]
                    for s in sources
                    if s.strip() in stripped_map
                ]

            if not matched:
                raise KeyError(
                    f"rows_to_add_dict entry '{agg_key}' references missing rows "
                    f"{sources!r}. Available (first 20): {sorted(available)[:20]!r}"
                )

            agg_series = df_num.loc[matched].sum(axis=0)
            agg_series.name = agg_key
            agg_rows.append(agg_series)
            rows_to_drop.extend(matched)

        # --- 4. Drop consumed source rows and append aggregated ones -----
        df_num = df_num.drop(index=[r for r in rows_to_drop if r in df_num.index])
        df_meta = df_meta.drop(index=[r for r in rows_to_drop if r in df_meta.index])

        if agg_rows:
            df_num = pd.concat([df_num, pd.DataFrame(agg_rows)])

        # --- 5. Rebuild metadata for aggregated rows ---------------------
        agg_meta_rows = []
        for agg_key, layer_dict in agg_layer_specs.items():
            row: dict[str, object] = {col: np.nan for col in meta_cols}
            row.update(layer_dict)
            row["var_name"] = agg_key
            agg_meta_rows.append(pd.Series(row, name=agg_key))

        if agg_meta_rows:
            df_meta = pd.concat([df_meta, pd.DataFrame(agg_meta_rows)])

        # --- 6. Recombine, sort, and set MultiIndex ----------------------
        df_result = pd.concat([df_num, df_meta], axis=1, join="outer")
        df_result["var_name"] = df_result.index
        df_result = df_result.sort_values(["layer_0", "layer_1", "layer_2"])
        df_result = df_result.set_index(["layer_0", "layer_1", "layer_2"], drop=False)
        return df_result

    def reduce_energy_balance_by_columns(
        self, df: pd.DataFrame, mapping_eb_pypsa: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Reduce the energy balance dataframe by summing up columns
        according to a given mapping between eb_index and pypsa-entry.

        Parameters
        ----------
        df : pd.DataFrame
            The energy balance dataframe to be reduced.
        mapping_eb_pypsa : pd.DataFrame
            A dataframe containing the mapping between eb_index
            and pypsa-entry.

        Returns
        -------
        pd.DataFrame
            A reduced energy balance dataframe containing the summed up columns.
        """
        # create mapping between eb_index and pypsa-entry and create sum of respective columns
        mapping_eb_pypsa_sum = mapping_eb_pypsa.copy().set_index(
            "pypsa-entry", drop=True
        )
        mapping_eb_pypsa_dict = (
            mapping_eb_pypsa_sum.groupby(mapping_eb_pypsa_sum.index)
            .agg(list)["eb_index"]
            .to_dict()
        )
        for pypsa_key, eb_list in mapping_eb_pypsa_dict.items():
            df[pypsa_key] = df[eb_list].sum(axis=1)
        df_red_pypsa_columns = df.loc[
            :,
            df.columns.isin(
                non_numerical_columns_list + list(mapping_eb_pypsa_dict.keys())
            ),
        ]
        return df_red_pypsa_columns

    def create_reduced_energy_balance(self) -> pd.DataFrame:
        """
        Creates a reduced version of the eurostat energy balance from the
        given file path and the mapping between eb_index and pypsa-entry.

        Parameters
        ----------
        self : object
            The object containing the file paths and the mapping.

        Inputfiles:
        -----------
        resources/carrier_mapping_energy_balance.csv: holding the mapping of
            pypsa-carriers with the energy balance carriers

        Returns
        -------
        pd.DataFrame
            A reduced energy balance dataframe containing the summed up columns.
        """
        # index_to_nicenames = eb.df_eb.iloc[0, :].to_dict()
        # pe_carrier_nicenames_to_index = {
        #     val: key for key, val in index_to_nicenames.items()
        # }
        mapping_eb_pypsa = read_mapping_csv(self.filepath_mapping_csv)
        df_light_rows = self.reduce_energy_balance_by_rows()
        df_light = self.reduce_energy_balance_by_columns(
            df=df_light_rows, mapping_eb_pypsa=mapping_eb_pypsa
        )
        return df_light

    def populate_dict_from_eb_input(self) -> None:
        """
        Reads from the reduced version of the eurostat energy balance to
        populate the dict eval_dict for the respective primary energy carrier.
        """
        pass


def main():
    print("This is a unit test of the energy_balance_eval")

    # eb = EnergyBalance(
    #     year=2023,
    #     path_to_xlsb="resources/EnergyBalances/BalancesFebruary2026/AT-Energy-balance-sheets-February2026-edition.xlsb",
    #     filepath_mapping_csv="resources/carrier_mapping_energy_balance.csv",
    #     country="AT",
    #     original_input=True,
    # )
    # eb.create_reduced_energy_balance()

    final_energy = VariablesSet(
        set_name="final_energy",
        year=2020,
        filepath_definition="definitions/variable/final_energy.yaml",
        filepath_codelist="definitions/validation/final_energy.yaml",
        country="AT",
    )

    final_energy.write_codelist()


if __name__ == "__main__":
    main()
