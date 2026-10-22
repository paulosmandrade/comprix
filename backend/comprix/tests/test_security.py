from comprix.security import get_password_hash, verify_password


def test_hash_nao_e_a_senha_em_texto_puro():
    senha_hash = get_password_hash('minha_senha')
    # senha_hash e diferente de texto puro (verdadeiro)
    assert senha_hash != 'minha_senha'
    # senha_hash no começo $argon2 (verdadeiro)
    assert senha_hash.startswith('$argon2')


def test_hash_da_mesma_senha_muda_a_cada_requisicao():
    assert get_password_hash('abc') != get_password_hash('abc')


def test_verify_password_senha_correta():
    senha_hash = get_password_hash('minha_senha')
    # Retornará true, comparando com a função verify_password
    assert verify_password('minha_senha', senha_hash)


def test_verify_password_senha_errada():
    senha_hash = get_password_hash('minha_senha')
    # Retornará false, comparando com a função verify_password
    assert not verify_password('outra_senha', senha_hash)
