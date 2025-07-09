import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np

def train_predict_model(csv_path):
    df = pd.read_csv(csv_path, parse_dates=['Date'])
    df = df.sort_values('Date')
    df['day_num'] = np.arange(len(df))

    X = df[['day_num']]
    y = df['Count']

    model = LinearRegression()
    model.fit(X, y)

    # Predict the next day's count
    next_day = [[len(df)]]
    predicted = model.predict(next_day)[0]
    return round(predicted)
