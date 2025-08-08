from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from bson import ObjectId
from pydantic import BaseModel
from typing import List, Optional

# Modelos Pydantic (que estariam no app.models)
class ClienteBase(BaseModel):
    nome: str
    email: str
    telefone: str
    empresa: Optional[str] = None
    segmento: Optional[str] = None

class ClienteCreate(ClienteBase):
    pass

class Cliente(ClienteBase):
    id: str

# Criação do app FastAPI
app = FastAPI()

# Conexão com MongoDB
client = MongoClient("mongodb://localhost:27017")
db = client["Marketing"]
collection = db["Dados dos clientes"]

# Rotas CRUD
@app.post("/clientes/", response_model=Cliente)
async def criar_cliente(cliente: ClienteCreate):
    cliente_dict = cliente.model_dump()
    result = collection.insert_one(cliente_dict)
    return {**cliente_dict, "id": str(result.inserted_id)}

@app.get("/clientes/", response_model=List[Cliente])
async def ler_clientes():
    clientes = list(collection.find())
    for cliente in clientes:
        cliente["id"] = str(cliente["_id"])
    return clientes

@app.get("/clientes/{cliente_id}", response_model=Cliente)
async def ler_cliente(cliente_id: str):
    if (cliente := collection.find_one({"_id": ObjectId(cliente_id)})) is not None:
        cliente["id"] = str(cliente["_id"])
        return cliente
    raise HTTPException(status_code=404, detail="Cliente não encontrado")

@app.put("/clientes/{cliente_id}", response_model=Cliente)
async def atualizar_cliente(cliente_id: str, cliente: ClienteCreate):
    update_result = collection.update_one(
        {"_id": ObjectId(cliente_id)},
        {"$set": cliente.model_dump()}
    )
    if update_result.modified_count == 1:
        return {**cliente.model_dump(), "id": cliente_id}
    raise HTTPException(status_code=404, detail="Cliente não encontrado")

@app.delete("/clientes/{cliente_id}")
async def deletar_cliente(cliente_id: str):
    delete_result = collection.delete_one({"_id": ObjectId(cliente_id)})
    if delete_result.deleted_count == 1:
        return {"message": "Cliente deletado com sucesso"}
    raise HTTPException(status_code=404, detail="Cliente não encontrado")