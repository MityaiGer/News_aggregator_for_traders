from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
import numpy as np
import requests
from typing import Any

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
            SELECT score, description_embedding FROM public.news_scaled
            WHERE description_embedding IS NOT NULL
        """)
        rows = cur.fetchall()
        if not rows:
            raise HTTPException(status_code=404, detail="Нет эмбеддингов в базе.")
        # Считаем косинусное сходство
        best_score = None
        best_sim = -2
        for score, emb in rows:
            if emb is None:
                continue
            sim = cosine_similarity(embedding, emb)
            if sim > best_sim:
                best_sim = sim
                best_score = score
        if best_score is None:
            raise HTTPException(status_code=404, detail="Не найдено подходящих новостей.")
        status = "up" if float(best_score) > 0 else "down"
        is_exist = bool(best_sim > 0.9)
        return {"status": status, "score": float(best_score), "is_exist": is_exist}
