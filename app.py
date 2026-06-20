from flask import Flask, render_template, jsonify, request
import pandas as pd

app = Flask(__name__)

CAMINHO = r"https://juliosimoes-my.sharepoint.com/:x:/g/personal/vinicius_andrade_jsl_com_br/IQDi7Z5w-gcTT4lK-IhbPYVlAUrKrEe0-rIzw3pf1vH_gcE?e=xOZt93"

def tratar_data(df):

    # tenta converter direto
    df["DATA_ORIGINAL"] = df["DATA"]
    df["DATA"] = pd.to_datetime(df["DATA"], dayfirst=True, errors="coerce")

    # se não conseguiu converter → corrige texto tipo 05/jan
    mask = df["DATA"].isna()

    if mask.any():

        df_temp = df.loc[mask].copy()
        df_temp["TXT"] = df_temp["DATA_ORIGINAL"].astype(str)

        meses = {
            "jan": "01","fev": "02","mar": "03","abr": "04",
            "mai": "05","jun": "06","jul": "07","ago": "08",
            "set": "09","out": "10","nov": "11","dez": "12"
        }

        for k, v in meses.items():
            df_temp["TXT"] = df_temp["TXT"].str.replace(k, v, case=False)

        df_temp["DATA"] = pd.to_datetime(df_temp["TXT"], dayfirst=True, errors="coerce")

        df.loc[mask, "DATA"] = df_temp["DATA"]

    # remove inválidas
    df = df.dropna(subset=["DATA"])

    return df


def processar(mes):

    df = pd.read_excel(CAMINHO, engine="openpyxl")
    df.columns = df.columns.str.strip()

    # ✅ DATA corrigida
    df = tratar_data(df)

    # ✅ FILTRO CORRETO
    df = df[df["DATA"].dt.month == mes]

    # DIA
    df["DIA"] = df["DATA"].dt.day

    # ✅ TURNO (PONTO ZP6)
    df["PONTO ZP6"] = df["PONTO ZP6"].astype(str).str.upper().str.strip()

    df["PONTO ZP6"] = df["PONTO ZP6"].replace({
        "1° TURNO": "1T",
        "2° TURNO": "2T",
        "1 TURNO": "1T",
        "2 TURNO": "2T",
        "TURNO 1": "1T",
        "TURNO 2": "2T"
    })

    dados = {"1T": {}, "2T": {}}

    for turno in ["1T", "2T"]:

        df_t = df[df["PONTO ZP6"] == turno]

        total = df_t.groupby("DIA")["TOTAL"].sum()
        aberto = df_t.groupby("DIA")["ABERTOS"].sum()
        debito = df_t.groupby("DIA")["DÉBITO"].sum()

        for dia in range(1, 32):
            dados[turno][dia] = {
                "total": int(total.get(dia, 0)),
                "aberto": int(aberto.get(dia, 0)),
                "debito": int(debito.get(dia, 0))
            }

    return dados


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/dados")
def dados():
    mes = int(request.args.get("mes", 1))
    return jsonify(processar(mes))


if __name__ == "__main__":
    app.run(debug=True, port=5003)
