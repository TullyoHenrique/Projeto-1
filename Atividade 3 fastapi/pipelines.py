def pipeline_clientes_por_faixa_etaria():
    return [
        {
            "$group": {
                "_id": {
                    "$switch": {
                        "branches": [
                            {"case": {"$lt": ["$idade", 20]}, "then": "<20"},
                            {"case": {"$lt": ["$idade", 30]}, "then": "20-29"},
                            {"case": {"$lt": ["$idade", 40]}, "then": "30-39"},
                            {"case": {"$lt": ["$idade", 50]}, "then": "40-49"}
                        ],
                        "default": "50+"
                    }
                },
                "total_clientes": {"$sum": 1},
                "total_gasto": {"$sum": "$ultima_compra.valor"},
                "clientes": {"$push": "$nome"}
            }
        },
        {
            "$sort": {"_id": 1}
        }
    ]

def pipeline_produtos_mais_vendidos(limit=5):
    return [
        {
            "$group": {
                "_id": "$ultima_compra.produto",
                "total_vendas": {"$sum": 1},
                "faturamento_total": {"$sum": "$ultima_compra.valor"},
                "clientes": {"$addToSet": "$nome"}
            }
        },
        {
            "$sort": {"faturamento_total": -1}
        },
        {
            "$limit": limit
        }
    ]