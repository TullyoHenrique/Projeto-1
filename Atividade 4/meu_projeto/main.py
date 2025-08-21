import sys
from pathlib import Path

# Adiciona o diretório pai ao path
sys.path.append(str(Path(__file__).parent.parent))
from fastapi import FastAPI
from routers.cliente_router import router as cliente_router
from dependencies import get_db

app = FastAPI(
    title="API de Análise de Clientes",
    description="API para análise de dados de clientes e suas compras",
    version="1.0.0",
)

# Inclui os routers
app.include_router(cliente_router)

@app.on_event("startup")
async def startup_db_client():
    # Inicializa a conexão com o banco de dados
    db = next(get_db())
    print("Conectado ao MongoDB!")

@app.on_event("shutdown")
async def shutdown_db_client():
    # Garante que a conexão será fechada
    db = next(get_db())
    db.client.close()
    print("Conexão com MongoDB fechada.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)