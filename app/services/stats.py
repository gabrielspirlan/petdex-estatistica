import pandas as pd
from statistics import mean, stdev
from scipy.stats import skew, norm
import numpy as np
import scipy.stats as stats
from typing import List, Dict
from datetime import datetime, timedelta, timezone, date

def calcular_estatisticas(dados: List[dict]) -> dict:
    df = pd.DataFrame(dados)
    df["frequenciaMedia"] = pd.to_numeric(df["frequenciaMedia"], errors="coerce")
    valores = df["frequenciaMedia"].dropna()
    valores = valores[(valores >= 30) & (valores <= 200)]
    print(f"Total bruto: {len(df)} | Após filtro de faixa: {len(valores)}")

    media = valores.mean()
    desvio = valores.std()

    if desvio > 0:
        limite_inferior = media - 3 * desvio
        limite_superior = media + 3 * desvio
        valores = valores[(valores >= limite_inferior) & (valores <= limite_superior)]

    if valores.empty:
        return {
            "media": None,
            "mediana": None,
            "moda": None,
            "desvio_padrao": None,
            "assimetria": None
        }

    return {
        "media": float(valores.mean()),
        "mediana": float(valores.median()),
        "moda": float(valores.mode().iloc[0]) if not valores.mode().empty else None,
        "desvio_padrao": float(valores.std()),
        "assimetria": float(skew(valores, bias=False))
        
    }

def media_por_intervalo(dados: List[dict], inicio: date, fim: date) -> Dict:
    if not dados:
        return {"media": None, "mensagem": "Nenhum dado disponível."}

    df = pd.DataFrame(dados)

    if 'data' not in df.columns or 'frequenciaMedia' not in df.columns:
        return {"media": None, "mensagem": "Colunas esperadas não encontradas."}

    df['data'] = pd.to_datetime(df['data'], errors='coerce').dt.date
    df['frequenciaMedia'] = pd.to_numeric(df['frequenciaMedia'], errors='coerce')

    df = df.dropna(subset=['data', 'frequenciaMedia'])

    df_filtrado = df[(df['data'] >= inicio) & (df['data'] <= fim)]

    if df_filtrado.empty:
        return {"media": None, "mensagem": "Nenhum dado encontrado para o intervalo fornecido."}

    media = df_filtrado['frequenciaMedia'].mean().round(2)
    return {"media": media}


def calcular_probabilidade(valor: int, dados: list):
    valores_validos = [v for v in dados if isinstance(v, (int, float)) and 30 <= v <= 200]

    if not valores_validos:
        return {
            "erro": "Não há dados suficientes dentro da faixa fisiológica (30 a 200 BPM) para análise."
        }

    media = np.mean(valores_validos)
    desvio = np.std(valores_validos)

    if valor < 30 or valor > 250:
        return {
            "valor_informado": valor,
            "media_registrada": round(media, 2),
            "desvio_padrao": round(desvio, 2),
            "titulo": "Valor fora da faixa ❌",
            "avaliacao": "O valor informado está fora da faixa fisiológica plausível para cães e gatos (30 a 200 BPM)."
        }

    z = abs((valor - media) / desvio)
    prob = (1 - norm.cdf(z)) * 2 * 100

    if z < 1:
        classificacao = "Dentro do esperado"
        titulo = "Batimento esperado ✅"
        interpretacao = (
            f"O valor de {valor} BPM está dentro do comportamento normal observado nos últimos dias. "
            f"A chance de ocorrer é alta ({round(prob, 2)}%)."
        )
    elif z < 2:
        classificacao = "Ligeiramente incomum"
        titulo = "Batimento um pouco fora do comum ⚠️"
        interpretacao = (
            f"O valor de {valor} BPM é um pouco diferente da média recente. "
            f"A chance de ocorrer é de aproximadamente {round(prob, 2)}%. Não necessariamente é preocupante, mas vale observar."
        )
    elif z < 3:
        classificacao = "Incomum"
        titulo = "Batimento incomum ❗"
        interpretacao = (
            f"O valor de {valor} BPM é estatisticamente incomum com base nos últimos 5 dias. "
            f"A chance de isso ocorrer naturalmente é de apenas {round(prob, 2)}%. Pode representar agitação, estresse ou outra condição fisiológica fora do padrão."
        )
    else:
        classificacao = "Raro ou fora do padrão"
        titulo = "Batimento raro ou atípico 🚨"
        interpretacao = (
            f"O valor de {valor} BPM é muito raro com base nos dados recentes. "
            f"A chance de ocorrer é de apenas {round(prob, 2)}%. Isso pode indicar uma situação atípica, erro na medição ou necessidade de atenção veterinária se persistir."
        )

    return {
        "valor_informado": valor,
        "media_registrada": round(media, 2),
        "desvio_padrao": round(desvio, 2),
        "probabilidade_percentual": round(prob, 2),
        "classificacao": classificacao,
        "titulo": titulo,
        "interpretacao": interpretacao,
        "avaliacao": interpretacao
    }

def media_ultimos_5_dias_validos(dados: List[dict]) -> dict:
    df = pd.DataFrame(dados)

    if 'data' not in df.columns or 'frequenciaMedia' not in df.columns:
        print("Colunas esperadas não encontradas. Colunas disponíveis:", df.columns.tolist())
        return {}

    df['data'] = pd.to_datetime(df['data'], errors='coerce').dt.date
    df['frequenciaMedia'] = pd.to_numeric(df['frequenciaMedia'], errors='coerce')

    df = df.dropna(subset=['data', 'frequenciaMedia'])

    medias_por_dia = df.groupby('data')['frequenciaMedia'].mean().round(2)

    ultimos_5_dias = medias_por_dia.sort_index(ascending=False).head(5)

    return ultimos_5_dias.sort_index().to_dict()

def media_ultimas_5_horas_registradas(dados: List[dict]) -> dict:
    df = pd.DataFrame(dados)
    if df.empty:
        return {"media": None, "media_por_hora": {}, "mensagem": "Nenhum dado disponível."}

    # Conversão e limpeza
    df["data"] = pd.to_datetime(df["data"], errors="coerce")
    df = df.dropna(subset=["data", "frequenciaMedia"])
    df["frequenciaMedia"] = pd.to_numeric(df["frequenciaMedia"], errors="coerce")
    df = df.dropna(subset=["frequenciaMedia"])

    # Ordenar por data decrescente
    df = df.sort_values(by="data", ascending=False)

    # Arredondar para hora cheia com 'h'
    df["hora"] = df["data"].dt.floor("h")

    # Selecionar as últimas 5 horas únicas
    ultimas_5_horas = df["hora"].drop_duplicates().head(5)

    # Filtrar os dados dessas horas
    df_filtrado = df[df["hora"].isin(ultimas_5_horas)]

    if df_filtrado.empty:
        return {"media": None, "media_por_hora": {}, "mensagem": "Nenhum dado nas últimas 5 horas registradas."}

    # Calcular média por hora
    medias_por_hora = df_filtrado.groupby("hora")["frequenciaMedia"].mean().sort_index()
    medias_formatadas = {str(hora): round(media, 2) for hora, media in medias_por_hora.items()}

    # Corrigindo a média geral (média das médias por hora)
    media_geral = round(medias_por_hora.mean(), 2)

    return {
        "media": media_geral,
        "media_por_hora": medias_formatadas
    }
