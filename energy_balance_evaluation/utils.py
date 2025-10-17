#!/usr/bin/env python3
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
    ):
        self.sheet_name = year
        self.path_to_xlsb = path_to_xlsb
        self.country = country
        self.df_eb = self.import_excel()

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
        df_eb.dropna(axis="columns", how="all", inplace=True)
        return df_eb

    def create_multiindex_structure(self) -> None:
        """Build multi-index from the 'index' column, capture +/- markers, showing input/output flows"""
        df_eb = self.df_eb.copy()
        try:
            df_eb["+/-"] = None
            df_eb["+/-"].astype("str")

            for index, row in df_eb.iterrows():
                if (
                    row["layer_0"] == "+"
                    or row["layer_0"] == "-"
                    or row["layer_0"] == "="
                ):
                    df_eb.at[index, "+/-"] = df_eb.at[index, "layer_0"]
                if (
                    row["layer_1"] == "+"
                    or row["layer_1"] == "-"
                    or row["layer_1"] == "="
                ):
                    df_eb.at[index, "+/-"] = df_eb.at[index, "layer_1"]
                if (
                    row["layer_2"] == "+"
                    or row["layer_2"] == "-"
                    or row["layer_2"] == "="
                ):
                    df_eb.at[index, "+/-"] = df_eb.at[index, "layer_2"]

            df_eb.replace("TI_NRG_FC_IND_NE", "TI_NRG-FC-IND_NE")
            var_multiindex = df_eb["index"].str.split("_", expand=True)

            df_eb["index0"] = var_multiindex[0]
            df_eb["index1"] = var_multiindex[1]
            df_eb["index2"] = var_multiindex[2]
            df_eb["index3"] = var_multiindex[3]
            df_eb_indexed = df_eb.set_index(
                ["index0", "index1", "index2", "index3"], inplace=False
            )

            df_eb_indexed["depth"] = np.nan
            df_eb_indexed["depth"] = [
                (sum(pd.notna(x) for x in idx) - 1) for idx in df_eb_indexed.index
            ]
        except Exception as e:
            print(f"An error occurred while creating the multiindex structure: {e}")
        else:
            self.df_eb = df_eb_indexed

    def map_variable_names(self) -> None:
        """Map variables to AT-Energy-Balance-specific variable names created from Sheets naming."""
        if "+/-" not in self.df_eb.columns:
            print("Need multiindex structure. Creating it first...")
            self.create_multiindex_structure()
        df_var_names = self.df_eb[
            ["layer_0", "layer_1", "layer_2", "index", "+/-", "depth"]
        ].copy()
        layer_0 = df_var_names["layer_0"].copy()
        layer_1 = df_var_names["layer_1"].copy()
        # forward fill layer_0 where layer_0 is NaN or in ["+", "-", "="
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
                    var_name += "_" + row["layer_1"]
                    if not pd.isna(row["layer_2"]) and row["layer_2"] not in [
                        "+",
                        "-",
                        "=",
                    ]:
                        var_name += "_" + row["layer_2"]
            elif not pd.isna(row["layer_1"]) and row["layer_1"] not in ["+", "-", "="]:
                var_name = row["layer_1"]
                if not pd.isna(row["layer_2"]) and row["layer_2"] not in [
                    "+",
                    "-",
                    "=",
                ]:
                    var_name += "_" + row["layer_2"]
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
