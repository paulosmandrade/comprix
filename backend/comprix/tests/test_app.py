from http import HTTPStatus

from fastapi.testclient import TestClient

from comprix.app import app

client = TestClient(app)


def test_root_deve_retornar_ok_e_mensagem():
    response = client.get('/')

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'message': 'Bem-vindo ao Comprix'}
