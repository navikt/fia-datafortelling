import os


def bigquery_kilde() -> tuple[str, str]:
    project = os.environ["PROJECT"]
    dataset = os.environ["DATASET"]
    if not project or not dataset:
        raise ValueError("PROJECT og DATASET må ha verdier")
    return project, dataset
