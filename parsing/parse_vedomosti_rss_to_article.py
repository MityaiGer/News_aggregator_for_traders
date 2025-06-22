import requests
import psycopg2
import xml.etree.ElementTree as ET
from datetime import datetime

def parse_vedomosti_rss_to_article():
    url = "https://www.vedomosti.ru/rss/rubric/finance"
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

        # Пропускаем, если нет description
        if not content or not content.strip():
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
    print(f"Добавлено {count} новостей из vedomosti.ru в article.")

if __name__ == "__main__":
    parse_vedomosti_rss_to_article() 