"""Gera amostra diagnóstica determinística para revisar a base harmonizada.

Uso: python3 validar_amostra.py

Seleciona uma linha por fonte/família incluída e três exclusões por fonte.
Não estima taxa de erro: torna regras e cobertura auditáveis antes dos gráficos.
"""

import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

from harmonizar import BASE, BRUTOS, DATA_PROCESSAMENTO, texto


SAIDA = BASE / "harmonizado"
CSV = SAIDA / f"vagas-harmonizadas-{DATA_PROCESSAMENTO}.csv"


def descricao_por_origem():
    descricoes = {}
    for vaga in json.loads((BASE / "gupy-bruto-2026-09-26.json").read_text(encoding="utf-8"))["vagas"]:
        descricoes[("gupy", str(vaga["id"]))] = texto(vaga.get("description"))
    for vaga in json.loads((BRUTOS / "vagas-fundidas-2026-10-07-enriquecido.json").read_text(encoding="utf-8"))["vagas"]:
        if vaga.get("fonte") == "linkedin":
            descricoes[("linkedin", str(vaga["id"]))] = texto(vaga.get("descricao_bruta"))
    for vaga in json.loads((BRUTOS / "remoteok-2026-10-07.json").read_text(encoding="utf-8"))["vagas"]:
        descricoes[("remoteok", str(vaga["id"]))] = texto(vaga.get("descricao_bruta"))
    return descricoes


def ordem_estavel(linha):
    chave = f"amostra-2026-10-30|{linha['fonte']}|{linha['id_origem']}"
    return hashlib.sha256(chave.encode()).hexdigest()


def linha_markdown(numero, linha, descricao):
    habilidades = linha["skills_mencionadas"] or "nenhuma"
    trecho = descricao[:500] if descricao else "[descrição não disponível no snapshot]"
    return "\n".join([
        f"### A{numero:02d} — {linha['fonte']} · {linha['familia_harmonizada']}",
        "",
        f"- **ID:** `{linha['id_origem']}` · **snapshot:** `{linha['snapshot']}`",
        f"- **Título:** {linha['titulo']}",
        f"- **Empresa:** {linha['empresa'] or '[não informada]' } · **publicada:** {linha['publicada'] or '[não informada]' }",
        f"- **Derivado:** inclusão `{linha['incluida_no_recorte']}` · família `{linha['familia_harmonizada']}` · nível `{linha['nivel_harmonizado']}` · skills `{habilidades}`",
        f"- **Cobertura:** descrição `{linha['descricao_disponivel']}` · truncada `{linha['descricao_truncada']}` · país `{linha['pais']}`/{linha['confianca_pais']}",
        f"- **Trecho para leitura:** {trecho}",
        "",
    ])


def main():
    linhas = list(csv.DictReader(CSV.open(encoding="utf-8")))
    descricoes = descricao_por_origem()
    estratos = defaultdict(list)
    for linha in linhas:
        chave = (linha["fonte"], linha["familia_harmonizada"])
        estratos[chave].append(linha)

    selecionadas = []
    for fonte in ("gupy", "linkedin", "remoteok"):
        for (origem, familia), itens in sorted(estratos.items()):
            if origem == fonte and familia != "fora_do_escopo":
                selecionadas.append(min(itens, key=ordem_estavel))
        exclusoes = estratos[(fonte, "fora_do_escopo")]
        selecionadas.extend(sorted(exclusoes, key=ordem_estavel)[:3])

    cabecalho = [
        "# Amostra estratificada para validação da harmonização",
        "",
        f"> Gerada em {DATA_PROCESSAMENTO}, sem rede, a partir do CSV harmonizado e dos snapshots de origem.",
        "",
        "## Desenho",
        "",
        "- Uma linha por estrato fonte × família incluída; três exclusões por fonte.",
        "- Seleção determinística por hash do par fonte + ID. A amostra diagnostica regras; não estima taxa de erro ou representatividade do mercado.",
        "- Revisar: (1) o título sustenta inclusão/exclusão, (2) a família, (3) senioridade, (4) skills diante do trecho e (5) cobertura/proveniência.",
        "- Descrição ausente é achado de cobertura, não falha de habilidade. Trechos são somente para auditoria interna e não são candidatos automáticos a publicação.",
        "",
        "## Resultado da revisão",
        "",
        "Revisão iterativa realizada em 30/10/26. A leitura dos estratos encontrou e corrigiu formas técnicas em português, inglês, espanhol e francês, além de excluir tarefas avulsas de anotação/treinamento de IA. A seleção atual é o artefato rastreável da rodada final, não uma estimativa de taxa de erro.",
        "",
        "Decisão conservadora mantida: títulos genéricos sem marcador técnico, como `Senior Analyst`, ficam fora do recorte mesmo quando a descrição disponível sugere análise de dados. Promovê-los exigiria classificar pela descrição, cuja cobertura é desigual no LinkedIn. Competências significam menção literal na descrição, não proficiência comprovada.",
        "",
        "## Itens selecionados",
        "",
    ]
    corpo = []
    for numero, linha in enumerate(selecionadas, 1):
        corpo.append(linha_markdown(numero, linha, descricoes.get((linha["fonte"], linha["id_origem"]), "")))
    destino = SAIDA / f"amostra-validacao-{DATA_PROCESSAMENTO}.md"
    destino.write_text("\n".join(cabecalho + corpo), encoding="utf-8")
    print(f"Amostra: {len(selecionadas)} itens em {destino}")


if __name__ == "__main__":
    main()
