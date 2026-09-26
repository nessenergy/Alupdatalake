"""Gerador do painel vivo (docs/planos/2026-09-25-painel-vivo.md).

Cada bloco do painel sai de uma função pura sobre dados já lidos; a leitura das
fontes (BigQuery, GitHub, Cloud Run) é fina e fica fora destes testes.
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import pytest
from scripts import painel
from scripts.painel import BRASILIA

RAIZ = Path(__file__).resolve().parents[2]
HOJE = date(2026, 9, 26)


def _exec(entidade: str, status: str, dia: int, hora: int = 9, ambiente: str = "dev", linhas: int = 3) -> dict:
    fonte, _, nome = entidade.partition("_")
    return {
        "ambiente": ambiente,
        "fonte": fonte,
        "entidade": nome,
        "status": status,
        "linhas_carregadas": linhas,
        "iniciada_em": datetime(2026, 9, dia, hora, tzinfo=BRASILIA),
    }


# ------------------------------------------------------------------ marcos


def test_marcos_do_repositorio_sao_validos():
    marcos = painel.carregar_marcos(RAIZ / "painel" / "marcos.toml")
    assert [o["numero"] for o in marcos["onda"]] == [0, 1, 2, 3, 4]
    entidades = [e for o in marcos["onda"] for e in o["entidades"]]
    assert len(entidades) == len(set(entidades)), "entidade em duas ondas"
    assert len(marcos["onda"][0]["entidades"]) + len(marcos["onda"][1]["entidades"]) == 23


@pytest.mark.parametrize(
    ("trecho", "erro"),
    [
        ('estado = "entregue"', 'estado = "quase"'),
        ("janela = [2026-08-31, 2026-09-11]", "janela = [2026-09-11, 2026-08-31]"),
    ],
)
def test_marcos_invalidos_sao_recusados(tmp_path, trecho, erro):
    texto = (RAIZ / "painel" / "marcos.toml").read_text(encoding="utf-8").replace(trecho, erro, 1)
    arquivo = tmp_path / "marcos.toml"
    arquivo.write_text(texto, encoding="utf-8")
    with pytest.raises(ValueError):
        painel.carregar_marcos(arquivo)


# ------------------------------------------------------------------ cargas


def test_cargas_por_onda_usam_a_ultima_execucao_de_cada_ambiente():
    ondas = [{"numero": 0, "entidades": ["bcb_cambio_ptax"]}, {"numero": 1, "entidades": ["ons_carga"]}]
    execucoes = [
        _exec("bcb_cambio_ptax", "ERRO", 24),
        _exec("bcb_cambio_ptax", "SUCESSO", 25),
        _exec("bcb_cambio_ptax", "SUCESSO", 25, ambiente="hml"),
        _exec("ons_carga", "SUCESSO", 24),
        _exec("ons_carga", "ERRO", 25),
    ]

    cargas = painel.resumir_cargas(execucoes, ondas)

    onda0, onda1 = cargas
    assert onda0["entidades"][0]["dev"]["status"] == "SUCESSO"
    assert onda0["entidades"][0]["hml"]["status"] == "SUCESSO"
    assert onda0["ok"] == {"dev": 1, "hml": 1, "total": 1}
    assert onda1["entidades"][0]["dev"]["status"] == "ERRO", "vale a última, não a melhor"
    assert onda1["entidades"][0]["hml"] is None, "entidade que nunca rodou no ambiente"
    assert onda1["ok"] == {"dev": 0, "hml": 0, "total": 1}


def test_dias_seguidos_contam_ate_hoje_ou_ate_ontem_se_hoje_ainda_nao_rodou():
    execucoes = [_exec("bcb_cambio_ptax", "SUCESSO", d) for d in (23, 24, 25)] + [_exec("bcb_cambio_ptax", "ERRO", 22)]
    assert painel.dias_seguidos(execucoes, "bcb_cambio_ptax", HOJE) == 3  # 26/09 ainda não rodou
    execucoes.append(_exec("bcb_cambio_ptax", "SUCESSO", 26))
    assert painel.dias_seguidos(execucoes, "bcb_cambio_ptax", HOJE) == 4


def test_dia_sem_sucesso_zera_a_sequencia():
    execucoes = [_exec("bcb_cambio_ptax", "SUCESSO", 23), _exec("bcb_cambio_ptax", "SUCESSO", 25)]
    assert painel.dias_seguidos(execucoes, "bcb_cambio_ptax", HOJE) == 1
    assert painel.dias_seguidos([], "bcb_cambio_ptax", HOJE) == 0


def test_dias_seguidos_so_olham_dev():
    execucoes = [_exec("bcb_cambio_ptax", "SUCESSO", d, ambiente="hml") for d in (24, 25)]
    assert painel.dias_seguidos(execucoes, "bcb_cambio_ptax", HOJE) == 0


# ------------------------------------------------------------------ pendências


def _issue(numero: int, titulo: str, corpo: str = "", comentarios: tuple[str, ...] = (), dia: int = 20) -> dict:
    return {
        "number": numero,
        "title": titulo,
        "body": corpo,
        "comments": list(comentarios),
        "created_at": datetime(2026, 9, dia, 12, tzinfo=BRASILIA),
        "url": f"https://github.com/x/y/issues/{numero}",
    }


def test_pendencias_leem_o_prazo_do_corpo_ou_do_ultimo_comentario_e_ordenam_por_urgencia():
    issues = [
        _issue(1, "[ALUP] Sem prazo"),
        _issue(2, "[ALUP] Futura", "texto\n\nPrazo: 2026-10-12"),
        _issue(3, "[ALUP] Vencida", "Prazo: 2026-10-30", ("Situação.\n\nPrazo: 2026-09-25",)),
        _issue(4, "[ALUP] Próxima", "Prazo: 2026-09-29", dia=25),
    ]

    pend = painel.resumir_pendencias(issues, HOJE)

    assert [p["numero"] for p in pend] == [3, 4, 2, 1]
    vencida = pend[0]
    assert vencida["titulo"] == "Vencida", "o prefixo [ALUP] sai do título"
    assert vencida["prazo"] == "2026-09-25"
    assert vencida["atrasada"] is True
    assert vencida["dias_aberta"] == 6
    assert pend[1]["atrasada"] is False
    assert pend[3]["prazo"] is None


# ------------------------------------------------------------------ rede


def test_teste_de_conexao_resume_a_ultima_execucao():
    execucoes = [
        {"fim": datetime(2026, 9, 25, 18, 5, tzinfo=BRASILIA), "sucesso": False},
        {"fim": datetime(2026, 9, 25, 17, 40, tzinfo=BRASILIA), "sucesso": False},
    ]
    assert painel.resumir_teste_conexao(execucoes) == {"estado": "falhou", "em": "2026-09-25T18:05:00-03:00"}
    assert painel.resumir_teste_conexao([]) == {"estado": "nunca_rodou", "em": None}


# ------------------------------------------------------------------ dados.json


def test_dados_juntam_os_blocos_e_nao_levam_linha_de_dado():
    marcos = painel.carregar_marcos(RAIZ / "painel" / "marcos.toml")
    agora = datetime(2026, 9, 26, 10, 0, tzinfo=BRASILIA)
    execucoes = [_exec("bcb_cambio_ptax", "SUCESSO", 25)]

    dados = painel.montar(marcos, execucoes, [], [], agora)

    assert dados["gerado_em"] == "2026-09-26T10:00:00-03:00"
    assert set(dados) >= {"gerado_em", "ondas", "marcos", "cargas", "dias_seguidos", "pendencias", "rede"}
    assert dados["dias_seguidos"] == {"entidade": "bcb_cambio_ptax", "dias": 1, "meta": 3}
    assert dados["rede"]["teste_conexao"]["estado"] == "nunca_rodou"
    # Só metadado de execução: nenhuma chave de conteúdo de tabela.
    entidade = dados["cargas"][0]["entidades"][0]
    assert set(entidade) == {"entidade", "dev", "hml"}
    assert set(entidade["dev"]) == {"status", "linhas", "em"}


# ------------------------------------------------------------------ entre jobs do workflow


def test_execucoes_exportadas_voltam_iguais():
    """O job de hml exporta; o de publicação importa. Nada se perde no caminho."""
    execucoes = [_exec("ons_carga", "SUCESSO", 25, ambiente="hml"), _exec("ons_ear", "ERRO", 24, ambiente="hml")]
    texto = painel.exportar_execucoes(execucoes)
    assert painel.importar_execucoes(texto) == execucoes


def test_importar_execucoes_vazias_nao_quebra_o_painel():
    """Se o job de hml falhar, o painel sai só com dev, em vez de não sair."""
    assert painel.importar_execucoes("") == []
    assert painel.importar_execucoes("   \n") == []


# ------------------------------------------------------------------ workflow


def test_workflow_do_painel_le_hml_sem_deployment_e_publica_com_identidade_propria():
    texto = (RAIZ / ".github" / "workflows" / "painel.yml").read_text(encoding="utf-8")
    assert 'cron: "7 * * * *"' in texto
    assert "name: hml\n      deployment: false" in texto, "hml sem registrar deployment a cada hora"
    assert "if: ${{ !cancelled() }}" in texto, "sem hml, o painel sai só com dev"
    assert "${{ inputs." not in texto
    # A escrita no projeto da ness. usa a identidade do painel, nunca a de deploy da Alupar.
    publicar = texto[texto.index("  publicar:") :]
    assert publicar.index("vars.GCP_DEPLOY_SA") < publicar.index("vars.PAINEL_SA") < publicar.index("gcloud storage cp")
    assert "permissions:\n  contents: read\n  id-token: write\n  issues: read\n" in texto


# ------------------------------------------------------------------ progresso global


def test_itens_de_cada_onda_somam_as_horas_da_proposta():
    marcos = painel.carregar_marcos(RAIZ / "painel" / "marcos.toml")
    assert sum(o["horas"] for o in marcos["onda"]) == 580
    for onda in marcos["onda"]:
        assert sum(i["horas"] for i in onda["item"]) == onda["horas"], onda["numero"]


def test_progresso_pesa_cada_item_pelas_horas_e_separa_aceito_em_aceite_e_adiantado():
    ondas = [
        {"numero": 0, "horas": 10, "estado": "aceita", "item": [{"horas": 10, "pronto": 1.0}]},
        {"numero": 1, "horas": 20, "estado": "entregue", "item": [{"horas": 20, "pronto": 1.0}]},
        {
            "numero": 2,
            "horas": 40,
            "estado": "aguarda_alup",
            "item": [{"horas": 30, "pronto": 0.5}, {"horas": 10, "pronto": 0}],
        },
        {"numero": 3, "horas": 30, "estado": "nao_iniciada", "item": [{"horas": 30, "auto": "dias_seguidos"}]},
    ]

    prog = painel.resumir_progresso(ondas, dias=2, meta=3)

    assert prog["horas_total"] == 100
    assert prog["aceito"] == 10
    assert prog["em_aceite"] == 20
    assert prog["adiantado"] == pytest.approx(15 + 20)  # 30 × 0,5 + 30 × 2/3
    assert prog["pct"] == pytest.approx(65.0)
    assert [o["prontas"] for o in prog["por_onda"]] == pytest.approx([10, 20, 15, 20])


def test_fracao_pronta_fora_de_zero_a_um_e_recusada(tmp_path):
    texto = (RAIZ / "painel" / "marcos.toml").read_text(encoding="utf-8").replace("pronto = 1.0", "pronto = 1.5", 1)
    arquivo = tmp_path / "marcos.toml"
    arquivo.write_text(texto, encoding="utf-8")
    with pytest.raises(ValueError):
        painel.carregar_marcos(arquivo)


# ------------------------------------------------------------------ dias adiantados ou atrasados


def test_onda_entregue_compara_a_entrega_com_o_fim_da_janela():
    onda = {"janela": [date(2026, 9, 14), date(2026, 10, 16)], "entregue_em": date(2026, 9, 25)}
    assert painel.saldo_dias(onda, fracao=1.0, hoje=HOJE) == 21
    atrasada = {"janela": [date(2026, 8, 31), date(2026, 9, 11)], "entregue_em": date(2026, 9, 25)}
    assert painel.saldo_dias(atrasada, fracao=1.0, hoje=HOJE) == -14


def test_onda_nao_entregue_compara_o_trabalho_feito_com_o_tempo_corrido_da_janela():
    antes = {"janela": [date(2026, 10, 19), date(2026, 11, 13)]}  # 25 dias; ainda não abriu
    assert painel.saldo_dias(antes, fracao=0.56, hoje=HOJE) == 14
    dentro = {"janela": [date(2026, 9, 16), date(2026, 10, 16)]}  # 30 dias; 10 corridos
    assert painel.saldo_dias(dentro, fracao=0.2, hoje=HOJE) == -4
    assert painel.saldo_dias(dentro, fracao=0.5, hoje=HOJE) == 5


def test_onda_com_prazo_postergado_mede_a_entrega_contra_o_prazo_vigente():
    """Cláusula 3ª: insumo atrasado posterga o prazo; a folga conta contra ele, não contra a janela original."""
    onda = {
        "janela": [date(2026, 8, 31), date(2026, 9, 11)],
        "entregue_em": date(2026, 9, 25),
        "prazo_postergado": date(2026, 9, 30),
    }
    assert painel.saldo_dias(onda, fracao=1.0, hoje=HOJE) == 5
