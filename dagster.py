import json
import pandas as pd
from dagster import job, op, In, Out
from pymongo import MongoClient
from sqlalchemy import create_engine
import seaborn as sns
import plotly.express as px
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt

# MongoDB connection (adjust URI as needed)
MONGO_URI = "mongodb://localhost:27017/"
mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client["food_waste_db"]
mongo_collection = mongo_db["raw_data"]

# PostgreSQL connection string
PG_CONN_STRING = "postgresql://user:password@localhost:5432/food_waste"
pg_engine = create_engine(PG_CONN_STRING)

@op(out=Out())
def get_and_store_json():
    with open("food_waste_data.json") as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    mongo_collection.delete_many({})  # clear existing data
    mongo_collection.insert_many(df.to_dict("records"))
    return df

@op(ins={"raw_df": In()}, out=Out())
def transform_data(raw_df):
    df = raw_df.copy()
    # Drop irrelevant columns
    irrelevant_cols = [col for col in df.columns if "unnecessary" in col]
    df.drop(columns=irrelevant_cols, inplace=True, errors='ignore')

    # Drop duplicates
    df.drop_duplicates(inplace=True)

    # Convert datatypes
    for col in df.select_dtypes(include='object'):
        try:
            df[col] = pd.to_datetime(df[col])
        except:
            pass

    # Handle missing values
    df.fillna(method='ffill', inplace=True)

    # Remove negative values
    num_cols = df.select_dtypes(include='number').columns
    for col in num_cols:
        df = df[df[col] >= 0]

    df.to_sql("transformed_data", pg_engine, if_exists="replace", index=False)
    return df

@op(ins={"transformed_df": In()})
def analyze_data(transformed_df):
    print("Creating Visualizations...")

    # Plotly example
    fig = px.histogram(transformed_df, x=transformed_df.columns[0])
    fig.show()

    # Seaborn example
    sns.pairplot(transformed_df.select_dtypes(include='number'))
    plt.show()

    # Linear Regression
    numeric_df = transformed_df.select_dtypes(include='number').dropna()
    if numeric_df.shape[1] >= 2:
        X = numeric_df.iloc[:, :-1]
        y = numeric_df.iloc[:, -1]
        model = LinearRegression().fit(X, y)
        print("Regression Coefficients:", model.coef_)
        print("Intercept:", model.intercept_)
    else:
        print("Not enough numeric data for regression")

@job
def food_waste_pipeline():
    df = get_and_store_json()
    transformed = transform_data(df)
    analyze_data(transformed)
