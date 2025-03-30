import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
APP_URL = os.getenv("APP_URL")

async def send_password_reset_email(email: str, token: str):
    message = MIMEMultipart()
    message["From"] = SMTP_USER
    message["To"] = email
    message["Subject"] = "Recuperação de senha"
    
    reset_link = f"{APP_URL}/reset-password?token={token}"
    
    html = f"""
    <html>
        <body>
            <h1>Recuperação de senha</h1>
            <p>Clique no link abaixo para redefinir sua senha:</p>
            <p><a href="{reset_link}">Redefinir senha</a></p>
            <p>Se você não solicitou uma recuperação de senha, ignore este email.</p>
        </body>
    </html>
    """
    
    message.attach(MIMEText(html, "html"))
    
    try:
        await aiosmtplib.send(
            message,
            hostname=SMTP_SERVER,
            port=SMTP_PORT,
            username=SMTP_USER,
            password=SMTP_PASSWORD,
            use_tls=True
        )
        return True
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")
        return False 