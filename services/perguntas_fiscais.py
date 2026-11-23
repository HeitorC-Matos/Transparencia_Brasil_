"""Perguntas controladas sobre despesas oficiais: interpretação restrita + Decimal.

O interpretador NÃO produz SQL, não acessa a Internet e não delega cálculos ao
modelo. Reconhece apenas cinco operações pré-definidas sobre a base validada.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from decimal import Decimal

from services.consulta_oficial import ler_oficiais
from services.siconfi import FUNCOES_CODIGO, UF_IBGE

ANOS = tuple(range(2021, 2026))
FUNCOES = tuple(FUNCOES_CODIGO)
CRITERIO = (
    "Siconfi / RREO, Anexo 02, 6º bimestre: despesas liquidadas acumuladas, "
    "excluídas as intraorçamentárias, referentes aos governos estaduais e ao DF. "
    "Valores nominais declarados, sem auditoria independente."
)


class PerguntaNaoSuportada(ValueError):
    """Pergunta ambígua ou indicador não disponível nesta base."""


class DadosIncompletos(ValueError):
    """Faltam registros necessários para uma conclusão comparável."""


class DadosNaoDisponiveis(RuntimeError):
    """Arquivo oficial ausente ou sem registros."""


def normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(letra for letra in texto if not unicodedata.combining(letra))
    return re.sub(r"\s+", " ", texto.casefold()).strip()


def contem(texto: str, termo: str) -> bool:
    return bool(re.search(r"(?<!\w)" + re.escape(termo) + r"(?!\w)", texto))


_ALIASES = {
    "df": ("distrito federal", "brasilia"),
    "sp": ("sao paulo",),
    "rj": ("rio de janeiro",),
}


def encontrar_ufs(pergunta: str) -> list[str]:
    """Nomes completos aceitam caixa livre; siglas exigem maiúsculas ou contexto.

    Isso impede que conjunções e preposições como 'se', 'am', 'pa', 'ma'
    sejam indevidamente interpretadas como unidades da Federação.
    """
    sem_acentos = normalizar(pergunta)
    trechos: list[tuple[int, int, str]] = []
    nomes = []
    for uf, (_, nome) in UF_IBGE.items():
        for n in (normalizar(nome), *_ALIASES.get(uf.lower(), ())):
            nomes.append((n, uf))
    # Processa primeiro os nomes maiores: "Mato Grosso do Sul" não pode virar MT.
    for nome, uf in sorted(set(nomes), key=lambda x: -len(x[0])):
        for match in re.finditer(r"(?<!\w)" + re.escape(nome) + r"(?!\w)", sem_acentos):
            if any(not (match.end() <= a or match.start() >= b) for a, b, _ in trechos):
                continue
            trechos.append((match.start(), match.end(), uf))
    # Abreviações explícitas, por ex. "SP" ou "DF".
    for match in re.finditer(r"(?<![A-Za-zÀ-ÿ])[A-Z]{2}(?![A-Za-zÀ-ÿ])", pergunta):
        uf = match.group()
        if uf in UF_IBGE:
            trechos.append((match.start(), match.end(), uf))
    # Abreviações em minúsculas após contexto inequívoco ("em sp", "entre sp e go").
    for match in re.finditer(r"\b(?:em|no|na|de|do|da|entre|versus|vs)\s+([a-z]{2})\b", sem_acentos):
        uf = match.group(1).upper()
        if uf in UF_IBGE and uf not in {"SE", "AM", "PA", "MA", "TO", "RO", "AL"}:
            trechos.append((match.start(1), match.end(1), uf))
    return list(dict.fromkeys(uf for _, _, uf in sorted(trechos)))


def encontrar_funcoes(texto: str) -> list[str]:
    aliases = {
        "Educação": ("educacao", "educacional", "ensino"),
        "Saúde": ("saude",),
        "Segurança Pública": ("seguranca publica", "seguranca"),
    }
    resultado = []
    for funcao, termos in aliases.items():
        if any(contem(texto, termo) for termo in termos):
            resultado.append(funcao)
    return resultado


@dataclass(frozen=True)
class ConsultaInterpretada:
    tipo: str
    ano: int
    funcao: str | None
    ufs: tuple[str, ...]
    ano_fim: int | None = None
    direcao: str = "maiores"
    ano_padrao: bool = False
    termo_investiu: bool = False


def interpretar(pergunta: str, ano_referencia: int = 2025) -> ConsultaInterpretada:
    if not pergunta or not pergunta.strip():
        raise PerguntaNaoSuportada("Escreva uma pergunta sobre despesas oficiais.")
    if ano_referencia not in ANOS:
        raise PerguntaNaoSuportada("Selecione um exercício entre 2021 e 2025.")
    texto = normalizar(pergunta)
    if any(contem(texto, termo) for termo in (
        "per capita", "por habitante", "por pessoa", "populacao", "corrigido pela inflacao",
        "valores reais", "descontada a inflacao", "investimento de capital", "despesa de capital",
        "pib", "orcamento inteiro", "orcamento total", "total do orcamento",
        "orcamento geral", "despesa total do governo", "total de despesas do governo",
    )):
        raise PerguntaNaoSuportada(
            "O indicador solicitado não está disponível: a base contém apenas despesas "
            "liquidadas nominais de Educação, Saúde e Segurança Pública, sem população "
            "nem despesa total do orçamento."
        )
    anos = list(dict.fromkeys(int(x) for x in re.findall(r"(?<!\d)20\d{2}(?!\d)", texto)))
    if any(ano not in ANOS for ano in anos):
        raise PerguntaNaoSuportada("A série oficial disponível cobre somente 2021 a 2025.")
    if len(anos) > 2:
        raise PerguntaNaoSuportada("Informe no máximo dois exercícios para delimitar uma série histórica.")
    ufs = encontrar_ufs(pergunta)
    funcoes = encontrar_funcoes(texto)
    participacao = any(p in texto for p in ("participacao", "percentual", "porcentagem", "proporcao", "composicao"))
    comparacao = any(p in texto for p in ("compar", "diferenca", "versus", " vs ", "quem gastou mais entre", "quem gastou menos entre", "quanto a mais", "quanto a menos"))
    evolucao = any(p in texto for p in ("evolu", "serie historica", "historico", "ano a ano", "ao longo", "variacao", "trajetoria", "cresceu", "crescimento")) or (
        len(anos) == 2 and bool(re.search(r"\b(?:entre|de)\s+20\d{2}\s+(?:e|a|ate)\s+20\d{2}", texto))
    )
    ranking = any(p in texto for p in ("ranking", "maior", "menor", "mais gast", "menos gast", "mais invest", "menos invest", "lider", "classific", "quais estados", "quais ufs", "qual estado", "qual uf"))
    if any(contem(texto, termo) for termo in ("em todas as areas", "todas as funcoes")) and not participacao:
        raise PerguntaNaoSuportada("Especifique uma das três funções de governo.")
    if not participacao and len(funcoes) != 1:
        raise PerguntaNaoSuportada(
            "Identifique uma única função: Educação, Saúde ou Segurança Pública. "
            "Para a composição percentual, é possível consultar as três funções."
        )
    if participacao and len(funcoes) > 1 and len(funcoes) != 3:
        raise PerguntaNaoSuportada("Na participação percentual, selecione uma função ou as três funções.")
    if participacao and any(p in texto for p in ("orcamento", "total do estado", "gastos totais", "despesas totais")):
        raise PerguntaNaoSuportada(
            "Não há despesa total orçamentária nesta base; o percentual disponível "
            "usa somente a soma de Educação, Saúde e Segurança Pública."
        )
    if len(ufs) > 2 and not ranking:
        raise PerguntaNaoSuportada("Escolha uma ou duas UFs; rankings consultam todas as 27.")
    if comparacao or (len(ufs) == 2 and not ranking and not participacao):
        tipo = "comparacao"
    elif participacao:
        tipo = "participacao"
    elif evolucao:
        tipo = "evolucao"
    elif ranking and not ufs:
        tipo = "ranking"
    elif len(ufs) == 1:
        tipo = "consulta"
    else:
        raise PerguntaNaoSuportada(
            "Não consegui identificar a consulta. Experimente: 'Qual UF mais gastou com "
            "Educação em 2025?', 'Quanto Goiás gastou com Saúde em 2024?' ou "
            "'Compare SP e BA na Segurança Pública em 2025'."
        )
    if tipo in ("comparacao",) and len(ufs) != 2:
        raise PerguntaNaoSuportada("Para comparar despesas, informe exatamente duas UFs.")
    if tipo in ("consulta", "evolucao", "participacao") and len(ufs) != 1:
        raise PerguntaNaoSuportada("Informe uma única UF para essa consulta.")
    if tipo == "ranking" and ufs:
        raise PerguntaNaoSuportada("O ranking nacional considera as 27 UFs, sem filtro individual.")
    if tipo != "evolucao" and len(anos) == 2:
        raise PerguntaNaoSuportada("Dois anos distintos exigem uma consulta de evolução histórica.")
    if tipo == "evolucao":
        if len(anos) == 2:
            inicio, fim = sorted(anos)
        elif len(anos) == 1:
            inicio, fim = 2021, anos[0]
        else:
            inicio, fim = 2021, 2025
        if inicio >= fim:
            raise PerguntaNaoSuportada("A evolução precisa de pelo menos dois exercícios distintos.")
        return ConsultaInterpretada(
            tipo, inicio, funcoes[0], tuple(ufs), fim,
            ano_padrao=not anos, termo_investiu="invest" in texto,
        )
    return ConsultaInterpretada(
        tipo=tipo, ano=anos[0] if anos else ano_referencia,
        funcao=funcoes[0] if len(funcoes) == 1 else None,
        ufs=tuple(ufs),
        direcao="menores" if any(p in texto for p in ("menos gast", "menor", "menos invest")) else "maiores",
        ano_padrao=not anos, termo_investiu="invest" in texto,
    )


def moeda(valor: Decimal) -> str:
    return "R$ " + f"{valor:,.2f}".replace(",", "§").replace(".", ",").replace("§", ".")


def percentual(valor: Decimal) -> str:
    return f"{valor:.2f}".replace(".", ",") + "%"


def registro_saida(item: dict, *, extra: dict | None = None) -> dict:
    resultado = {
        "uf": item["uf"], "estado": UF_IBGE[item["uf"]][1],
        "ano": item["ano"], "funcao": item["funcao"],
        "valor_reais": item["valor_reais"], "fonte_url": item["fonte_url"],
    }
    if extra:
        resultado.update(extra)
    return resultado


def executar_consulta(consulta: ConsultaInterpretada, *, registros: list[dict] | None = None) -> dict:
    base = ler_oficiais() if registros is None else registros
    if not base:
        raise DadosNaoDisponiveis("A base de despesas oficiais não está disponível.")
    indice = {(r["uf"], r["ano"], r["funcao"]): r for r in base}

    def obter(uf: str, ano: int, funcao: str) -> dict:
        item = indice.get((uf, ano, funcao))
        if item is None:
            raise DadosIncompletos(
                f"Falta dado oficial para {uf}, {ano}, {funcao}. "
                "Não é possível concluir esta consulta sem cobertura completa."
            )
        return item

    fonte_ids: list[str] = []

    def fontes(linhas: list[dict]) -> list[str]:
        return list(dict.fromkeys(r["fonte_url"] for r in linhas if r.get("fonte_url")))

    tipo, ano, funcao = consulta.tipo, consulta.ano, consulta.funcao
    saida: list[dict]
    if tipo == "ranking":
        assert funcao is not None
        linhas = [obter(uf, ano, funcao) for uf in sorted(UF_IBGE)]
        invertido = consulta.direcao == "maiores"
        ordenados = sorted(linhas, key=lambda r: (-(r["valor_reais"]) if invertido else r["valor_reais"], r["uf"]))
        saida = [registro_saida(r, extra={"posicao": i}) for i, r in enumerate(ordenados, 1)]
        primeiro = ordenados[0]
        empatados = [r for r in ordenados if r["valor_reais"] == primeiro["valor_reais"]]
        candidatos = ", ".join(UF_IBGE[r["uf"]][1] + " (" + r["uf"] + ")" for r in empatados)
        qualificacao = "maior" if invertido else "menor"
        resumo = (f"Em {ano}, a {qualificacao} despesa liquidada na função {funcao} foi "
                  f"registrada por {candidatos}, no valor de {moeda(primeiro['valor_reais'])}. "
                  "O ranking considera as 27 UFs e valores nominais, não valores por habitante.")
        fonte_ids = fontes(linhas)
    elif tipo == "consulta":
        assert funcao is not None
        uf = consulta.ufs[0]
        r = obter(uf, ano, funcao)
        saida = [registro_saida(r)]
        resumo = (f"Em {ano}, {UF_IBGE[uf][1]} ({uf}) registrou "
                  f"{moeda(r['valor_reais'])} em despesas liquidadas na função {funcao}.")
        fonte_ids = fontes([r])
    elif tipo == "comparacao":
        assert funcao is not None
        primeira, segunda = consulta.ufs
        a, b = obter(primeira, ano, funcao), obter(segunda, ano, funcao)
        maior, menor = sorted((a, b), key=lambda r: (-r["valor_reais"], r["uf"]))
        diferenca = maior["valor_reais"] - menor["valor_reais"]
        variacao = (diferenca / menor["valor_reais"] * 100) if menor["valor_reais"] else None
        saida = [registro_saida(r) for r in (a, b)]
        resumo = (
            f"Em {ano}, na função {funcao}, {UF_IBGE[a['uf']][1]} ({a['uf']}) registrou "
            f"{moeda(a['valor_reais'])}, e {UF_IBGE[b['uf']][1]} ({b['uf']}), "
            f"{moeda(b['valor_reais'])}. "
            f"A diferença absoluta foi de {moeda(diferenca)}; "
            f"{UF_IBGE[maior['uf']][1]} apresentou o maior valor. "
            + (f"A diferença equivale a {percentual(variacao)} do valor da UF de menor despesa."
               if variacao is not None else "A diferença percentual não é calculável porque a base é zero.")
        )
        fonte_ids = fontes([a, b])
    elif tipo == "evolucao":
        assert funcao is not None and consulta.ano_fim is not None
        uf = consulta.ufs[0]
        linhas = [obter(uf, exercicio, funcao) for exercicio in range(ano, consulta.ano_fim + 1)]
        saida = []
        for pos, r in enumerate(linhas):
            ant = linhas[pos-1]["valor_reais"] if pos else None
            variacao = ((r["valor_reais"] / ant - 1) * 100) if ant is not None and ant != 0 else None
            saida.append(registro_saida(r, extra={"variacao_nominal_percentual": variacao}))
        inicio, fim = linhas[0], linhas[-1]
        diferenca = fim["valor_reais"] - inicio["valor_reais"]
        pct = ((fim["valor_reais"] / inicio["valor_reais"] - 1) * 100) if inicio["valor_reais"] else None
        resumo = (
            f"Em {UF_IBGE[uf][1]} ({uf}), a despesa liquidada na função {funcao} passou "
            f"de {moeda(inicio['valor_reais'])} em {inicio['ano']} para "
            f"{moeda(fim['valor_reais'])} em {fim['ano']}; "
            f"variação nominal de {moeda(diferenca)} "
            + (f"({percentual(pct)})." if pct is not None else
               "(percentual não calculável porque o valor inicial é zero).")
        )
        fonte_ids = fontes(linhas)
    elif tipo == "participacao":
        uf = consulta.ufs[0]
        linhas = [obter(uf, ano, funcao_item) for funcao_item in FUNCOES]
        total = sum((r["valor_reais"] for r in linhas), Decimal("0"))
        if total == 0:
            raise DadosIncompletos("A soma das três funções é zero; não é possível calcular a composição percentual.")
        selecionadas = [r for r in linhas if consulta.funcao is None or r["funcao"] == consulta.funcao]
        saida = [registro_saida(r, extra={"participacao_percentual": r["valor_reais"] / total * 100})
                 for r in selecionadas]
        partes = "; ".join(f"{r['funcao']}: {percentual(r['valor_reais'] / total * 100)}" for r in selecionadas)
        resumo = (
            f"Em {ano}, em {UF_IBGE[uf][1]} ({uf}), a participação no subtotal das três funções "
            f"analisadas foi: {partes}. Subtotal: {moeda(total)}. "
            "Os percentuais NÃO representam participação na despesa total do orçamento."
        )
        fonte_ids = fontes(linhas)
    else:
        raise PerguntaNaoSuportada("Tipo de consulta não implementado.")
    observacoes = []
    if consulta.ano_padrao and tipo != "evolucao":
        observacoes.append(f"O exercício {ano} foi utilizado por padrão porque a pergunta não indicou um ano.")
    if consulta.termo_investiu:
        observacoes.append(
            "A expressão 'investiu' foi interpretada como despesa liquidada na função; "
            "não equivale necessariamente a investimento (despesa de capital)."
        )
    observacoes.append("Os valores não estão corrigidos pela inflação nem divididos pela população.")
    return {
        "tipo": tipo,
        "pergunta_interpretada": f"{tipo} | {funcao or 'três funções'} | {ano}" + (
            f"–{consulta.ano_fim}" if consulta.ano_fim else ""
        ),
        "resposta_calculada": resumo,
        "dados": saida,
        "fontes": fonte_ids,
        "criterio": CRITERIO,
        "observacoes": observacoes,
    }
