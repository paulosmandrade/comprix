from http import HTTPStatus
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from comprix.schemas.app import Message

app = FastAPI()

FAVICON = Path(__file__).parent / 'static' / 'comprix-icon.ico'

@app.get('/favicon.ico', include_in_schema=False)
def favicon():
    return FileResponse(FAVICON)


@app.get('/', status_code = HTTPStatus.OK, response_model=Message)
def read_root():
    return {'message': 'Bem-vindo ao Comprix'}
