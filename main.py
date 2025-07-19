from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import tempfile
from src.api.service import processamento
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/upload-pdfs")
async def upload_pdfs(
    funcionarios: UploadFile = File(...),
    cartao_pontos: UploadFile = File(...),
    cesta: UploadFile = File(...),
    vt: UploadFile = File(...),
    funcionarios_substitutos: UploadFile = File(...)
):
    f_funcionarios = tempfile.NamedTemporaryFile(delete=False)
    f_cartao_pontos = tempfile.NamedTemporaryFile(delete=False)
    f_cesta = tempfile.NamedTemporaryFile(delete=False)
    f_vt = tempfile.NamedTemporaryFile(delete=False)
    f_func_substitutos = tempfile.NamedTemporaryFile(delete=False)

    try:
        f_funcionarios.write(await funcionarios.read())
        f_funcionarios.flush()

        f_cartao_pontos.write(await cartao_pontos.read())
        f_cartao_pontos.flush()

        f_cesta.write(await cesta.read())
        f_cesta.flush()

        f_vt.write(await vt.read())
        f_vt.flush()

        f_func_substitutos.write(await funcionarios_substitutos.read())
        f_func_substitutos.flush()

        arquivos_recebidos = {
            "funcionarios": f_funcionarios.name,
            "cartao_pontos": f_cartao_pontos.name,
            "cesta": f_cesta.name,
            "vt": f_vt.name,
            "funcionarios_substitutos": f_func_substitutos.name,
        }

        response = processamento(arquivos_recebidos)

    finally:
        f_funcionarios.close()
        f_cartao_pontos.close()
        f_cesta.close()
        f_vt.close()
        f_func_substitutos.close()

        os.unlink(f_funcionarios.name)
        os.unlink(f_cartao_pontos.name)
        os.unlink(f_cesta.name)
        os.unlink(f_vt.name)
        os.unlink(f_func_substitutos.name)

    return JSONResponse(content=response)


