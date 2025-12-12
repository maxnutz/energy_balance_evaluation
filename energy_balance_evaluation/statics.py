# dict of rows to include for the light version of the energy balance
rows_to_include_dict = {
    "Total absolute values": {
        "Primary production": True,  #
        "Recovered & recycled products": False,
        "Imports": True,  #
        "Exports": True,  #
        "Change in stock": True,  #
        "Gross available energy": True,  #
        "International maritime bunkers": True,  #
        "Gross inland consumption": True,  #
        "International aviation": True,  #
        "Total energy supply": True,  #
        "Gross inland consumption (Europe 2020-2030)": False,
        "Primary energy consumption (Europe 2020-2030)": False,
        "Final energy consumption (Europe 2020-2030)": False,
    },
    "Transformation input": {
        "nan": True,
        "Electricity & heat generation": {
            "nan": True,
            "Main activity producer electricity only": True,
            "Main activity producer CHP": True,
            "Main activity producer heat only": True,
            "Autoproducer electricity only": True,  # sum to Main activitiv producer electricity only
            "Autoproducer CHP ": True,  # sum to Main activity producer CHP
            "Autoproducer heat only": True,  # sum to Main activity producer heat only
            "Electrically driven heat pumps": True,
            "Electric boilers": False,
            "Electricity for pumped storage": True,
            "Derived heat for electricity production": False,
        },
        "Coke ovens": False,
        "Blast furnaces": False,
        "Gas works": True,
        "Refineries & petrochemical industry": {
            "nan": True,
            "Refinery intake": False,
            "Backflows from petrochemical industry": False,
            "Products transferred": False,
            "Interproduct transfers": False,
            "Direct use": False,
            "Petrochemical industry intake": False,
        },
        "Patent fuel plants": False,
        "BKB & PB plants": False,
        "Coal liquefaction plants": False,
        "For blended natural gas": False,
        "Liquid biofuels blended": False,
        "Charcoal production plants": False,
        "Gas-to-liquids plants": False,
        "Not elsewhere specified ": False,
    },
    "Transformation output": False,
    "Energy sector": False,
    "Distribution losses": True,
    "Available for final consumption": True,
    "Final non-energy consumption": False,
    "Final energy consumption": {
        "nan": True,
        "Industry sector": {
            "nan": True,
            "Iron & steel": False,
            "Chemical & petrochemical": False,
            "Non-ferrous metals": False,
            "Non-metallic minerals": False,
            "Transport equipment": False,
            "Machinery": False,
            "Mining & quarrying": False,
            "Food, beverages & tobacco": False,
            "Paper, pulp & printing": False,
            "Wood & wood products": False,
            "Construction": False,
            "Textile & leather": False,
            "Not elsewhere specified (industry)": False,
        },
        "Transport sector": {
            "nan": True,
            "Rail": True,  # sum with road
            "Road": True,  # sum with Rail
            "Domestic aviation": True,  # sum with international aviation!
            "Domestic navigation": True,  # sum with Road and Rail
            "Pipeline transport": True,
            "Not elsewhere specified (transport)": False,
        },
        "Other sectors": {
            "nan": True,
            "Commercial & public services": True,  # sum with households
            "Households": True,  # sum with commercial & public services
            "Agriculture & forestry": True,
            "Fishing": True,  # sum with agriculture & forestry??
            "Not elsewhere specified (other)": False,
        },
    },
}

# dict of rows-lists to be added together for the light version of the energy balance
rows_to_add_dict = {
    "Final energy consumption>Transport sector>Land transport": [
        "Final energy consumption>Transport sector>Road",
        "Final energy consumption>Transport sector>Rail",
        "Final energy consumption>Transport sector>Domestic navigation",
    ],
    "Total absolute values>National and International aviation": [
        "Total absolute values>International aviation",
        "Final energy consumption>Transport sector>Domestic aviation",
    ],
    "Final energy consumption>Other sectors>Households & Commercial & public services": [
        "Final energy consumption>Other sectors>Commercial & public services",
        "Final energy consumption>Other sectors>Households",
    ],
    "Final energy consumption>Other sectors>Agriculture & forestry & fishing": [
        "Final energy consumption>Other sectors>Agriculture & forestry",
        "Final energy consumption>Other sectors>Fishing",
    ],
}

# non numerical columns in eurostat energy balance matrix
non_numerical_columns_list = [
    "layer_0",
    "layer_1",
    "layer_2",
    "index",
    "+/-",
    "depth",
    "var_name",
]
