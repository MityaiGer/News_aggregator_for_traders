import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from sentence_transformers import SentenceTransformer
from catboost import CatBoostRegressor

# 1. Загрузка данных
# Замените путь на ваш, если нужно
df = pd.read_csv('data_scaled_with_tickers.csv')

# 2. Получение эмбеддингов для title
model_name = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'  # Поддерживает русский
embedder = SentenceTransformer(model_name)

print('Вычисляем эмбеддинги для title...')
title_emb = embedder.encode(df['title'].astype(str).tolist(), show_progress_bar=True)

# 3. Подготовка данных
X = np.array(title_emb)
y = df['score'].values

# 4. Разделение на train/test
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

# 5. Обучение модели
print('Обучаем CatBoostRegressor...')
model = CatBoostRegressor(verbose=0)
model.fit(X_train, y_train)

# 6. Оценка качества
y_pred = model.predict(X_test)
print('MSE:', mean_squared_error(y_test, y_pred))

# 7. Пример предсказания
example = ["Яндекс увеличил прибыль на $1 млрд"]
example_emb = embedder.encode(example)
pred = model.predict(example_emb)
print(f'Prediction for "{example[0]}":', pred[0]) 