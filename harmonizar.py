"""Harmoniza os snapshots Gupy, LinkedIn e RemoteOK sem alterar os originais.

Uso: python3 harmonizar.py

Gera `harmonizado/vagas-harmonizadas-2026-10-30.csv` e o relatório associado.
Os campos derivados não substituem classificações históricas: cada linha conserva
fonte, identificador e data do snapshot para permitir auditoria por anúncio.
"""

import csv
import html
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path


BASE = Path(__file__).resolve().parent
BRUTOS = BASE / "brutos"
SAIDA = BASE / "harmonizado"
DATA_PROCESSAMENTO = "2026-10-30"
GUPY_COLETA = date(2026, 9, 26)
GUPY_CORTE = "2026-06-28"  # 90 dias antes da coleta, sem depender do relógio atual.


FAMILIAS = [
    ("engenharia_dados", r"\bdata engineer\b|\banalytics engineer\b|\bengineer,? data (?:&|and) analytics\b|engenheir[oa](?:\(a\))?\w*(?: de)? dados|engenheir[oa](?:\(a\))?\w* de analytics|ingenier[oa] de datos|ing[eé]nieur(?:e|\(e\))?(?: de(?:s)?)? donn[eé]es|ing[eé]nierie de donn[eé]es|\bdataops\b|arquitet\w* de dados"),
    ("ciencia_dados", r"\bdata scientist\b|cientista de dados|cient[ií]fic[oa] de datos|scientifique des donn[eé]es|science des donn[eé]es|\bmachine learning\b|\bml engineer\b|engenheir[oa]\w* de (?:machine )?(?:deep )?learning|\bestat[ií]stic[oa]\b"),
    ("analise_bi", r"\bdata analyst\b|analista de dados|analista de datos|especialista (?:de|em) dados|analista de bi\b|\banalyste bi\b|\bbusiness intelligence\b|\bbusiness analytics\b|\bbi analyst\b|inteligencia de negocios|intelligence d['’]affaires|\bpower\s*bi\b|analista de indicadores|analista de dados gerenciais"),
    ("ia", r"\bai engineer\b|engenheir[oa]\w* de ia|intelig[eê]ncia artificial|\bgenerative ai\b|\bai\b|\bia generativa\b|\bia\b"),
    ("pesquisa_inteligencia", r"analista de pesquisa|intelig[eê]ncia de mercado|\bmarket intelligence\b|\bpeople analytics\b|\bhr analytics\b|monitoramento e avalia[cç][aã]o|avalia[cç][aã]o de impacto"),
    ("governanca_qualidade", r"governan[cç]a de dados|qualidade de dados|\bdata governance\b|\bdata quality\b|\bdata steward\b|\bmdm\b"),
]
EXCLUIR_TITULO = re.compile(
    r"\bdata entry\b|\bdata annotator\b|\bannota[cç][aã]o\b|camareir|atendimento|customer success|"
    r"\bhuman resources\b|business development|diretor de arte|suporte\b|\badvpl\b|monitor pedag[oó]gico|"
    r"freelance.*(?:grabaci|tareas cotidianas)|\bai trainer\b",
    re.I,
)
NIVEIS = [
    ("junior", r"\bjunior\b|\bj[uú]nior\b|\bjr\.?\b"),
    ("pleno", r"\bpleno\b|\bpl\.?\b|\bmid[ -]?level\b"),
    ("senior", r"\bsenior\b|\bs[eê]nior\b|\bsr\.?\b|\blead\b|\bstaff\b|\bprincipal\b|especialista"),
    ("gestao", r"\bhead\b|\bmanager\b|\bgerente\b|\bcoordenador\w*\b|\bdiretor\w*\b"),
]
SKILLS = {
    "SQL": r"\bsql\b",
    "Python": r"\bpython\b|\bpandas\b|\bnumpy\b|\bscikit(?:-learn)?\b",
    "Power BI": r"\bpower\s*bi\b|\bpowerbi\b",
    "Excel": r"\bexcel\b",
    "Cloud": r"\baws\b|\bgcp\b|\bazure\b|\bgoogle cloud\b|\bbigquery\b|\bsnowflake\b",
    "ETL/ELT": r"\betl\b|\belt\b",
    "dbt": r"\bdbt\b",
    "Airflow": r"\bairflow\b",
    "Spark": r"\bspark\b|\bpyspark\b",
    "Databricks": r"\bdatabricks\b",
    "IA generativa/LLM": r"\bllms?\b|\bgpt\b|generativ\w*|\blangchain\b|\bprompt\w*\b",
}


def texto(valor):
    """Remove HTML e normaliza espaços sem modificar o snapshot em disco."""
    valor = html.unescape(valor or "")
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", valor)).strip()


def familia(titulo):
    if EXCLUIR_TITULO.search(titulo):
        return "fora_do_escopo"
    for nome, padrao in FAMILIAS:
        if re.search(padrao, titulo, re.I):
            return nome
    return "fora_do_escopo"


def nivel(titulo):
    for nome, padrao in NIVEIS:
        if re.search(padrao, titulo, re.I):
            return nome
    return "nao_informado"


def skills(descricao):
    return ";".join(nome for nome, padrao in SKILLS.items() if re.search(padrao, descricao, re.I))


def truncado(descricao, limite):
    return bool(descricao and len(descricao) >= limite)


def linha_base(fonte, registro_id, titulo, empresa, descricao, publicada, pais, confianca_pais,
               modelo, confianca_modelo, snapshot, texto_truncado, tipo_contrato=""):
    titulo = texto(titulo)
    descricao = texto(descricao)
    familia_derivada = familia(titulo)
    return {
        "fonte": fonte,
        "id_origem": str(registro_id),
        "snapshot": snapshot,
        "titulo": titulo,
        "empresa": texto(empresa),
        "publicada": str(publicada or "")[:10],
        "pais": pais,
        "confianca_pais": confianca_pais,
        "modelo_trabalho": modelo,
        "confianca_modelo": confianca_modelo,
        "tipo_contrato_origem": tipo_contrato,
        "descricao_disponivel": str(bool(descricao)).lower(),
        "descricao_truncada": str(texto_truncado).lower(),
        "familia_harmonizada": familia_derivada,
        "incluida_no_recorte": str(familia_derivada != "fora_do_escopo").lower(),
        "nivel_harmonizado": nivel(titulo),
        "skills_mencionadas": skills(descricao),
    }


def carregar_gupy():
    bruto = json.loads((BASE / "gupy-bruto-2026-09-26.json").read_text(encoding="utf-8"))["vagas"]
    saida = []
    tipos = {"vacancy_type_effective", "vacancy_legal_entity", "vacancy_temporary"}
    for vaga in bruto:
        publicada = vaga["publishedDate"][:10]
        if publicada < GUPY_CORTE or vaga.get("type") not in tipos:
            continue
        saida.append(linha_base(
            "gupy", vaga["id"], vaga.get("name"), vaga.get("careerPageName"), vaga.get("description"),
            publicada, "BR", "metadata_da_fonte", vaga.get("workplaceType") or "nao_informado",
            "metadata_da_fonte", "gupy-bruto-2026-09-26.json", False, vaga.get("type", ""),
        ))
    return saida


def carregar_linkedin():
    fundido = json.loads((BRUTOS / "vagas-fundidas-2026-10-07-enriquecido.json").read_text(encoding="utf-8"))["vagas"]
    saida = []
    for vaga in fundido:
        if vaga.get("fonte") != "linkedin":
            continue
        descricao = vaga.get("descricao_bruta") or ""
        saida.append(linha_base(
            "linkedin", vaga["id"], vaga.get("titulo"), vaga.get("empresa"), descricao,
            vaga.get("data_publicacao"), vaga.get("pais") or "nao_informado", "pais_da_busca_linkedin",
            "nao_capturado", "nao_disponivel", "vagas-fundidas-2026-10-07-enriquecido.json",
            truncado(descricao, 3000), "",
        ))
    return saida


def carregar_remoteok():
    bruto = json.loads((BRUTOS / "remoteok-2026-10-07.json").read_text(encoding="utf-8"))["vagas"]
    saida = []
    for vaga in bruto:
        descricao = vaga.get("descricao_bruta") or ""
        saida.append(linha_base(
            "remoteok", vaga["id"], vaga.get("titulo"), vaga.get("empresa"), descricao,
            vaga.get("data_publicacao"), vaga.get("pais") or "nao_informado", "inferido_pelo_coletor",
            "canal_remoto", "propriedade_do_canal", "remoteok-2026-10-07.json",
            truncado(descricao, 3000), vaga.get("tipo_contrato", ""),
        ))
    return saida


def validar():
    assert familia("Pessoa Engenheira de Dados Sênior") == "engenharia_dados"
    assert familia("Engenheiro Dados Especialista") == "engenharia_dados"
    assert familia("Engenheiro(a) de Dados Sênior") == "engenharia_dados"
    assert familia("Ingénierie de données") == "engenharia_dados"
    assert familia("Ingénieur des données") == "engenharia_dados"
    assert familia("Ingénieur(e) de données, Placements") == "engenharia_dados"
    assert familia("Power BI Developer") == "analise_bi"
    assert familia("Sr. Power BI/Qlick Developer") == "analise_bi"
    assert familia("Senior Power BI /Dashboard UI Specialist") == "analise_bi"
    assert familia("Analyste BI senior") == "analise_bi"
    assert familia("Analista de datos") == "analise_bi"
    assert familia("Especialista de Dados - RH") == "analise_bi"
    assert familia("Especialista em Dados e BI") == "analise_bi"
    assert familia("Senior Business Analytics Lead") == "analise_bi"
    assert familia("Développeur, système d'intelligence d'affaires BI") == "analise_bi"
    assert familia("Engenheiro de Machine Deep Learning Pleno") == "ciencia_dados"
    assert familia("Founding ML Engineer") == "ciencia_dados"
    assert familia("Software Engineer (Machine Learning)") == "ciencia_dados"
    assert familia("Analista Júnior de Automação com IA e Agentes") == "ia"
    assert familia("Senior AI/ML Applied Scientist") == "ia"
    assert familia("Científico de datos") == "ciencia_dados"
    assert familia("HR Analytics") == "pesquisa_inteligencia"
    assert familia("Senior Data Steward, Master Data") == "governanca_qualidade"
    assert familia("Camareira de Hotel") == "fora_do_escopo"
    assert familia("Freelance grabación de tareas cotidianas para proyecto de IA") == "fora_do_escopo"
    assert familia("Generalist AI Trainer") == "fora_do_escopo"
    assert nivel("Pessoa Engenheira de Dados Sênior | Projeto Internacional") == "senior"
    assert nivel("Engenheiro Dados Especialista") == "senior"
    assert nivel("Analista Educacional Sr. | Designer de Aprendizagem") == "senior"
    assert "Excel" not in skills("excelência operacional")
    assert "Excel" in skills("Excel avançado")


def relatorio(linhas, excluidas):
    por_fonte = Counter(l["fonte"] for l in linhas)
    cobertura = Counter((l["fonte"], l["descricao_disponivel"]) for l in linhas)
    familias = Counter((l["fonte"], l["familia_harmonizada"]) for l in linhas)
    niveis = Counter(
        (l["fonte"], l["nivel_harmonizado"])
        for l in linhas if l["incluida_no_recorte"] == "true"
    )
    texto_saida = [
        "# Relatório da harmonização de vagas",
        "",
        f"> Processado em {DATA_PROCESSAMENTO}, sem chamadas de rede. Os snapshots de origem não foram alterados.",
        "",
        "## Contrato do conjunto",
        "",
        "- Uma linha por `fonte` + `id_origem`, sem deduplicação semântica entre plataformas.",
        "- Inclusão pelo título em taxonomia comum; anúncios `fora_do_escopo` ficam registrados no CSV com essa marca e não entram nos agregados substantivos.",
        "- Competências são menções em texto disponível, não requisitos obrigatórios. Texto truncado e ausência de descrição são atributos explícitos.",
        "- Gupy conserva tipos efetiva/PJ/temporária e janela de 90 dias antes da coleta (28/06/26 a 26/09/26): são 1.022 registros antes da taxonomia comum. O recorte histórico de 752 aplicava regras anteriores de família/processos e é preservado, não substituído.",
        "- LinkedIn usa o país da busca, não confirmação de elegibilidade ou local de trabalho. RemoteOK conserva país inferido pelo coletor e canal remoto, sem equivaler isso a modalidade/contrato da vaga.",
        "",
        "## Contagens",
        "",
        "| Fonte | Linhas | Com descrição | Sem descrição | Fora do escopo |",
        "|---|---:|---:|---:|---:|",
    ]
    for fonte in ("gupy", "linkedin", "remoteok"):
        sub = [l for l in linhas if l["fonte"] == fonte]
        texto_saida.append(
            f"| {fonte} | {len(sub)} | {cobertura[fonte, 'true']} | {cobertura[fonte, 'false']} | {excluidas[fonte]} |"
        )
    texto_saida.extend(["", "## Famílias incluídas", "", "| Fonte | Família | Linhas |", "|---|---|---:|"])
    for (fonte, nome), quantidade in sorted(familias.items()):
        if nome != "fora_do_escopo":
            texto_saida.append(f"| {fonte} | {nome} | {quantidade} |")
    texto_saida.extend(["", "## Senioridade derivada das linhas incluídas", "", "| Fonte | Nível | Linhas |", "|---|---|---:|"])
    for (fonte, nome), quantidade in sorted(niveis.items()):
        if nome != "nao_informado":
            texto_saida.append(f"| {fonte} | {nome} | {quantidade} |")
    texto_saida.extend([
        "",
        "## Artefatos analíticos",
        "",
        "A amostra estratificada foi concluída em `amostra-validacao-2026-10-30.md`. Tabelas e SVGs reprodutíveis estão em `figuras/`; comparações de competências usam apenas linhas incluídas com descrição disponível e expõem esse denominador.",
        "",
    ])
    return "\n".join(texto_saida)


def main():
    validar()
    linhas = carregar_gupy() + carregar_linkedin() + carregar_remoteok()
    assert len(linhas) == len({(l["fonte"], l["id_origem"]) for l in linhas})
    linhas.sort(key=lambda l: (l["fonte"], l["id_origem"]))
    excluidas = Counter(l["fonte"] for l in linhas if l["familia_harmonizada"] == "fora_do_escopo")
    SAIDA.mkdir(exist_ok=True)
    campos = list(linhas[0])
    csv_path = SAIDA / f"vagas-harmonizadas-{DATA_PROCESSAMENTO}.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as arquivo:
        escrita = csv.DictWriter(arquivo, fieldnames=campos)
        escrita.writeheader()
        escrita.writerows(linhas)
    (SAIDA / f"relatorio-harmonizacao-{DATA_PROCESSAMENTO}.md").write_text(
        relatorio(linhas, excluidas), encoding="utf-8"
    )
    print(f"Linhas: {len(linhas)} | incluídas: {len(linhas) - sum(excluidas.values())} | fora do escopo: {sum(excluidas.values())}")
    print(f"CSV: {csv_path}")


if __name__ == "__main__":
    main()
