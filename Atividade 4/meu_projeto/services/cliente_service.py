from typing import List, Dict, Any, Optional
from pymongo.database import Database
from bson import ObjectId
from models.cliente import ClienteCreate, ClienteUpdate

class ClienteService:
    def __init__(self, db: Database):
        self.db = db
    
    # Operações CRUD
    def criar_cliente(self, cliente: ClienteCreate) -> Dict:
        """Cria um novo cliente"""
        if self.db.clientes.find_one({"id": cliente.id}):
            raise ValueError("ID do cliente já existe")
        
        cliente_dict = cliente.dict()
        result = self.db.clientes.insert_one(cliente_dict)
        
        if not result.inserted_id:
            raise RuntimeError("Erro ao criar cliente")
        
        return self.obter_cliente_por_id(cliente.id)
    
    def obter_cliente_por_id(self, cliente_id: str) -> Dict:
        """Obtém um cliente pelo ID"""
        cliente = self.db.clientes.find_one({"id": cliente_id}, {"_id": 0})
        if not cliente:
            raise ValueError("Cliente não encontrado")
        return cliente
    
    def atualizar_cliente(self, cliente_id: str, update_data: ClienteUpdate) -> Dict:
        """Atualiza um cliente existente"""
        result = self.db.clientes.update_one(
            {"id": cliente_id},
            {"$set": update_data.dict(exclude_unset=True)}
        )
        
        if result.modified_count == 0:
            raise ValueError("Cliente não encontrado ou dados idênticos")
        
        return self.obter_cliente_por_id(cliente_id)
    
    def deletar_cliente(self, cliente_id: str) -> bool:
        """Remove um cliente"""
        result = self.db.clientes.delete_one({"id": cliente_id})
        return result.deleted_count > 0
    
    def listar_clientes(self, filtros: Dict = {}) -> List[Dict]:
        """Lista clientes com filtros opcionais"""
        query = {}
        if "nome" in filtros:
            query["nome"] = {"$regex": filtros["nome"], "$options": "i"}
        if "idade_min" in filtros:
            query["idade"] = {"$gte": filtros["idade_min"]}
        
        return list(self.db.clientes.find(query, {"_id": 0}))

    # Métodos de Análise
    def analisar_faixa_etaria(self) -> List[Dict[str, Any]]:
        """Agrupa clientes por faixa etária com estatísticas de compra"""
        pipeline = [
            {
                "$bucket": {
                    "groupBy": "$idade",
                    "boundaries": [0, 20, 30, 40, 50, 60, 100],
                    "default": "Outros",
                    "output": {
                        "total": {"$sum": 1},
                        "valor_medio": {"$avg": "$ultima_compra.valor"},
                        "produtos": {"$push": "$ultima_compra.produto"}
                    }
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "faixa": {
                        "$switch": {
                            "branches": [
                                {"case": {"$eq": ["$_id", 0]}, "then": "0-19"},
                                {"case": {"$eq": ["$_id", 20]}, "then": "20-29"},
                                {"case": {"$eq": ["$_id", 30]}, "then": "30-39"},
                                {"case": {"$eq": ["$_id", 40]}, "then": "40-49"},
                                {"case": {"$eq": ["$_id", 50]}, "then": "50-59"},
                                {"case": {"$eq": ["$_id", 60]}, "then": "60+"},
                                {"case": {"$eq": ["$_id", "Outros"]}, "then": "Outros"}
                            ],
                            "default": "Desconhecido"
                        }
                    },
                    "total_clientes": "$total",
                    "valor_medio": {"$round": ["$valor_medio", 2]},
                    "produtos_populares": {
                        "$slice": [
                            {
                                "$reduce": {
                                    "input": "$produtos",
                                    "initialValue": [],
                                    "in": {"$concatArrays": ["$$value", ["$$this"]]}
                                }
                            },
                            5
                        ]
                    }
                }
            },
            {"$sort": {"faixa": 1}}
        ]
        return self._executar_pipeline(pipeline)
    
    def segmentacao_rfm(self) -> List[Dict[str, Any]]:
        """Segmentação RFM (Recência, Frequência, Valor Monetário)"""
        pipeline = [
            {
                "$match": {
                    "ultima_compra": {"$exists": True},
                    "ultima_compra.data": {"$exists": True}
                }
            },
            {
                "$addFields": {
                    "recencia": {
                        "$dateDiff": {
                            "startDate": {"$toDate": "$ultima_compra.data"},
                            "endDate": "$$NOW",
                            "unit": "day"
                        }
                    }
                }
            },
            {
                "$bucket": {
                    "groupBy": "$recencia",
                    "boundaries": [0, 30, 90, 180, 365],
                    "default": "Inativo",
                    "output": {
                        "count": {"$sum": 1},
                        "valor_medio": {"$avg": "$ultima_compra.valor"},
                        "recencia_media": {"$avg": "$recencia"}
                    }
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "segmento": {
                        "$switch": {
                            "branches": [
                                {"case": {"$eq": ["$_id", 0]}, "then": "Ativo (0-30 dias)"},
                                {"case": {"$eq": ["$_id", 30]}, "then": "Regular (30-90 dias)"},
                                {"case": {"$eq": ["$_id", 90]}, "then": "Levemente Inativo (90-180 dias)"},
                                {"case": {"$eq": ["$_id", 180]}, "then": "Inativo (180-365 dias)"},
                                {"case": {"$eq": ["$_id", "Inativo"]}, "then": "Muito Inativo (365+ dias)"}
                            ],
                            "default": "Desconhecido"
                        }
                    },
                    "recencia_media": {"$round": ["$recencia_media", 1]},
                    "valor_medio": {"$round": ["$valor_medio", 2]},
                    "total_clientes": "$count"
                }
            },
            {"$sort": {"recencia_media": 1}}
        ]
        return self._executar_pipeline(pipeline)
    
    def produtos_mais_vendidos(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Lista os produtos mais vendidos"""
        pipeline = [
            {
                "$match": {
                    "ultima_compra.produto": {"$exists": True}
                }
            },
            {
                "$group": {
                    "_id": "$ultima_compra.produto",
                    "total_vendas": {"$sum": 1},
                    "valor_total": {"$sum": "$ultima_compra.valor"},
                    "clientes": {"$push": "$nome"}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "produto": "$_id",
                    "total_vendas": 1,
                    "valor_total": 1,
                    "valor_medio": {"$round": [{"$divide": ["$valor_total", "$total_vendas"]}, 2]},
                    "exemplo_clientes": {"$slice": ["$clientes", 3]}
                }
            },
            {"$sort": {"total_vendas": -1}},
            {"$limit": limit}
        ]
        return self._executar_pipeline(pipeline)
    
    def clientes_maior_valor_compra(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Lista clientes que fizeram as compras de maior valor"""
        pipeline = [
            {
                "$match": {
                    "ultima_compra.valor": {"$exists": True}
                }
            },
            {
                "$sort": {"ultima_compra.valor": -1}
            },
            {
                "$limit": limit
            },
            {
                "$project": {
                    "_id": 0,
                    "id": 1,
                    "nome": 1,
                    "idade": 1,
                    "produto": "$ultima_compra.produto",
                    "valor_compra": "$ultima_compra.valor",
                    "data_compra": "$ultima_compra.data"
                }
            }
        ]
        return self._executar_pipeline(pipeline)
    
    def comportamento_por_idade(self) -> List[Dict[str, Any]]:
        """Analisa comportamento de compra por faixa etária"""
        pipeline = [
            {
                "$addFields": {
                    "faixa_etaria": {
                        "$switch": {
                            "branches": [
                                {"case": {"$lt": ["$idade", 20]}, "then": "Menor que 20"},
                                {"case": {"$lt": ["$idade", 30]}, "then": "20-29"},
                                {"case": {"$lt": ["$idade", 40]}, "then": "30-39"},
                                {"case": {"$lt": ["$idade", 50]}, "then": "40-49"},
                                {"case": {"$lt": ["$idade", 60]}, "then": "50-59"}
                            ],
                            "default": "60+"
                        }
                    }
                }
            },
            {
                "$group": {
                    "_id": "$faixa_etaria",
                    "total_clientes": {"$sum": 1},
                    "valor_medio_compra": {"$avg": "$ultima_compra.valor"},
                    "produtos_diferentes": {"$addToSet": "$ultima_compra.produto"}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "faixa_etaria": "$_id",
                    "total_clientes": 1,
                    "valor_medio_compra": {"$round": ["$valor_medio_compra", 2]},
                    "variedade_produtos": {"$size": "$produtos_diferentes"}
                }
            },
            {"$sort": {"faixa_etaria": 1}}
        ]
        return self._executar_pipeline(pipeline)
    
    def _executar_pipeline(self, pipeline: List[Dict]) -> List[Dict]:
        """Executa um pipeline de agregação com tratamento de erros"""
        try:
            return list(self.db.clientes.aggregate(pipeline))
        except Exception as e:
            raise RuntimeError(f"Erro ao executar pipeline: {str(e)}")