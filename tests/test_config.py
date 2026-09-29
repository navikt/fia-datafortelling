import pytest

from datafortelling_utils.config import bigquery_kilde


@pytest.mark.parametrize(
    ("project", "dataset"),
    [
        ("pia-dev-214a", "pia_bigquery_sink_v1_dataset_dev"),
        ("pia-prod-85b2", "pia_bigquery_sink_v1_dataset_prod"),
    ],
)
def test_bigquery_kilde_uses_explicit_environment(
    monkeypatch: pytest.MonkeyPatch, project: str, dataset: str
) -> None:
    monkeypatch.setenv("PROJECT", project)
    monkeypatch.setenv("DATASET", dataset)

    assert bigquery_kilde() == (project, dataset)


@pytest.mark.parametrize("missing", ["PROJECT", "DATASET"])
def test_bigquery_kilde_requires_both_variables(
    monkeypatch: pytest.MonkeyPatch, missing: str
) -> None:
    monkeypatch.setenv("PROJECT", "pia-dev-214a")
    monkeypatch.setenv("DATASET", "pia_bigquery_sink_v1_dataset_dev")
    monkeypatch.delenv(missing)

    with pytest.raises(KeyError, match=missing):
        bigquery_kilde()


@pytest.mark.parametrize("empty", ["PROJECT", "DATASET"])
def test_bigquery_kilde_rejects_empty_values(
    monkeypatch: pytest.MonkeyPatch, empty: str
) -> None:
    monkeypatch.setenv("PROJECT", "pia-dev-214a")
    monkeypatch.setenv("DATASET", "pia_bigquery_sink_v1_dataset_dev")
    monkeypatch.setenv(empty, "")

    with pytest.raises(ValueError, match="PROJECT og DATASET"):
        bigquery_kilde()
