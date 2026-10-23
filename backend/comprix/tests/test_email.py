from pathlib import Path

import pytest
from freezegun import freeze_time
from jinja2 import Environment, FileSystemLoader

from comprix.email import conf, data_expiracao, enviar_email_definir_senha
from comprix.security import create_definir_senha_token


# ---------------------------------------------------------------------------
# Auxiliar
# ---------------------------------------------------------------------------
def renderizar_template(**valores) -> str:
    """Renderiza o template do e-mail com os valores informados."""
    env = Environment(loader=FileSystemLoader(conf.TEMPLATE_FOLDER))
    return env.get_template('definir_senha.html').render(**valores)


# ---------------------------------------------------------------------------
# Função: data_expiracao
# ---------------------------------------------------------------------------
def test_data_expiracao_no_horario_de_brasilia():
    """A data de expiração sai no horário de Brasília"""
    # Token criado ao meio-dia UTC; vence 24h depois, às 12:00 UTC
    with freeze_time('2026-01-01 12:00:00'):
        token = create_definir_senha_token('teste@comprix.com.br')

    # 12:00 UTC = 09:00 em Brasília
    assert data_expiracao(token) == '02/01/2026 às 09:00'


# ---------------------------------------------------------------------------
# Função: enviar_email_definir_senha
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_enviar_email_monta_a_mensagem(monkeypatch, settings):
    """A mensagem é montada com assunto, destinatário e dados certos"""
    mensagens = []

    # Troca o envio real por uma função que só guarda a mensagem
    async def send_message_falso(self, message, template_name=None):
        mensagens.append({'mensagem': message, 'template': template_name})

    monkeypatch.setattr(
        'comprix.email.FastMail.send_message', send_message_falso
    )

    token = create_definir_senha_token('maria@comprix.com.br')
    await enviar_email_definir_senha('Maria', 'maria@comprix.com.br', token)

    # Confirma que uma mensagem foi enviada
    assert len(mensagens) == 1
    mensagem = mensagens[0]['mensagem']

    # Confirma o template, o assunto e o destinatário
    assert mensagens[0]['template'] == 'definir_senha.html'
    assert mensagem.subject == 'Defina sua senha no COMPRIX'
    assert [r.email for r in mensagem.recipients] == ['maria@comprix.com.br']

    # Confirma os valores que vão para o template
    assert mensagem.template_body['nome'] == 'Maria'
    assert mensagem.template_body['link'] == (
        f'{settings.FRONTEND_URL}/definir-senha?token={token}'
    )
    assert mensagem.template_body['expira_em'] == data_expiracao(token)


# ---------------------------------------------------------------------------
# Template: definir_senha.html
# ---------------------------------------------------------------------------
def test_template_existe():
    """O arquivo do template está na pasta configurada"""
    caminho = Path(conf.TEMPLATE_FOLDER) / 'definir_senha.html'

    assert caminho.is_file()


def test_template_mostra_nome_link_e_validade():
    """O e-mail mostra o nome, o link e a data de expiração"""
    html = renderizar_template(
        nome='Maria',
        link='http://localhost:5173/definir-senha?token=abc123',
        expira_em='02/01/2026 às 09:00',
    )

    assert 'Olá, Maria!' in html
    assert 'http://localhost:5173/definir-senha?token=abc123' in html
    assert '02/01/2026 às 09:00' in html


def test_template_escapa_html_no_nome():
    """Um nome com HTML aparece como texto, sem virar código no e-mail"""
    html = renderizar_template(
        nome='<b>Maria</b>',
        link='http://localhost:5173/definir-senha?token=abc123',
        expira_em='02/01/2026 às 09:00',
    )

    # O HTML não entra cru no e-mail
    assert '<b>Maria</b>' not in html
    # Ele aparece escapado, como texto
    assert '&lt;b&gt;Maria&lt;/b&gt;' in html
