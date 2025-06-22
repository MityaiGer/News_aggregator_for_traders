import pandas as pd
import requests
import psycopg2
from tqdm import tqdm

def get_embedding_from_ollama(text):
    ollama_api_url = "http://10.10.144.2:11434/api/embeddings"
    response = requests.post(ollama_api_url, json={"prompt": text, "model": "nomic-embed-text:latest"})
    print(response.status_code)
    if response.status_code == 200:
        print(response.json())
        return response.json()["embedding"]
    else:
        raise Exception(f"Ошибка при получении эмбеддинга: {response.text}")

# Загрузка CSV
csv_file = 'merged_and_scaled_concat.csv'
df = pd.read_csv(csv_file)

# Подключение к PostgreSQL через psycopg2
conn = psycopg2.connect(
    dbname='postgres',
    user='postgres',
    password='postgres',
    host='10.10.144.2',
    port=5432
)
conn.autocommit = True

# Обновляем эмбеддинги для всех строк с прогресс-баром
with conn.cursor() as cur:
    for idx, row in tqdm(df.iterrows(), total=len(df), desc='Обновление эмбеддингов'):
        if pd.isna(row['description']) or not str(row['description']).strip():
            print(f"Пропущено: пустое описание для строки {idx}")
            continue
        # Проверяем, есть ли уже эмбеддинг
        cur.execute(
            "SELECT description_embedding FROM public.news_scaled WHERE title = %s AND description = %s",
            (row["title"], row["description"])
        )
        existing = cur.fetchone()
        if existing and existing[0] is not None:
            print(f"Пропущено: эмбеддинг уже есть для строки {idx} (title: {row['title']})")
            continue
        embedding = get_embedding_from_ollama(row['description'])
        embedding_str = "{" + ",".join(str(float(x)) for x in embedding) + "}"
        cur.execute(
            """
            UPDATE public.news_scaled
            SET description_embedding = %s
            WHERE title = %s AND description = %s
            """,
            (embedding_str, row["title"], row["description"])
        )
        print(f'Обновлено строк: {cur.rowcount} для title: {row["title"]}')
conn.close()