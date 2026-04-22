import pandas as pd
from sklearn.linear_model import LinearRegression
import joblib

data = pd.read_csv("data/weather.csv")

X = data[['tavg','tmin','tmax']]
y = data['prcp']

model = LinearRegression()
model.fit(X,y)

joblib.dump(model,"models/rainfall_model.pkl")

print("Model trained")