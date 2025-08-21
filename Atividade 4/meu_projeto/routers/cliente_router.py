import sys
from pathlib import Path

# Adiciona o diretório pai ao path
sys.path.append(str(Path(__file__).parent.parent))

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from models.cliente import ClienteCreate, ClienteUpdate, ClienteResponse
from services.cliente_service import ClienteService
from dependencies import get_cliente_service

router = APIRouter(prefix="/clientes", tags=["Clientes"])

@router.post("/", response_model=ClienteResponse, status_code=status.HTTP_201_CREATED)
async def criar_cliente(
    cliente: ClienteCreate, 
    service: ClienteService = Depends(get_cliente_service)
):
    try:
        return service.criar_cliente(cliente)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro interno")

@router.get("/", response_model=List[ClienteResponse])
async def listar_clientes(
    nome: Optional[str] = None,
    idade_min: Optional[int] = None,
    service: ClienteService = Depends(get_cliente_service)
):
    filtros = {}
    if nome:
        filtros["nome"] = nome
    if idade_min:
        filtros["idade_min"] = idade_min
    
    return service.listar_clientes(filtros)

@router.get("/{cliente_id}", response_model=ClienteResponse)
async def obter_cliente(
    cliente_id: str, 
    service: ClienteService = Depends(get_cliente_service)
):
    try:
        return service.obter_cliente_por_id(cliente_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/{cliente_id}", response_model=ClienteResponse)
async def atualizar_cliente(
    cliente_id: str,
    cliente: ClienteUpdate,
    service: ClienteService = Depends(get_cliente_service)
):
    try:
        return service.atualizar_cliente(cliente_id, cliente)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao atualizar")

@router.delete("/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_cliente(
    cliente_id: str,
    service: ClienteService = Depends(get_cliente_service)
):
    if not service.deletar_cliente(cliente_id):
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

# Rotas de Análise
@router.get("/analise/faixa-etaria", response_model=List[dict])
async def analise_faixa_etaria(service: ClienteService = Depends(get_cliente_service)):
    try:
        return service.analisar_faixa_etaria()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))