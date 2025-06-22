from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
import numpy as np
import requests
from typing import Any
import ast

app = FastAPI()

# Модель запроса
class QueryRequest(BaseModel):
    text: str

# Функция получения эмбеддинга
def get_embedding_from_ollama(text: str):
    ollama_api_url = "http://10.10.144.2:11434/api/embeddings"
    response = requests.post(ollama_api_url, json={"prompt": text, "model": "nomic-embed-text:latest"})
    if response.status_code == 200:
        return response.json()["embedding"]
    else:
        raise HTTPException(status_code=500, detail=f"Ошибка эмбеддинга: {response.text}")

# Функция косинусного сходства
def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def parse_pg_array(arr):
    if isinstance(arr, list):
        return arr
    if isinstance(arr, str):
        arr = arr.strip()
        # Если строка начинается с [, это Python-список
        if arr.startswith("[") and arr.endswith("]"):
            try:
                return [float(x) for x in ast.literal_eval(arr)]
            except Exception:
                return []
        # Если строка в формате {0.1,0.2,...}
        arr = arr.strip("{}")
        if not arr:
            return []
        return [float(x) for x in arr.split(",")]
    return []

# Подключение к БД
conn = psycopg2.connect(
    dbname='postgres',
    user='postgres',
    password='postgres',
    host='10.10.144.2',
    port=5432
)

@app.post("/score")
def get_score(query: QueryRequest):
    embedding = get_embedding_from_ollama(query.text)
    with conn.cursor() as cur:
        cur.execute("""
            SELECT embedding FROM public.annotation_vec
            WHERE embedding IS NOT NULL
        """)
        rows = cur.fetchall()
        if not rows:
            raise HTTPException(status_code=404, detail="Нет эмбеддингов в базе.")
        best_sim = -2
        for (emb,) in rows:
            emb = parse_pg_array(emb)
            if not emb:
                continue
            sim = cosine_similarity(embedding, emb)
            if sim > best_sim:
                best_sim = sim
        is_exist = bool(best_sim > 0.9)
        return {"is_exist": is_exist}