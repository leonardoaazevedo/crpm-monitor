import requests
from bs4 import BeautifulSoup
import json
import os
import smtplib
from email.mime.text import MIMEText

URL = "https://conhecimento.fgv.br/concursos/cprm"
ARQUIVO_ESTADO = "estado_cprm.json"

EMAIL_REMETENTE = os.getenv("EMAIL_REMETENTE")
EMAIL_SENHA = os.getenv("EMAIL_SENHA")
EMAIL_DESTINO = os.getenv("EMAIL_DESTINO")


def enviar_email(novos_itens):
    corpo = "Veja se sobrou algo para os betas.\n\nNovos arquivos adicionados no concurso CPRM:\n\n"

    for item in novos_itens:
        corpo += f"{item['data']} - {item['titulo']}\n{item['link']}\n\n"

    msg = MIMEText(corpo)
    msg["Subject"] = "CPRM - Novo arquivo publicado!"
    msg["From"] = EMAIL_REMETENTE
    msg["To"] = EMAIL_DESTINO

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_REMETENTE, EMAIL_SENHA)
        server.send_message(msg)

    print("📧 Email enviado!")


def extrair_arquivos():
    response = requests.get(URL, timeout=20)

    status = response.status_code
    print(f"Status HTTP: {status}")

    soup = BeautifulSoup(response.text, "html.parser")

    itens = []
    blocos = soup.select("div.paragraph--type--texto-data")

    for bloco in blocos:
        data = bloco.find("time")
        link = bloco.find("a")

        if data and link:
            itens.append({
                "data": data.text.strip(),
                "titulo": link.text.strip(),
                "link": link["href"]
            })

    return itens


def carregar_estado():
    if not os.path.exists(ARQUIVO_ESTADO):
        return []

    with open(ARQUIVO_ESTADO, "r", encoding="utf-8") as f:
        return json.load(f)


def salvar_estado(itens):
    with open(ARQUIVO_ESTADO, "w", encoding="utf-8") as f:
        json.dump(itens, f, ensure_ascii=False, indent=2)


def main():
    print("🚀 Execução do monitor...")

    estado_antigo = carregar_estado()
    estado_atual = extrair_arquivos()

    if not estado_atual:
        print("❌ Sem dados válidos do site.")
        return

    # primeira execução
    if not estado_antigo:
        print("🆕 Inicializando base...")
        salvar_estado(estado_atual)
        return

    links_antigos = {item["link"] for item in estado_antigo}
    novos = [item for item in estado_atual if item["link"] not in links_antigos]

    if novos:
        print("🚨 Novo arquivo detectado!")
        enviar_email(novos)
    else:
        print("✅ Nenhuma novidade.")

    salvar_estado(estado_atual)


if __name__ == "__main__":
    main()