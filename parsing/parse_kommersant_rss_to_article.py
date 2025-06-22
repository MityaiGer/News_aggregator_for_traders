import requests
import psycopg2
import xml.etree.ElementTree as ET
from datetime import datetime

def parse_kommersant_rss_to_article():
    url = "https://www.kommersant.ru/rss/section-economics.xml"
    resp = requests.get(url)
    resp.raise_for_status()
    root = ET.fromstring(resp.content)

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
        title = item.findtext('title')
        content = item.findtext('description')
        link = item.findtext('link')
        pubDate = item.findtext('pubDate')
        category = item.findtext('category')

        # Пропускаем, если нет description
        if not content or not content.strip():
            continue

        # Оставляем только новости с категорией "Экономика"
        is_economics = False
        if category and category.strip().lower() == "экономика":
            is_economics = True
        elif title and title.strip().lower().startswith("экономика"):
            is_economics = True

        if not is_economics:
            continue

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
                (title, content, link, [3], date_str)
            )
        count += 1

    conn.close()
    print(f"Добавлено {count} экономических новостей из kommersant.ru в article.")

if __name__ == "__main__":
    parse_kommersant_rss_to_article()