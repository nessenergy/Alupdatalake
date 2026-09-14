"""Migração do cofre local para o Secret Manager.

O que estes testes protegem: o script **nunca imprime uma credencial**, e a
simulação nunca grava. São as duas maneiras de um utilitário de migração
estragar exatamente aquilo que existe para proteger.
"""

from __future__ import annotations

import pytest
from scripts.migrar_segredos import _resumo, migrar

VALOR_DE_TESTE = "cafe1234567890abcdef"


@pytest.fixture
def cofre(tmp_path, monkeypatch):
    arquivo = tmp_path / "segredos.env"
    arquivo.write_text(f"alupdata-tempook-api-token={VALOR_DE_TESTE}\n", encoding="utf-8")
    monkeypatch.setenv("ALUPDATA_SECRETS_LOCAIS", "1")
    monkeypatch.setenv("ALUPDATA_SECRETS_ARQUIVO", str(arquivo))
    monkeypatch.delenv("K_SERVICE", raising=False)
    return arquivo


def test_resumo_nao_reconstroi_a_credencial():
    resumo = _resumo(VALOR_DE_TESTE)

    assert VALOR_DE_TESTE not in resumo
    assert "20 caracteres" in resumo  # tamanho confere contra o que o fornecedor informou


def test_simulacao_nao_grava_e_nao_imprime_o_valor(cofre, capsys, monkeypatch):
    def explode():
        raise AssertionError("simulação não pode falar com o Secret Manager")

    monkeypatch.setattr("google.cloud.secretmanager.SecretManagerServiceClient", explode, raising=False)

    assert migrar("alupdata-dev", aplicar=False) == 0

    saida = capsys.readouterr().out
    assert "simularia" in saida
    assert "alupdata-tempook-api-token" in saida
    assert VALOR_DE_TESTE not in saida


def test_valor_vazio_no_cofre_falha_em_vez_de_gravar_secret_vazio(tmp_path, monkeypatch, capsys):
    arquivo = tmp_path / "segredos.env"
    arquivo.write_text("alupdata-bbce-api-token=\n", encoding="utf-8")
    monkeypatch.setenv("ALUPDATA_SECRETS_LOCAIS", "1")
    monkeypatch.setenv("ALUPDATA_SECRETS_ARQUIVO", str(arquivo))

    assert migrar("alupdata-dev", aplicar=False) == 1
    assert "PULADO" in capsys.readouterr().out
