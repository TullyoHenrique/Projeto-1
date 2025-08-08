from pydantic import BaseModel
from datetime import date
from typing import Optional

class UltimaCompra(BaseModel):
    produto: str
    valor: float
    data: date

class Cliente(BaseModel):
    id: str
    nome: str
    idade: int
    ultima_compra: UltimaCompra

class ClienteUpdate(BaseModel):
    nome: Optional[str] = None
    idade: Optional[int] = None