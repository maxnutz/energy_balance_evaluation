#!/usr/bin/env python3

import pandas as pd
import numpy as np


class EnergyBalanceAT:
    """
    AT energy balance reader and mapper

    Inputs:
    - year: sheet name (str)
    - path_to_xlsb: path to .xlsb file (str), optional

    Outputs / attributes:
    - df_eb: cleaned energy balance DataFrame (pandas.DataFrame)
    - df_variables: variable mapping DataFrame (pandas.DataFrame)
    - sheet_name: provided sheet name (str)
    - path_to_xlsb: provided file path (str)

    Methods:
    - import_excel: import and initial cleaning
    - create_multiindex_structure: build multi-index and depth column
    - map_variable_names: derive variable names and mappings
    """

    def __init__(
        self,
        year,
        path_to_xlsb="EnergyBalances/BalancesApril2025/AT-Energy-balance-sheets-April2025-edition.xlsb",
        country="AT",
        input_matrix: pd.DataFrame | None = None,
        original_input: bool = True,
    ):
        self.original_input = original_input
        if input_matrix is not None:
            self.df_eb = input_matrix
            self.create_multiindex_structure()
            self.map_variable_names()
        else:
            self.sheet_name = year
            self.path_to_xlsb = path_to_xlsb
            self.country = country
            self.df_eb = self.import_excel()
            self.create_multiindex_structure()
            self.map_variable_names()

    def import_excel(self) -> pd.DataFrame:
        """Imports the energy balance excel sheet and does some initial cleaning."""
        df_eb = pd.read_excel(
            self.path_to_xlsb,
            sheet_name=self.sheet_name,
            skiprows=3,
        )
        df_eb.rename(
            columns={
                "Unnamed: 0": "layer_0",
                "Unnamed: 1": "layer_1",
                "Unnamed: 2": "layer_2",
                "Unnamed: 7": "index",
            },
            inplace=True,
        )
        df_eb.drop(
            columns=["Unnamed: 3", "Unnamed: 4", "Unnamed: 5", "Unnamed: 6"],
            inplace=True,
        )
        df_eb.loc[0, "index"] = "energycarrier"
        df_eb.loc[1, "layer_0"] = "Total absolute values"
        if self.original_input:
            df_eb.dropna(axis="columns", how="all", inplace=True)
        return df_eb

    def create_multiindex_structure(self) -> None:
        """Build a multi-index from layer columns and compute row depth.

        Scans layer_0/1/2 for +/- markers, records them in a '+/-' column,
        replaces marker values with NaN, forward-fills hierarchical labels,
        sets a MultiIndex (layer_0, layer_1, layer_2) and adds a 'depth' column
        indicating the hierarchy level (0..n). Updates self.df_eb in-place.
        """
        try:
            df = self.df_eb.copy()
            df["+/-"] = None
            df["+/-"].astype("str")

            for index, row in df.iterrows():
                if (
                    row["layer_0"] == "+"
                    or row["layer_0"] == "-"
                    or row["layer_0"] == "="
                ):
                    df.at[index, "+/-"] = df.at[index, "layer_0"]
                if (
                    row["layer_1"] == "+"
                    or row["layer_1"] == "-"
                    or row["layer_1"] == "="
                ):
                    df.at[index, "+/-"] = df.at[index, "layer_1"]
                if (
                    row["layer_2"] == "+"
                    or row["layer_2"] == "-"
                    or row["layer_2"] == "="
                ):
                    df.at[index, "+/-"] = df.at[index, "layer_2"]
            layers = [col for col in df.columns if col.startswith("layer_")]
            df[layers] = df[layers].replace(["+", "-", "=", "NaN", "nan"], np.nan)
            df = df.replace("Z", np.nan)

            last_valid_value_1 = df["layer_1"].values[0]
            for index, row in df.iterrows():
                if pd.isna(row["layer_0"]) and pd.isna(row["layer_1"]):
                    df.at[index, "layer_1"] = last_valid_value_1
                if not pd.isna(row["layer_1"]):
                    last_valid_value_1 = row["layer_1"]
            df["layer_0"] = df["layer_0"].ffill()
            df.set_index(["layer_0", "layer_1", "layer_2"], inplace=True, drop=False)

            df["depth"] = np.nan
            df["depth"] = [(sum(pd.notna(x) for x in idx) - 1) for idx in df.index]
        except Exception as e:
            print(f"An error occurred while creating the multiindex structure: {e}")
            raise Exception(e)
        else:
            self.df_eb = df

    def map_variable_names(self) -> None:
        """
        Map variables to AT-Energy-Balance-specific variable names created from Sheets naming.

        This method takes the multi-index structure of the AEB-Sheet and
        maps the hierarchical variable names tospecific variable names
        created from that AEB-Sheet.

        It creates a new column "var_name" by concatenating the hierarchical labels
        of the multilayer index with ">" and sets the index to "var_name" and drops the column.

        The method updates the instance variables self.df_variables and self.df_eb in-place.
        """
        if "+/-" not in self.df_eb.columns:
            print("Need multiindex structure. Creating it first...")
            self.create_multiindex_structure()
        df_var_names = self.df_eb[
            ["layer_0", "layer_1", "layer_2", "index", "+/-", "depth"]
        ].copy()
        layer_0 = df_var_names["layer_0"].copy()
        layer_1 = df_var_names["layer_1"].copy()
        # forward fill layer_0 where layer_0 is NaN or in ["+", "-", "="]
        last_valid_value_0 = layer_0.values[0]
        valid_value_1 = layer_1.values[0]
        for i0, i1 in zip(range(0, len(layer_0.values)), range(0, len(layer_1.values))):
            val0 = layer_0.values[i0]
            val1 = layer_1.values[i1]
            if pd.notna(val0) and val0 not in ["+", "-", "="]:
                last_valid_value_0 = val0
            else:
                layer_0[i0] = last_valid_value_0
                if pd.notna(val1) and val1 not in ["+", "-", "="]:
                    valid_value_1 = layer_1.values[i1]
                else:
                    layer_1[i1] = valid_value_1

        df_var_names["layer_0"] = layer_0
        df_var_names["layer_1"] = layer_1
        var_names = []

        for index, row in df_var_names.iterrows():
            if not pd.isna(row["layer_0"]) and row["layer_0"] not in ["+", "-", "="]:
                var_name = row["layer_0"]
                if not pd.isna(row["layer_1"]) and row["layer_1"] not in [
                    "+",
                    "-",
                    "=",
                ]:
                    var_name += ">" + row["layer_1"]
                    if not pd.isna(row["layer_2"]) and row["layer_2"] not in [
                        "+",
                        "-",
                        "=",
                    ]:
                        var_name += ">" + row["layer_2"]
            elif not pd.isna(row["layer_1"]) and row["layer_1"] not in ["+", "-", "="]:
                var_name = row["layer_1"]
                if not pd.isna(row["layer_2"]) and row["layer_2"] not in [
                    "+",
                    "-",
                    "=",
                ]:
                    var_name += ">" + row["layer_2"]
            elif not pd.isna(row["layer_2"]) and row["layer_2"] not in ["+", "-", "="]:
                var_name = row["layer_2"]
            else:
                var_name = None
            var_names.append(var_name)
        df_var_names["var_name"] = var_names
        df_variables = df_var_names[["var_name", "index", "+/-"]].set_index(
            "var_name", drop=True
        )
        self.df_variables = df_variables
        self.df_eb["var_name"] = df_var_names["var_name"]

    def select(
        self,
        search_string: str | None = None,
        depth: int | None = None,
        only_return_index: bool = False,
        drop_multilayer: bool = False,
    ) -> pd.DataFrame:
        """
        Search for given string of any hierachical layer in multiindex
        ---
        Arguments:
        - search_string: string to search for (str, default: None)
        - depth: depth level to filter by (int, default: None)
        - only_return_index: only return index values (bool, default: False)
        - drop_multilayer: drop multi-layer structure and return flat DataFrame (bool, default: False)
        **Ether search_string or depth must be provided.**
        ---
        Returns:
        - matching rows as pandas DataFrame.
        - ValueError if no matches found.
        """
        found = []
        if search_string is None and depth is None:
            raise ValueError("Either search_string or depth must be provided.")
        if search_string != None:
            for tuples in self.df_eb.index:
                for strings in tuples:
                    if strings == search_string:
                        found.append(tuples)
            if found:
                df = self.df_eb.T[found].T
            else:
                msg = "No matches found for string '{search_string}'".format(
                    search_string=search_string
                )
                raise ValueError(msg)
        else:
            df = self.df_eb.copy()
        if depth != None:
            df = df[df["depth"] == depth]

        if only_return_index:
            if drop_multilayer:
                return df.var_name.values
            return df.index.values
        if drop_multilayer:
            return df.set_index("var_name").drop(
                columns=["layer_0", "layer_1", "layer_2"]
            )
            raise ValueError(msg)
