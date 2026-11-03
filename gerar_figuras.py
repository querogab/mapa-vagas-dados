"""Gera tabelas e SVGs do recorte harmonizado, sem dependências externas.

Uso: python3 gerar_figuras.py
"""

import csv
import html
from collections import Counter
from pathlib import Path

from harmonizar import BASE, DATA_PROCESSAMENTO


ENTRADA = BASE / "harmonizado" / f"vagas-harmonizadas-{DATA_PROCESSAMENTO}.csv"
SAIDA = BASE / "harmonizado" / "figuras"
FONTES = ("gupy", "linkedin", "remoteok")
FAMILIAS = ("analise_bi", "ciencia_dados", "engenharia_dados", "governanca_qualidade", "ia", "pesquisa_inteligencia")
NOMES_FAMILIA = {
    "analise_bi": "Análise e BI", "ciencia_dados": "Ciência de dados",
    "engenharia_dados": "Engenharia de dados", "governanca_qualidade": "Governança e qualidade",
    "ia": "IA", "pesquisa_inteligencia": "Pesquisa e inteligência",
}
NOMES_FONTE = {"gupy": "Gupy", "linkedin": "LinkedIn", "remoteok": "RemoteOK"}
CORES_FONTE = {"gupy": "#0080ab", "linkedin": "#c8591c", "remoteok": "#7a55c7"}
CORES_FAMILIA = {"analise_bi": "#0080ab", "ciencia_dados": "#35a877", "engenharia_dados": "#d08a10", "governanca_qualidade": "#c9506f", "ia": "#7a55c7", "pesquisa_inteligencia": "#5f7f1a"}
SKILLS = ("SQL", "Python", "Power BI", "Excel", "Cloud", "ETL/ELT", "dbt", "Airflow", "Spark", "Databricks", "IA generativa/LLM")
FAMILIAS_COMPARADAS = ("analise_bi", "ciencia_dados", "engenharia_dados", "ia")
N_PEQUENO = 30


def esc(valor):
    return html.escape(str(valor), quote=True)


def num(valor):
    return f"{valor:,}".replace(",", ".")


def pct(valor):
    return f"{valor:.1f}%".replace(".", ",")


def classe_rotulo(fundo):
    """Escolhe texto claro ou escuro pelo maior contraste com a cor do segmento."""
    canais = [int(fundo[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    r, g, b = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in canais]
    luminancia = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return "l c" if 1.05 / (luminancia + 0.05) >= (luminancia + 0.05) / 0.0689 else "l"


def svg_inicio(largura, altura, titulo, subtitulo):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{largura}" height="{altura}" viewBox="0 0 {largura} {altura}" role="img" aria-label="{esc(titulo)}">
<style>text{{font-family:Arial,sans-serif;fill:#1d2730}}.t{{font-size:24px;font-weight:700}}.s{{font-size:13px;fill:#52606b}}.l{{font-size:12px}}.v{{font-size:12px;font-weight:700}}.n{{font-size:11px;fill:#52606b}}.c{{fill:#ffffff}}</style>
<rect width="100%" height="100%" fill="#fbfcfd"/><text x="34" y="38" class="t">{esc(titulo)}</text><text x="34" y="61" class="s">{esc(subtitulo)}</text>'''


def svg_fim(largura, altura, nota):
    return f'<line x1="34" y1="{altura - 39}" x2="{largura - 34}" y2="{altura - 39}" stroke="#d8dee4"/><text x="34" y="{altura - 18}" class="n">{esc(nota)}</text></svg>'


def escrever_csv(nome, campos, linhas):
    with (SAIDA / nome).open("w", newline="", encoding="utf-8") as arquivo:
        saida = csv.DictWriter(arquivo, fieldnames=campos)
        saida.writeheader()
        saida.writerows(linhas)


def fig_cobertura(tabela):
    largura, altura = 920, 390
    partes = [svg_inicio(largura, altura, "Cobertura e seleção por fonte", "Cada barra representa todos os anúncios do snapshot; a seleção é definida pelo título.")]
    legenda = [("#d7dde3", "Fora do escopo"), ("#f1c57a", "Incluída sem descrição"), ("#0080ab", "Incluída com descrição")]
    for i, (cor, nome) in enumerate(legenda):
        x = 350 + i * 175
        partes.append(f'<rect x="{x}" y="84" width="14" height="14" rx="2" fill="{cor}"/><text x="{x + 20}" y="96" class="l">{nome}</text>')
    inicio_x, largura_barra = 170, 600
    for indice, linha in enumerate(tabela):
        y = 145 + indice * 68
        total = linha["total"]
        segmentos = [(linha["fora_do_escopo"], "#d7dde3"), (linha["incluidas_sem_descricao"], "#f1c57a"), (linha["incluidas_com_descricao"], "#0080ab")]
        partes.append(f'<text x="34" y="{y + 18}" class="l" font-weight="700">{NOMES_FONTE[linha["fonte"]]}</text><text x="34" y="{y + 38}" class="n">N = {num(total)}</text>')
        x = inicio_x
        for quantidade, cor in segmentos:
            largura_segmento = largura_barra * quantidade / total
            if largura_segmento:
                partes.append(f'<rect x="{x:.1f}" y="{y}" width="{max(largura_segmento - 2, 1):.1f}" height="28" fill="{cor}"/>')
            if largura_segmento > 42:
                partes.append(f'<text x="{x + largura_segmento / 2:.1f}" y="{y + 19}" text-anchor="middle" class="{classe_rotulo(cor)}">{num(quantidade)}</text>')
            x += largura_segmento
        partes.append(f'<text x="{inicio_x + largura_barra + 10}" y="{y + 19}" class="v">{num(linha["incluidas"])} incluídas</text>')
    partes.append(svg_fim(largura, altura, "Fonte: snapshots locais processados em 30/10/26. Descrição é condição de observação de competências, não de inclusão."))
    (SAIDA / "01-cobertura-e-selecao.svg").write_text("".join(partes), encoding="utf-8")


def fig_familias(tabela):
    largura, altura = 920, 455
    partes = [svg_inicio(largura, altura, "Composição das vagas incluídas", "Percentuais dentro de cada fonte; famílias são atribuídas por regras explícitas de título.")]
    for i, familia in enumerate(FAMILIAS):
        x = 38 + (i % 3) * 285
        y = 92 + (i // 3) * 24
        partes.append(f'<rect x="{x}" y="{y}" width="13" height="13" rx="2" fill="{CORES_FAMILIA[familia]}"/><text x="{x + 19}" y="{y + 11}" class="l">{NOMES_FAMILIA[familia]}</text>')
    inicio_x, largura_barra = 220, 600
    for indice, fonte in enumerate(FONTES):
        dados = [x for x in tabela if x["fonte"] == fonte]
        total = sum(x["quantidade"] for x in dados)
        mapa = {x["familia"]: x["quantidade"] for x in dados}
        y = 180 + indice * 72
        partes.append(f'<text x="34" y="{y + 18}" class="l" font-weight="700">{NOMES_FONTE[fonte]}</text><text x="34" y="{y + 38}" class="n">N = {num(total)}</text>')
        x = inicio_x
        for familia in FAMILIAS:
            quantidade = mapa.get(familia, 0)
            w = largura_barra * quantidade / total if total else 0
            if w:
                partes.append(f'<rect x="{x:.1f}" y="{y}" width="{max(w - 2, 1):.1f}" height="30" fill="{CORES_FAMILIA[familia]}"/>')
                if w >= 45:
                    partes.append(f'<text x="{x + w / 2:.1f}" y="{y + 20}" text-anchor="middle" class="{classe_rotulo(CORES_FAMILIA[familia])}">{num(quantidade)} · {quantidade / total:.0%}</text>')
            x += w
    partes.append(svg_fim(largura, altura, "A composição não mede participação no mercado: as fontes, países e buscas não têm a mesma cobertura."))
    (SAIDA / "02-composicao-por-familia.svg").write_text("".join(partes), encoding="utf-8")


def fig_skills(tabela):
    largura, altura = 920, 670
    partes = [svg_inicio(largura, altura, "Menções de competências em descrições disponíveis", "Percentual = anúncios incluídos que mencionam a competência / anúncios incluídos com descrição.")]
    inicio_y = 105
    for painel, fonte in enumerate(FONTES):
        itens = [x for x in tabela if x["fonte"] == fonte]
        denominador = itens[0]["denominador_descricao"] if itens else 0
        base_y = inicio_y + painel * 167
        partes.append(f'<text x="34" y="{base_y}" class="v">{NOMES_FONTE[fonte]} <tspan class="n">N com descrição = {denominador}</tspan></text>')
        for indice, item in enumerate(itens):
            y = base_y + 16 + indice * 12
            percentual = item["percentual"]
            w = 510 * percentual / 100
            partes.append(f'<text x="34" y="{y + 9}" class="n">{esc(item["skill"])}</text><rect x="165" y="{y}" width="510" height="9" fill="#e7ebee"/><rect x="165" y="{y}" width="{w:.1f}" height="9" fill="{CORES_FONTE[fonte]}"/><text x="690" y="{y + 9}" class="n">{item["quantidade"]}/{denominador} · {pct(percentual)}</text>')
    partes.append(svg_fim(largura, altura, "Ausência de menção não equivale a ausência da competência. LinkedIn tem descrição em subconjunto das vagas incluídas."))
    (SAIDA / "03-mencoes-de-competencias.svg").write_text("".join(partes), encoding="utf-8")


def fig_por_familia(tabela):
    largura, altura = 920, 548
    partes = [svg_inicio(largura, altura, "O agregado esconde a diferença entre famílias", "Menções entre vagas incluídas com descrição. Gupy cobre só o Brasil; no LinkedIn, há texto apenas de BR, PT e CA.")]
    for i, fonte in enumerate(("gupy", "linkedin")):
        x = 34 + i * 90
        partes.append(f'<rect x="{x}" y="84" width="13" height="13" rx="2" fill="{CORES_FONTE[fonte]}"/><text x="{x + 19}" y="95" class="l">{NOMES_FONTE[fonte]}</text>')
    colunas = {"SQL": 110, "Python": 510}
    largura_barra = 190
    for skill, x in colunas.items():
        partes.append(f'<text x="{x}" y="129" class="v">{skill}</text>')
    linhas = [("todas", "Todas as famílias incluídas")] + [(f, NOMES_FAMILIA[f]) for f in FAMILIAS_COMPARADAS]
    for indice, (familia, rotulo) in enumerate(linhas):
        y = 152 + indice * 66
        partes.append(f'<text x="34" y="{y}" class="l" font-weight="700">{esc(rotulo)}</text>')
        if indice == 1:
            partes.append(f'<line x1="34" y1="{y - 19}" x2="{largura - 34}" y2="{y - 19}" stroke="#d8dee4"/>')
        for j, fonte in enumerate(("gupy", "linkedin")):
            base = y + 9 + j * 18
            partes.append(f'<text x="34" y="{base + 10}" class="n">{NOMES_FONTE[fonte]}</text>')
            for skill, x in colunas.items():
                item = next(l for l in tabela if l["familia"] == familia and l["fonte"] == fonte and l["skill"] == skill)
                n, denominador = item["quantidade"], item["denominador_descricao"]
                if not denominador:
                    partes.append(f'<text x="{x}" y="{base + 10}" class="n">sem descrição no snapshot (0/{item["incluidas"]})</text>')
                    continue
                opacidade = ' opacity="0.45"' if denominador < N_PEQUENO else ""
                partes.append(f'<rect x="{x}" y="{base}" width="{largura_barra}" height="11" fill="#e7ebee"/><rect x="{x}" y="{base}" width="{largura_barra * n / denominador:.1f}" height="11" fill="{CORES_FONTE[fonte]}"{opacidade}><title>{NOMES_FONTE[fonte]}, {esc(rotulo)}, {skill}: {n}/{denominador}</title></rect>')
                partes.append(f'<text x="{x + largura_barra + 8}" y="{base + 10}" class="n">{pct(item["percentual"])} · {num(n)}/{num(denominador)}</text>')
    partes.append(svg_fim(largura, altura, f"Barra clara: menos de {N_PEQUENO} descrições. Governança e Pesquisa ficam de fora porque não têm descrição no LinkedIn. Menção não é requisito."))
    (SAIDA / "04-sql-python-por-familia.svg").write_text("".join(partes), encoding="utf-8")


def calcular_tabelas():
    linhas = list(csv.DictReader(ENTRADA.open(encoding="utf-8")))
    incluidas = [l for l in linhas if l["incluida_no_recorte"] == "true"]

    cobertura = []
    for fonte in FONTES:
        todas = [l for l in linhas if l["fonte"] == fonte]
        recorte = [l for l in incluidas if l["fonte"] == fonte]
        com_texto = [l for l in recorte if l["descricao_disponivel"] == "true"]
        cobertura.append({"fonte": fonte, "total": len(todas), "incluidas": len(recorte), "fora_do_escopo": len(todas) - len(recorte), "incluidas_com_descricao": len(com_texto), "incluidas_sem_descricao": len(recorte) - len(com_texto), "descricao_truncada": sum(l["descricao_truncada"] == "true" for l in com_texto)})
    escrever_csv("tabela-cobertura.csv", list(cobertura[0]), cobertura)

    familias = []
    for fonte in FONTES:
        contagem = Counter(l["familia_harmonizada"] for l in incluidas if l["fonte"] == fonte)
        for familia in FAMILIAS:
            familias.append({"fonte": fonte, "familia": familia, "rotulo": NOMES_FAMILIA[familia], "quantidade": contagem[familia]})
    escrever_csv("tabela-familias.csv", list(familias[0]), familias)

    competencias = []
    for fonte in FONTES:
        base = [l for l in incluidas if l["fonte"] == fonte and l["descricao_disponivel"] == "true"]
        for skill in SKILLS:
            quantidade = sum(skill in l["skills_mencionadas"].split(";") for l in base)
            competencias.append({"fonte": fonte, "skill": skill, "quantidade": quantidade, "denominador_descricao": len(base), "percentual": round(100 * quantidade / len(base), 1) if base else 0})
    escrever_csv("tabela-competencias.csv", list(competencias[0]), competencias)

    por_familia = []
    for familia in ("todas",) + FAMILIAS_COMPARADAS:
        for fonte in ("gupy", "linkedin"):
            recorte = [l for l in incluidas if l["fonte"] == fonte and (familia == "todas" or l["familia_harmonizada"] == familia)]
            base = [l for l in recorte if l["descricao_disponivel"] == "true"]
            for skill in ("SQL", "Python"):
                quantidade = sum(skill in l["skills_mencionadas"].split(";") for l in base)
                por_familia.append({"familia": familia, "fonte": fonte, "skill": skill, "quantidade": quantidade, "denominador_descricao": len(base), "incluidas": len(recorte), "percentual": round(100 * quantidade / len(base), 1) if base else ""})
    escrever_csv("tabela-sql-python-por-familia.csv", list(por_familia[0]), por_familia)

    return cobertura, familias, competencias, por_familia


def ler_tabela(nome, inteiros=(), decimais=()):
    linhas = list(csv.DictReader((SAIDA / nome).open(encoding="utf-8")))
    for linha in linhas:
        for campo in inteiros:
            linha[campo] = int(linha[campo])
        for campo in decimais:
            linha[campo] = float(linha[campo]) if linha[campo] else ""
    return linhas


def ler_tabelas():
    """Sem a base linha a linha, que não é pública, as figuras saem das tabelas agregadas."""
    return (
        ler_tabela("tabela-cobertura.csv", ("total", "incluidas", "fora_do_escopo", "incluidas_com_descricao", "incluidas_sem_descricao", "descricao_truncada")),
        ler_tabela("tabela-familias.csv", ("quantidade",)),
        ler_tabela("tabela-competencias.csv", ("quantidade", "denominador_descricao"), ("percentual",)),
        ler_tabela("tabela-sql-python-por-familia.csv", ("quantidade", "denominador_descricao", "incluidas"), ("percentual",)),
    )


def main():
    SAIDA.mkdir(exist_ok=True)
    cobertura, familias, competencias, por_familia = calcular_tabelas() if ENTRADA.exists() else ler_tabelas()

    fig_cobertura(cobertura)
    fig_familias(familias)
    fig_skills(competencias)
    fig_por_familia(por_familia)
    (SAIDA / "LEIA-ME.md").write_text("\n".join([
        "# Tabelas e figuras do Mapa de vagas", "",
        f"Geradas em {DATA_PROCESSAMENTO} por `gerar_figuras.py`, a partir de `vagas-harmonizadas-{DATA_PROCESSAMENTO}.csv`.",
        "", "## Artefatos", "",
        "- `01-cobertura-e-selecao.svg`: cobertura, inclusão e descrição por fonte.",
        "- `02-composicao-por-familia.svg`: composição percentual somente das vagas incluídas.",
        "- `03-mencoes-de-competencias.svg`: menções literais somente entre vagas incluídas com descrição disponível.",
        "- `04-sql-python-por-familia.svg`: SQL e Python por família em Gupy e LinkedIn, com o agregado em cima; família sem descrição aparece como tal, não como zero.",
        "- `tabela-*.csv`: valores usados nos SVGs.",
        "", "## Limites", "",
        "- Fontes não são amostras comparáveis do mercado e não houve deduplicação semântica entre elas.",
        "- LinkedIn não tem descrição em parte relevante das vagas; nenhuma célula sem texto deve ser lida como zero competência.",
        "- RemoteOK identifica um canal remoto, não contrato, país confirmado ou elegibilidade global.",
        "- As famílias decorrem de regras de título; competências são menções literais no texto, não requisitos confirmados.", "",
    ]), encoding="utf-8")
    print(f"Figuras e tabelas: {SAIDA}")


if __name__ == "__main__":
    main()
