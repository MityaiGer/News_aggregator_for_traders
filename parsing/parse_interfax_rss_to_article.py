import requests
import psycopg2
import xml.etree.ElementTree as ET
from datetime import datetime

# Сопоставление category (из RSS) с id сектора из вашей базы
CATEGORY_TO_SECTOR = {
    "Здравоохранение": 1,
    "Нециклические компании": 2,
    "Финансы": 3,
    "Промышленность": 4,
    "Сырье": 5,
    "Коммунальные услуги": 6,
    "Технологии": 7,
    "Энергетика": 8,
    "Циклические компании": 9,
    "Недвижимость": 10,
}

def parse_rss_and_insert():
    url = "https://www.interfax.ru/rss.asp"
    resp = requests.get(url)
    resp.raise_for_status()
    root = ET.fromstring(resp.content)

    # Подключение к БД
    conn = psycopg2.connect(
        dbname='postgres',
        user='postgres',
        password='postgres',
        host='10.10.144.2',
        port=5432
    )
    conn.autocommit = True

    items = root.findall('.//item')
    count = 0

    for item in items:
        category = item.findtext('category')
        sector_id = CATEGORY_TO_SECTOR.get(category)
        if not sector_id:
            continue  # Пропускаем, если категория не совпала

        title = item.findtext('title')
        content = item.findtext('description')
        link = item.findtext('link')
        pubDate = item.findtext('pubDate')

        # Преобразуем pubDate к формату базы (YYYY-MM-DD HH:MM:SS)
        try:
            date = datetime.strptime(pubDate, "%a, %d %b %Y %H:%M:%S %z")
            date_str = date.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            date_str = None

        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO article (title, content, link, sectors, date)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (title, content, link, [sector_id], date_str)
            )
        count += 1
        if count >= 50:
            break  # Останавливаемся после 50 подходящих новостей

    conn.close()
    print(f"Добавлено {count} новостей в article.")

if __name__ == "__main__":
    parse_rss_and_insert() 