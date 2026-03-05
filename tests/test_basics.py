import yaml
import pandas as pd
import pytest
from energy_balance_evaluation import VariablesSet


def test_import_variables_set():
    assert VariablesSet is not None


def test_read_yaml_file(tmp_path):
    yaml_content = [
        {"Final Energy": {"nrg": "FC_E", "siec": "TOTAL"}}
    ]
    p = tmp_path / "vars.yaml"
    p.write_text(yaml.safe_dump(yaml_content))
    vs = VariablesSet("final_energy", 2020, str(p), "out.yaml", country="AT")
    d = vs.read_yaml_file()
    assert "Final Energy" in d


def test_calculate_variable_values_with_dataframe():
    vs = VariablesSet(
        "final_energy",
        2020,
        "definitions/variable/final_energy.yaml",
        "out.yaml",
        country="AT",
    )
    vs.variables_dict = {"Final Energy": {"nrg": "FC_E", "siec": "TOTAL"}}
    df = pd.DataFrame(
        [
            {
                "freq": "A",
                "nrg_bal": "FC_E",
                "siec": "TOTAL",
                "unit": "GWH",
                "geo": "AT",
                "2020": 100.0,
            }
        ]
    )
    vs.tsv_data = df
    res = vs.calculate_variable_values("unused.tsv")
    assert res["Final Energy"] == 100.0


def test_calculate_variable_values_reads_tsv_file(tmp_path):
    vs = VariablesSet(
        "final_energy",
        2020,
        "definitions/variable/final_energy.yaml",
        "out.yaml",
        country="AT",
    )
    vs.variables_dict = {"Final Energy": {"nrg": "FC_E", "siec": "TOTAL"}}
    vs.tsv_data = None

    tsv_path = tmp_path / "energy_data.tsv"
    df = pd.DataFrame(
        [
            {
                "freq": "A",
                "nrg_bal": "FC_E",
                "siec": "TOTAL",
                "unit": "GWH",
                "geo": "AT",
                "2020": 100.0,
            }
        ]
    )
    df.to_csv(tsv_path, sep="\t", index=False)

    res = vs.calculate_variable_values(str(tsv_path))

    assert res["Final Energy"] == 100.0


def test_fetch_and_load_tsv_data_downloads_when_file_missing(tmp_path, monkeypatch):
    vs = VariablesSet(
        "final_energy",
        2020,
        "definitions/variable/final_energy.yaml",
        "out.yaml",
        country="AT",
    )
    vs.variables_dict = {"Final Energy": {"nrg": "FC_E", "siec": "TOTAL"}}
    vs.tsv_data = None

    tsv_path = tmp_path / "downloaded_energy_data.tsv"
    assert not tsv_path.exists()

    fake_tsv_content = (
        "freq\tnrg_bal\tsiec\tunit\tgeo\t2020\n"
        "A\tFC_E\tTOTAL\tGWH\tAT\t100.0\n"
    )

    class FakeResponse:
        def __init__(self, payload: bytes):
            self.payload = payload

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return self.payload

    def fake_urlopen(url: str) -> FakeResponse:
        del url
        import gzip

        payload = gzip.compress(fake_tsv_content.encode("utf-8"))
        return FakeResponse(payload)

    monkeypatch.setattr(
        "energy_balance_evaluation.energy_balance_eval.urlopen",
        fake_urlopen,
        raising=True,
    )

    with pytest.warns(UserWarning, match="not found"):
        res = vs.calculate_variable_values(str(tsv_path))

    assert tsv_path.exists()

    expected_columns = {"freq", "nrg_bal", "siec", "unit", "geo", "2020"}
    assert expected_columns.issubset(set(vs.tsv_data.columns))
    assert pd.api.types.is_numeric_dtype(vs.tsv_data["2020"])
    assert res["Final Energy"] == 100.0
