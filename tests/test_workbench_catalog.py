from apps.workbench import catalog
from kinn.data.store import DataStore


def test_the_catalog_describes_the_build_without_reading_the_holdout(built):
    store = DataStore(built)
    page = catalog.catalog(built, store)
    assert page["schema"] == "data-catalog-1" and page["build"]["id"] == store.build_id
    assert page["calendar"]["sessions"] > 0 and page["calendar"]["last"] < "2023-11-09"
    assert page["companies"]["total"] == store.securities().num_rows
    names = {t["name"] for t in page["tables"]}
    assert {"panel", "security master"} <= names
    panel = next(t for t in page["tables"] if t["name"] == "panel")
    assert panel["rows"] and panel["bytes"] > 0
    assert any(b["current"] for b in page["builds"])
    assert page["seal"]["holdout_start"] == "2023-11-09"
    assert {i["name"] for i in page["inputs"]} == {"form4", "form8k_timed"}
    assert catalog.catalog(built, store)["build"] == page["build"]
