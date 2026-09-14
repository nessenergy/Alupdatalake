"""Leitura de credenciais: Secret Manager em produção, cofre local antes de A3.

A cláusula 8.5 proíbe credencial em código, `.env` versionado, log ou mensagem
de erro. O cofre local existe porque o projeto GCP ainda não existe (A3), e é
desenhado para **não conseguir** virar porta aberta em produção:

- é opt-in explícito, nunca fallback silencioso;
- recusa rodar dentro do Cloud Run;
- recusa arquivo dentro do repositório, que é o único jeito de ele ser
  commitado por acidente.
"""

from __future__ import annotations

import pytest
from src.core.secrets import RAIZ_REPO, ler_secret, nome_secret


@pytest.fixture(autouse=True)
def _limpa_cache():
    ler_secret.cache_clear()
    yield
    ler_secret.cache_clear()


@pytest.fixture
def cofre(tmp_path, monkeypatch):
    """Um cofre local válido, fora do repositório."""
    arquivo = tmp_path / "segredos.env"
    arquivo.write_text(
        "# comentário é ignorado\n"
        "alupdata-tempook-api-token=tok-do-tempook\n"
        "\n"
        "alupdata-hubspot-api-token = com-espacos \n",
        encoding="utf-8",
    )
    monkeypatch.setenv("ALUPDATA_SECRETS_LOCAIS", "1")
    monkeypatch.setenv("ALUPDATA_SECRETS_ARQUIVO", str(arquivo))
    monkeypatch.delenv("K_SERVICE", raising=False)
    monkeypatch.delenv("CLOUD_RUN_JOB", raising=False)
    return arquivo


def test_nome_do_secret_e_o_nome_canonico():
    assert nome_secret("tempook", "api-token") == "alupdata-tempook-api-token"


def test_le_do_cofre_local_quando_habilitado(cofre):
    assert ler_secret("tempook", "api-token") == "tok-do-tempook"


def test_espacos_em_volta_do_valor_sao_removidos(cofre):
    """Colar um token com espaço sobrando é o erro mais fácil de cometer."""
    assert ler_secret("hubspot", "api-token") == "com-espacos"


def test_secret_ausente_no_cofre_diz_o_nome_que_falta_e_nao_vaza_valor(cofre):
    with pytest.raises(KeyError) as erro:
        ler_secret("bbce", "api-token")

    mensagem = str(erro.value)
    assert "alupdata-bbce-api-token" in mensagem
    assert "tok-do-tempook" not in mensagem  # nenhum valor do cofre na mensagem


def test_cofre_inexistente_diz_onde_era_esperado(tmp_path, monkeypatch):
    monkeypatch.setenv("ALUPDATA_SECRETS_LOCAIS", "1")
    monkeypatch.setenv("ALUPDATA_SECRETS_ARQUIVO", str(tmp_path / "nao-existe.env"))
    monkeypatch.delenv("K_SERVICE", raising=False)

    with pytest.raises(FileNotFoundError, match="nao-existe.env"):
        ler_secret("tempook", "api-token")


# ------------------------------------------------------------------- as travas


def test_cofre_dentro_do_repositorio_e_recusado(monkeypatch):
    """É o único jeito de o arquivo ser commitado por acidente."""
    monkeypatch.setenv("ALUPDATA_SECRETS_LOCAIS", "1")
    monkeypatch.setenv("ALUPDATA_SECRETS_ARQUIVO", str(RAIZ_REPO / "segredos.env"))
    monkeypatch.delenv("K_SERVICE", raising=False)

    with pytest.raises(ValueError, match="dentro do repositório"):
        ler_secret("tempook", "api-token")


@pytest.mark.parametrize("variavel", ["K_SERVICE", "CLOUD_RUN_JOB"])
def test_cofre_local_e_recusado_dentro_do_cloud_run(cofre, monkeypatch, variavel):
    """Em produção a credencial vem do Secret Manager, e ponto."""
    monkeypatch.setenv(variavel, "ingestao-tempook-boletins")

    with pytest.raises(RuntimeError, match="Secret Manager"):
        ler_secret("tempook", "api-token")


def test_sem_opt_in_nao_ha_fallback_silencioso_para_o_cofre(cofre, monkeypatch):
    """Sem a variável de opt-in, vai ao Secret Manager mesmo que o cofre exista.

    Fallback silencioso deixaria um token local antigo mascarar o de produção.
    """
    monkeypatch.delenv("ALUPDATA_SECRETS_LOCAIS")
    chamou = {"secret_manager": False}

    def ClienteFalso():  # noqa: N802 — substitui uma classe do SDK
        chamou["secret_manager"] = True
        raise RuntimeError("sem credencial de GCP neste teste")

    # Trocar o atributo, e não `sys.modules`: `from google.cloud import
    # secretmanager` resolve por getattr no pacote quando o módulo real já foi
    # importado por outro teste, e aí um dublê em sys.modules é ignorado.
    monkeypatch.setattr("google.cloud.secretmanager.SecretManagerServiceClient", ClienteFalso)

    with pytest.raises(RuntimeError, match="sem credencial de GCP"):
        ler_secret("tempook", "api-token")

    assert chamou["secret_manager"], "deveria ter ido ao Secret Manager, não ao cofre"
