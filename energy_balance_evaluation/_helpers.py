import pandas as pd


def process_pypsa_mapping_to_csv(
    mapping_filepath: str, sheet_name: str = "20251114_inputs_eb_pypsa"
) -> None:
    """
    Processes a pypsa mapping file (ods-format) to a csv-file with seperator ";"
    and saves csv-file to same location and name as inputfile with .csv extension.

    Parameters
    ----------
    mapping_filepath : str
        Path to the pypsa mapping file (.ods)
    sheet_name : str, optional
        Name of the excel sheet to read from the pypsa mapping file.
        Defaults to "20251114_inputs_eb_pypsa".
    """
    pd.read_excel(mapping_filepath, sheet_name=sheet_name, engine="odf").to_csv(
        mapping_filepath.replace(".ods", ".csv"), sep=";", index=False
    )


def main():
    print("Directly executing _helpers-file!")
    process_pypsa_mapping_to_csv("~/data/AT-balance-sheets-April2025-mapped.ods")


if __name__ == "__main__":
    main()
