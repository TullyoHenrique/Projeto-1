from pymongo import MongoClient
from pymongo.database import Database
from fastapi import Depends
from typing import Generator
from services.cliente_service import ClienteService

def get_db() -> Generator[Database, None, None]:
    client = MongoClient("mongodb://localhost:27017")
    try:
        db = client["clientes_db"]
        # Configura índices
        db.clientes.create_index([("id", 1)], unique=True)
        db.clientes.create_index([("nome", "text")])
        yield db
    finally:
        client.close()

def get_cliente_service(db: Database = Depends(get_db)) -> ClienteService:
    return ClienteService(db)