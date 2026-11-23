"""Sumarização hierárquica e composição numérica, sem atribuir cálculos ao LLM."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from services.consulta_oficial import filtrar
from services.engenharia_prompts import construir_instrucoes
from services.siconfi import FUNCOES_CODIGO, UF_IBGE

TAMANHO_TRECHO = 2300
MAX_TRECHOS = 5  # Restringe requisições longas na GPU de 8 GiB.


class TextoAcimaDaCapacidade(ValueError):
    pass


class RecorteIncompleto(ValueError):
    pass


@dataclass(frozen=True)
class ResultadoSumarizacao:
    resultado: str
    etapas: int
    tokens_entrada: int
    tokens_saida: int
    tempo_ms: int


def dividir_texto(texto: str, *, tamanho: int = TAMANHO_TRECHO) -> list[str]:
    """Divide sem eliminar caracteres, preferindo espaços como fronteira."""
    if not texto.strip():
        raise ValueError("Documento sem conteúdo textual legível.")
    trechos = []
    resto = texto.strip()
    while resto:
        if len(resto) <= tamanho:
            trechos.append(resto)
            break
        corte = resto.rfind(" ", int(tamanho * .6), tamanho + 1)
        if corte < 1:
            corte = tamanho
        trechos.append(resto[:corte].strip())
        resto = resto[corte:].lstrip()
    if len(trechos) > MAX_TRECHOS:
        raise TextoAcimaDaCapacidade(
            "O documento excede a capacidade desta sessão local. "
            "Limite de cinco trechos por solicitação; divida-o em documentos menores."
        )
    return trechos


def _gerar(servico, conteudo: str, modo: str, versao: str, max_tokens: int, etapa: str):
    sistema, tarefa = construir_instrucoes(modo, versao, etapa=etapa)
    return servico.gerar(
        texto=conteudo, operacao="resumo", max_novos_tokens=max_tokens,
        instrucoes_sistema=sistema, instrucao_tarefa=tarefa,
    )


def sumarizar(texto: str, *, modo: str, versao: str, max_tokens: int, servico) -> ResultadoSumarizacao:
    trechos = dividir_texto(texto)
    metricas = []
    if len(trechos) == 1:
        resultado = _gerar(servico, trechos[0], modo, versao, max_tokens, "final")
        metricas.append(resultado)
    else:
        apontamentos = []
        # A síntese intermediária fica mais curta para caber no contexto final.
        for indice, trecho in enumerate(trechos, start=1):
            parcial = _gerar(servico, f"Trecho {indice}/{len(trechos)}:\n{trecho}", modo,
                             versao, min(max_tokens, 128), "trecho")
            metricas.append(parcial)
            apontamentos.append(f"Trecho {indice}: {parcial.texto}")
        consolidado = "Sínteses parciais do mesmo documento (não inventar informação):\n" + "\n".join(apontamentos)
        resultado = _gerar(servico, consolidado, modo, versao, max_tokens, "final")
        metricas.append(resultado)
    return ResultadoSumarizacao(
        resultado=resultado.texto, etapas=len(metricas),
        tokens_entrada=sum(r.tokens_entrada for r in metricas),
        tokens_saida=sum(r.tokens_saida for r in metricas),
        tempo_ms=sum(r.tempo_ms for r in metricas),
    )


def _moeda(valor: Decimal) -> str:
    representacao = f"{valor:,.2f}".replace(",", "#").replace(".", ",").replace("#", ".")
    return f"R$ {representacao}"


def contexto_fiscal(ufs: list[str], ano: int, funcoes: list[str]) -> tuple[str, list[str], int]:
    """Calcula resultados exatos para as UFs escolhidas. Não preenche ausências."""
    if not ufs or any(uf not in UF_IBGE for uf in ufs) or len(set(ufs)) != len(ufs):
        raise ValueError("Selecione UFs válidas e sem repetição.")
    if not funcoes or any(f not in FUNCOES_CODIGO for f in funcoes) or len(set(funcoes)) != len(funcoes):
        raise ValueError("Selecione funções válidas e sem repetição.")
    registros = [r for r in filtrar(ano=ano) if r["uf"] in ufs and r["funcao"] in funcoes]
    if not registros:
        raise RecorteIncompleto("Não há registros oficiais disponíveis para esse recorte.")
    mapa = {(r["uf"], r["funcao"]): r for r in registros}
    faltantes = [(uf, f) for uf in ufs for f in funcoes if (uf, f) not in mapa]
    secoes = [
        f"Base: Siconfi RREO Anexo 02; exercício {ano}; 6º bimestre; despesas liquidadas acumuladas; ",
        "governos estaduais e distrital, excluídas despesas intraorçamentárias; valores nominais declarados, não auditados pelo aplicativo.",
        f"UFs solicitadas: {', '.join(ufs)}. Funções: {', '.join(funcoes)}.",
        f"Cobertura: {len(registros)} de {len(ufs)*len(funcoes)} combinações UF/função.",
    ]
    if faltantes:
        secoes.append("Dados ausentes: " + ", ".join(f"{uf}/{f}" for uf, f in faltantes) + ".")
    for f in funcoes:
        presentes = [mapa[(uf, f)]["valor_reais"] for uf in ufs if (uf, f) in mapa]
        if len(presentes) == len(ufs):
            secoes.append(f"Soma da função {f} para as UFs selecionadas: {_moeda(sum(presentes, Decimal(0)))}.")
        else:
            secoes.append(f"Soma da função {f}: não calculada por falta de cobertura completa.")
    completos = []
    for uf in ufs:
        if all((uf, f) in mapa for f in funcoes):
            total = sum((mapa[(uf, f)]["valor_reais"] for f in funcoes), Decimal(0))
            completos.append((uf, total))
    if completos:
        completos.sort(key=lambda p: (-p[1], p[0]))
        if len(completos) <= 10:
            rankings = completos
        else:
            rankings = completos[:5] + completos[-3:]
        secoes.append(
            "Soma das funções selecionadas por UF com cobertura completa (não é despesa total do orçamento): "
            + "; ".join(f"{uf}: {_moeda(total)}" for uf, total in rankings) + "."
        )
        if len(completos) > 10:
            secoes.append("Para concisão, apresentados os cinco maiores e três menores valores.")
    secoes.append("Não existe população do IBGE integrada nesta análise; não calcule valores per capita.")
    secoes.append("Diferenças de montante não demonstram eficiência, desempenho ou causalidade.")
    fontes = sorted({r["fonte_url"] for r in registros if r.get("fonte_url")})
    return "\n".join(secoes), fontes, len(registros)
