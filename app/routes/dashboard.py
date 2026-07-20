from fastapi import APIRouter
from sqlalchemy import text
from database.postgres_sql import get_engine

router = APIRouter()

@router.get("/metrics")
def get_metrics():
    engine = get_engine()

    query = """
    SELECT *
    FROM (
        SELECT *,
               ROW_NUMBER() OVER (
                   PARTITION BY company, year
                   ORDER BY created_at DESC
               ) AS rn
        FROM financial_metrics
    ) t
    WHERE rn = 1
    ORDER BY company
    """

    try:
        with engine.connect() as connection:
            result = connection.execute(text(query))
            rows = []
            for row in result:
                r = dict(row._mapping)
                if 'created_at' in r:
                    del r['created_at']
                rows.append(r)
        return rows
    except Exception as e:
        print(f"Error connecting to database or fetching metrics: {e}")
        return []
