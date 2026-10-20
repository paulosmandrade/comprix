from http import HTTPStatus


def test_root_deve_retornar_ok_e_mensagem(client):
    response = client.get('/')

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'message': 'Bem-vindo ao Comprix'}


def test_favicon_deve_retornar_o_icone(client):
    response = client.get('/favicon.ico')

    assert response.status_code == HTTPStatus.OK
    assert response.headers['content-type'] == 'image/vnd.microsoft.icon'
