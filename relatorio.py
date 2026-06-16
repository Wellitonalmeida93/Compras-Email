import os
import sys
import time
import traceback
import smtplib
from datetime import datetime

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

from playwright.sync_api import sync_playwright

# ==================================================
# CONFIGURAÇÕES
# ==================================================

URL_POWER_BI = "https://app.powerbi.com/view?r=eyJrIjoiZTg0YjIxMjgtYjJhOC00NDY5LWEzYjItNjM0M2IyZTgyMTExIiwidCI6ImY0Y2Q4NWNjLWQ1YTAtNGVmZC04NzkzLThhNzg5NDE5MGNmYSJ9&pageName=2307bfd0ca141332ad94"

REMETENTE_EMAIL = "welliton.almeida@pizzattolog.com.br"
REMETENTE_SENHA = os.environ.get("SENHA_EMAIL")

DESTINATARIOS = [
    "welliton.almeida@pizzattolog.com.br"
]

SMTP_SERVIDOR = "smtp.gmail.com"
SMTP_PORTA = 587

# ==================================================
# CAPTURA DO POWER BI
# ==================================================

def capturar_print_powerbi(url, caminho_saida):

    print("=" * 60)
    print("📸 INICIANDO CAPTURA DO POWER BI")
    print("=" * 60)

    try:

        with sync_playwright() as p:

            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage"
                ]
            )

            context = browser.new_context(
                viewport={
                    "width": 1920,
                    "height": 1080
                }
            )

            page = context.new_page()

            page.set_default_timeout(120000)

            print("🌐 Abrindo dashboard...")

            page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=120000
            )

            print("⏳ Aguardando renderização dos gráficos...")
            time.sleep(60)

            print("📷 Capturando screenshot...")

            page.screenshot(
                path=caminho_saida,
                full_page=True
            )

            browser.close()

            if not os.path.exists(caminho_saida):
                print("❌ Screenshot não foi criada.")
                return False

            tamanho = os.path.getsize(caminho_saida)

            print(f"✅ Screenshot criada.")
            print(f"📦 Tamanho: {tamanho:,} bytes")

            if tamanho < 10000:
                print("⚠️ Screenshot muito pequena.")
                return False

            return True

    except Exception:

        print("\n❌ ERRO AO CAPTURAR O POWER BI")
        traceback.print_exc(file=sys.stdout)

        return False


# ==================================================
# ENVIO DE E-MAIL
# ==================================================

def enviar_email(caminho_imagem):

    print("=" * 60)
    print("📧 ENVIANDO E-MAIL")
    print("=" * 60)

    try:

        if not REMETENTE_SENHA:
            print("❌ SENHA_EMAIL não encontrada.")
            return False

        msg = MIMEMultipart("related")

        msg["From"] = REMETENTE_EMAIL
        msg["To"] = ", ".join(DESTINATARIOS)
        msg["Subject"] = f"Relatório Diário Salesco - {datetime.now().strftime('%d/%m/%Y')}"

        cid_imagem = "dashboard_salesco"

        html = f"""
        <html>
            <body style="font-family: Arial">

                <h2>Dashboard Salesco</h2>

                <p>
                    Relatório atualizado automaticamente.
                </p>

                <p>
                    <a href="{URL_POWER_BI}">
                        Abrir Dashboard Online
                    </a>
                </p>

                <br>

                <img src="cid:{cid_imagem}" width="1200">

                <br><br>

                <p>
                    Enviado automaticamente pelo GitHub Actions.
                </p>

            </body>
        </html>
        """

        msg.attach(
            MIMEText(
                html,
                "html",
                "utf-8"
            )
        )

        with open(caminho_imagem, "rb") as arquivo:

            imagem = MIMEImage(
                arquivo.read()
            )

            imagem.add_header(
                "Content-ID",
                f"<{cid_imagem}>"
            )

            imagem.add_header(
                "Content-Disposition",
                "inline",
                filename="dashboard_salesco.png"
            )

            msg.attach(imagem)

        print("📡 Conectando Gmail SMTP...")

        with smtplib.SMTP(
            SMTP_SERVIDOR,
            SMTP_PORTA,
            timeout=60
        ) as server:

            server.ehlo()
            server.starttls()
            server.ehlo()

            print("🔑 Realizando login...")

            server.login(
                REMETENTE_EMAIL,
                REMETENTE_SENHA
            )

            print("📤 Enviando e-mail...")

            server.sendmail(
                REMETENTE_EMAIL,
                DESTINATARIOS,
                msg.as_string()
            )

        print("✅ E-mail enviado com sucesso.")

        return True

    except Exception:

        print("\n❌ ERRO AO ENVIAR E-MAIL")
        traceback.print_exc(file=sys.stdout)

        return False


# ==================================================
# EXECUÇÃO
# ==================================================

if __name__ == "__main__":

    print("🚀 INICIANDO PROCESSO")

    pasta_script = os.path.dirname(
        os.path.abspath(__file__)
    )

    caminho_print = os.path.join(
        pasta_script,
        "print_salesco_auto.png"
    )

    sucesso_print = capturar_print_powerbi(
        URL_POWER_BI,
        caminho_print
    )

    if not sucesso_print:
        print("🛑 Falha ao capturar dashboard.")
        sys.exit(1)

    sucesso_email = enviar_email(
        caminho_print
    )

    if not sucesso_email:
        print("🛑 Falha ao enviar e-mail.")
        sys.exit(1)

    print("🎉 PROCESSO CONCLUÍDO COM SUCESSO")
