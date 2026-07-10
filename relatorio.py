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

URL_POWER_BI = "https://app.powerbi.com/view?r=eyJrIjoiMjdhZmQ4MGMtNDM4NC00MDUyLWJjN2YtMDI4NDgwZjhiYzgwIiwidCI6ImY0Y2Q4NWNjLWQ1YTAtNGVmZC04NzkzLThhNzg5NDE5MGNmYSJ9&pageName=204706e0c37ceab79e87"

REMETENTE_EMAIL = "welliton.almeida@pizzattolog.com.br"
REMETENTE_SENHA = os.environ.get("SENHA_EMAIL")

# 1. MAPEAMENTO: Gestores e Gerentes do painel -> E-mail Corporativo
MAPA_EMAILS = {
    # --- GESTORES ---
    "FRANCISCOW": "frota@pizzattolog.com.br",
    "FERNANDOS": "fernando.sarzi@pizzattolog.com.br",
    "TIAGOA": "tiago.alves@pizzattolog.com.br",
    "ANAILSONS": "anailson.moraes@pizzattolog.com.br",
    "ALEXM": "alex.moreira@pizzattolog.com.br",
    "ERICKT": "erick.tosin@pizzattolog.com.br",
    "EDEMILSONG": "edemilson.gomes@pizzattolog.com.br",
    "GUSTAVOA": "gustavo.alves@pizzattolog.com.br",
    "JULIANAA": "juliana.andrade@pizzattolog.com.br",
    "JULIOR": "julio.junior@pizzattolog.com.br",
    "NILTONM": "nilton.marcondes@pizzattolog.com.br",
    "SANDROA": "sandro.almeida@pizzattolog.com.br",
    "ALISONM": "alison.martins@pizzattolog.com.br",
    "JULIOJ": "julio.franca@pizzattolog.com.br",
    "LEANDROP": "leandro.patricio@pizzattolog.com.br",

    # --- GERÊNCIA ---
    "DIEGON": "diego.nascimento@pizzattolog.com.br",
    "CARLOSB": "carlos.batista@pizzattolog.com.br", 
    "DAIANEC": "daiane.camilo@pizzattolog.com.br",
    "LUCASW": "lucas.justus@pizzattolog.com.br"
}

# E-mails que sempre vão receber o relatório completo para monitoramento
COPIA_FIXA = [
    "welliton.almeida@pizzattolog.com.br",
    "magdo.ferreira@pizzattolog.com.br"
]

SMTP_SERVIDOR = "smtp.gmail.com"
SMTP_PORTA = 587

# ==================================================
# CAPTURA DO POWER BI E LEITURA DE TEXTOS
# ==================================================

def capturar_print_e_usuarios(url, caminho_saida):

    print("=" * 60)
    print("📸 INICIANDO CAPTURA E LEITURA DO POWER BI")
    print("=" * 60)

    usuarios_detectados = set()

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

            context = browser.new_context(viewport={"width": 1920, "height": 1080})
            page = context.new_page()
            page.set_default_timeout(120000)

            print("🌐 Abrindo dashboard...")
            page.goto(url, wait_until="domcontentloaded", timeout=120000)

            print("⏳ Aguardando renderização dos gráficos (60s)...")
            time.sleep(60)

            # 🔍 PROCURANDO OS NOMES DOS USUÁRIOS DENTRO DOS GRÁFICOS (SVG text elements)
            print("🔍 Identificando usuários ativos na tela...")
            text_elements = page.locator("svg text, text, .visual-title").all_text_contents()
            
            for texto in text_elements:
                texto_limpo = texto.strip().upper()
                # Se o texto capturado bater com alguma chave do nosso MAPA_EMAILS, nós adicionamos
                if texto_limpo in MAPA_EMAILS:
                    usuarios_detectados.add(texto_limpo)

            print(f"👥 Usuários encontrados com pendências hoje: {list(usuarios_detectados)}")

            print("📷 Capturando screenshot...")
            page.screenshot(path=caminho_saida, full_page=True)
            browser.close()

            if not os.path.exists(caminho_saida):
                print("❌ Screenshot não foi criada.")
                return False, []

            return True, list(usuarios_detectados)

    except Exception:
        print("\n❌ ERRO AO CAPTURAR O POWER BI")
        traceback.print_exc(file=sys.stdout)
        return False, []


# ==================================================
# ENVIO DE E-MAIL DINÂMICO
# ==================================================

def enviar_email(caminho_imagem, usuarios_pendentes):

    print("=" * 60)
    print("📧 ENVIANDO E-MAIL PARA TODOS OS GESTORES E GERENTES")
    print("=" * 60)

    try:
        if not REMETENTE_SENHA:
            print("❌ SENHA_EMAIL não encontrada.")
            return False

        # Começa com a cópia fixa
        destinatarios_finais = list(COPIA_FIXA)
        
        # MODIFICAÇÃO AQUI: Em vez de usar apenas os 'usuarios_pendentes', 
        # agora pegamos TODOS do MAPA_EMAILS diretamente.
        for email_user in MAPA_EMAILS.values():
            if email_user and email_user not in destinatarios_finais:
                destinatarios_finais.append(email_user)

        print(f"📬 Lista final de envio para este e-mail ({len(destinatarios_finais)} destinatários): {destinatarios_finais}")

        msg = MIMEMultipart("related")
        msg["From"] = REMETENTE_EMAIL
        msg["To"] = ", ".join(destinatarios_finais)
        msg["Subject"] = f"Relatório Diário de Aprovações - {datetime.now().strftime('%d/%m/%Y')}"

        cid_imagem = "dashboard_Compras"

        html = f"""
<html>
    <body style="font-family: Arial">
        <h2>Dashboard Compras</h2>
        <p>Prezados,</p>
        <p>Segue aprovações pendentes para acompanhamento Geral.</p>
        <p>Acesse também o dashboard completo pelo link abaixo:</p>
        <p><a href="{URL_POWER_BI}">Abrir Dashboard Online</a></p>
        <br>
        <img src="cid:{cid_imagem}" width="1200">
        <br><br>
        <p>Enviado automaticamente pelo GitHub Actions.</p>
    </body>
</html>
"""

        msg.attach(MIMEText(html, "html", "utf-8"))

        with open(caminho_imagem, "rb") as arquivo:
            imagem = MIMEImage(arquivo.read())
            imagem.add_header("Content-ID", f"<{cid_imagem}>")
            imagem.add_header("Content-Disposition", "inline", filename="dashboard_compras.png")
            msg.attach(imagem)

        print("📡 Conectando Gmail SMTP...")
        with smtplib.SMTP(SMTP_SERVIDOR, SMTP_PORTA, timeout=60) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()

            print("🔑 Realizando login...")
            server.login(REMETENTE_EMAIL, REMETENTE_SENHA)

            print("📤 Enviando e-mail...")
            server.sendmail(REMETENTE_EMAIL, destinatarios_finais, msg.as_string())

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

    pasta_script = os.path.dirname(os.path.abspath(__file__))
    caminho_print = os.path.join(pasta_script, "print_compras_auto.png")

    # Mantivemos a função de captura caso você queira resolver a leitura em tela futuramente,
    # porém a lista gerada aqui 'usuarios_na_tela' não influenciará no envio por enquanto.
    sucesso_print, usuarios_na_tela = capturar_print_e_usuarios(URL_POWER_BI, caminho_print)

    if not sucesso_print:
        print("🛑 Falha ao capturar dashboard.")
        sys.exit(1)

    # Passa a lista (mesmo que vazia ou incompleta) mas a função enviará para todos.
    sucesso_email = enviar_email(caminho_print, usuarios_na_tela)

    if not sucesso_email:
        print("🛑 Falha ao enviar e-mail.")
        sys.exit(1)

    print("🎉 PROCESSO CONCLUÍDO COM SUCESSO")
