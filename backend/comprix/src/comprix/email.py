from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from jwt import decode

from comprix.settings import Settings

settings = Settings()

FUSO_BRASIL = ZoneInfo('America/Sao_Paulo')

PORT_STARTLS = 587
PORT_SSL = 465

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_FROM_NAME='COMPRIX',
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_STARTTLS=settings.MAIL_PORT == PORT_STARTLS,
    MAIL_SSL_TLS=settings.MAIL_PORT == PORT_SSL,
    USE_CREDENTIALS=bool(settings.MAIL_USERNAME),
    TEMPLATE_FOLDER=Path(__file__).parent / 'templates' / 'email',
)


def data_expiracao(token: str) -> str:
    """Lê a claim 'exp' do token e formata no horário de Brasília."""
    payload = decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
        # Só lemos a data; quem valida a expiração é a rota /definir-senha
        options={'verify_exp': False},
    )
    expira = datetime.fromtimestamp(payload['exp'], tz=FUSO_BRASIL)

    return expira.strftime('%d/%m/%Y às %H:%M')


async def enviar_email_definir_senha(
    nome: str, email: str, token: str
) -> None:
    """Envia o e-mail com o link para o usuário definir a senha."""
    mensagem = MessageSchema(
        subject='Defina sua senha no COMPRIX',
        recipients=[email],
        template_body={
            'nome': nome,
            'link': f'{settings.FRONTEND_URL}/definir-senha?token={token}',
            'expira_em': data_expiracao(token),
        },
        subtype=MessageType.html,
    )

    await FastMail(conf).send_message(
        mensagem, template_name='definir_senha.html'
    )


async def testar_conexao() -> None:  # pragma: no cover
    """Testa o login no servidor de e-mail, sem enviar nada."""
    import aiosmtplib  # noqa: PLC0415

    senha = settings.MAIL_PASSWORD.get_secret_value()

    print(f'Servidor: {settings.MAIL_SERVER}:{settings.MAIL_PORT}')  # noqa: T201
    print(f'Usuário:  {settings.MAIL_USERNAME}')  # noqa: T201
    print(f'Senha:    {len(senha)} caracteres')  # noqa: T201

    smtp = aiosmtplib.SMTP(
        hostname=settings.MAIL_SERVER,
        port=settings.MAIL_PORT,
        start_tls=settings.MAIL_PORT == 587,  # noqa: PLR2004
        timeout=15,
    )

    try:
        await smtp.connect()
        print('Conexão com o servidor: OK')  # noqa: T201

        await smtp.login(settings.MAIL_USERNAME, senha)
        print('Login: OK, usuário e senha corretos!')  # noqa: T201

    except aiosmtplib.SMTPAuthenticationError as erro:
        print(f'Login recusado: {erro.code} {erro.message}')  # noqa: T201

    except Exception as erro:  # noqa: BLE001
        print(f'Não foi possível conectar: {erro}')  # noqa: T201

    finally:
        if smtp.is_connected:
            await smtp.quit()


if __name__ == '__main__':  # pragma: no cover
    import asyncio

    asyncio.run(testar_conexao())
