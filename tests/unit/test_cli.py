"""A CLI é o entrypoint do Cloud Run Job e da DAG — erro aqui só apareceria em produção."""

import pytest
from src.cli import main
from src.core.execucao import Janela


@pytest.fixture
def ingestoes(monkeypatch):
    """Captura o que a CLI pediria ao conector, sem executar ingestão."""
    chamadas = []

    class ConectorFalso:
        def ingerir(self, janela: Janela):
            chamadas.append(janela)
            return type("E", (), {"status": "SUCESSO"})()

    monkeypatch.setattr("src.cli.obter", lambda _rotulo: ConectorFalso())
    return chamadas


def test_listar_imprime_os_conectores_registrados(capsys):
    assert main(["listar"]) == 0

    saida = capsys.readouterr().out
    assert "bcb_cambio_ptax" in saida
    assert "ons_carga" in saida


def test_ingerir_com_de_e_ate_monta_a_janela(ingestoes):
    assert main(["ingerir", "ons_carga", "--de", "2026-01-01", "--ate", "2026-01-31"]) == 0
    assert ingestoes == [Janela.de_texto("2026-01-01", "2026-01-31")]


def test_ingerir_com_ultimos_dias(ingestoes):
    main(["ingerir", "ons_carga", "--ultimos-dias", "7"])

    (janela,) = ingestoes
    assert len(janela.dias()) == 7


def test_sem_janela_a_cli_recusa(ingestoes):
    with pytest.raises(SystemExit, match="--de e --ate"):
        main(["ingerir", "ons_carga"])
    assert ingestoes == []


def test_apenas_de_sem_ate_tambem_recusa(ingestoes):
    with pytest.raises(SystemExit):
        main(["ingerir", "ons_carga", "--de", "2026-01-01"])


def test_janela_invertida_e_rejeitada(ingestoes):
    with pytest.raises(ValueError, match="invertida"):
        main(["ingerir", "ons_carga", "--de", "2026-02-01", "--ate", "2026-01-01"])


def test_dry_run_liga_a_configuracao(ingestoes):
    from src.core.config import get_settings

    main(["ingerir", "ons_carga", "--de", "2026-01-01", "--ate", "2026-01-02", "--dry-run"])

    assert get_settings().dry_run is True


def test_execucao_com_erro_devolve_codigo_1(monkeypatch):
    class ConectorQueFalha:
        def ingerir(self, _janela):
            return type("E", (), {"status": "ERRO"})()

    monkeypatch.setattr("src.cli.obter", lambda _r: ConectorQueFalha())

    assert main(["ingerir", "ons_carga", "--ultimos-dias", "1"]) == 1


def test_conector_desconhecido_falha_alto():
    with pytest.raises(KeyError, match="desconhecido"):
        main(["ingerir", "fonte_que_nao_existe", "--ultimos-dias", "1"])
