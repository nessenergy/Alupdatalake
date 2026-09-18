"""O esqueleto de conector novo gera os três .sqlx no formato do Dataform."""

from __future__ import annotations

from scripts import novo_conector


def test_esqueleto_gera_sqlx_das_tres_camadas(tmp_path, monkeypatch):
    monkeypatch.setattr(novo_conector, "RAIZ", tmp_path)

    assert novo_conector.main(["--fonte", "ons", "--entidade", "carga"]) == 0

    bronze = (tmp_path / "definitions" / "bronze" / "ons_carga.sqlx").read_text(encoding="utf-8")
    silver = (tmp_path / "definitions" / "silver" / "ons_carga.sqlx").read_text(encoding="utf-8")
    gold = (tmp_path / "definitions" / "gold" / "ons_carga.sqlx").read_text(encoding="utf-8")
    assert 'type: "operations"' in bronze and "CREATE TABLE IF NOT EXISTS ${self()}" in bronze
    assert 'type: "view"' in silver and '${ref("bronze", "ons_carga")}' in silver
    assert "uniqueKey:" in silver
    assert 'type: "table"' in gold and '${ref("silver", "ons_carga")}' in gold
    assert "dependOnDependencyAssertions: true" in gold
    assert not (tmp_path / "sql").exists()
