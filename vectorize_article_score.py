import psycopg2
import numpy as np
import requests

def get_embedding_from_ollama(text):
    ollama_api_url = "http://10.10.144.2:11434/api/embeddings"
    response = requests.post(ollama_api_url, json={"prompt": text, "model": "nomic-embed-text:latest"})
    if response.status_code == 200:
        return response.json()["embedding"]
    else:
        raise Exception(f"Ошибка при получении эмбеддинга: {response.text}")

def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def vectorize_and_update_scores():
    conn = psycopg2.connect(
        dbname='postgres',
        user='postgres',
        password='postgres',
        host='10.10.144.2',
        port=5432
    )
    conn.autocommit = True

    with conn.cursor() as cur:
        cur.execute("SELECT id, content FROM article WHERE score IS NULL")
        articles = cur.fetchall()
        print(f"Найдено {len(articles)} статей для обработки.")
        for id_, content in articles:
            if not content or not content.strip():
                continue
            embedding = get_embedding_from_ollama(content)
            # Получаем все эмбеддинги и score из news_scaled
            cur.execute("""
                SELECT score, description_embedding FROM public.news_scaled
                WHERE description_embedding IS NOT NULL
            """)
            rows = cur.fetchall()
            best_score = None
            best_sim = -2
            for score, emb in rows:
                if emb is None:
                    continue
                sim = cosine_similarity(embedding, emb)
                if sim > best_sim:
                    best_sim = sim
                    best_score = score
            if best_score is not None:
                cur.execute(
                    "UPDATE article SET score = %s WHERE id = %s",
                    (best_score, id_)
                )
                print(f"Обновлено: id={id_}, score={best_score}")

    conn.close()
    print("Векторизация и обновление score завершены.")

if __name__ == "__main__":
    vectorize_and_update_scores() 