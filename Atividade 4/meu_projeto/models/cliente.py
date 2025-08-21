from pydantic import BaseModel, Field
from typing import Optional

class UltimaCompra(BaseModel):
    produto: str
    valor: float
    data: str  # Formato YYYY-MM-DD

class ClienteBase(BaseModel):
    id: str = Field(..., min_length=1)
    nome: str = Field(..., min_length=2)
    idade: int = Field(..., gt=0)

class ClienteCreate(ClienteBase):
    ultima_compra: Optional[UltimaCompra] = None

class ClienteUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=2)
    idade: Optional[int] = Field(None, gt=0)
    ultima_compra: Optional[UltimaCompra] = None

class ClienteResponse(ClienteBase):
    ultima_compra: Optional[UltimaCompra] = None