from dagster import job, op, In, Out, get_dagster_logger
import requests
import pandas as pd
import json
import io
import seaborn as sns
import plotly.express as px
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
from pyjstat import pyjstat
from config import mongo_db,pg_engine


logger = get_dagster_logger()
url="https://ws.cso.ie/public/api.restful/PxStat.Data.Cube_API.ReadDataset/CJQ06/JSON-stat/2.0/en" 
table_name="crime_offence_garda"

# Step 1: Fetch raw data from API and store in MongoDB
@op(out=Out())
def fetch_and_store_data():
    logger.info(f"Started Fetching records")
    
    response = requests.get(url)
    data = response.json() # returns dict datatype
    
    json_str = json.dumps(data)
    json_io = io.StringIO(json_str)

    # Convert JSON-stat to a flat table pandas Dataframe
    dataset = pyjstat.Dataset.read(json_io)
    df = dataset.write('dataframe')
    logger.info(f"Fetched {len(df)} records")

    mongo_db[table_name].drop()  # clear old data
    records = df.to_dict(orient='records')
    
    # Store the raw data in MongoDB
    mongo_db[table_name].insert_many(records)
    logger.info("Stored data in MongoDB")
    
    return True

# Step 2: Read from MongoDB, ETL, store in PostgreSQL
@op(out=Out(pd.DataFrame))
def transform_and_store():
    records = list(mongo_db[table_name].find())
    df = pd.DataFrame(records)

    logger.info("Starting transformations")

    # ETL: Example transformations
    # Drop irrelevant columns
    df.drop(columns=[col for col in df.columns if 'irrelevant' in col.lower()], inplace=True, errors='ignore')
    # Drop duplicates
    df.drop_duplicates(inplace=True)
    # Handle missing values
    df.fillna(0, inplace=True)

    # Convert datatypes
    for col in df.select_dtypes(include=['object']).columns:
        try:
            df[col] = pd.to_numeric(df[col], errors='ignore')
        except:
            continue
    
    # Remove negative values
    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
    for col in numeric_cols:
        df[col] = df[col].apply(lambda x: max(x, 0))  # Bound check

    logger.info("Finished cleaning")

    df.to_sql('cleaned_data', pg_engine, if_exists='replace', index=False)
    logger.info("Stored cleaned data in PostgreSQL")

    return df

# Step 3: Visualizations and Model
@op(ins={"df": In(pd.DataFrame)})
def visualize_and_model(df):
    if df.empty:
        logger.warning("Empty DataFrame, skipping analysis.")
        return

    logger.info("Generating visualizations and running model...")

    # Plot with Seaborn
    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
    if len(numeric_cols) >= 2:
        sns.pairplot(df[numeric_cols[:4]])
        plt.suptitle("Seaborn Pairplot", y=1.02)
        plt.show()
        # plt.savefig("seaborn_pairplot.png")

        # Plotly scatter
        fig = px.scatter(df, x=numeric_cols[0], y=numeric_cols[1], title='Plotly Scatter')
        fig.show() 
        
        fig = px.histogram(df, x=df.columns[0])
        fig.show() 
        # fig.write_html("plotly_scatter.html")

        # Linear Regression
        # X = df[[numeric_cols[0]]]
        # y = df[numeric_cols[1]]
        # model = LinearRegression()
        # model.fit(X, y)
        # r2 = model.score(X, y)
        # logger.info(f"Linear Regression R² score: {r2:.4f}")

@job
def data_pipeline():
    data = fetch_and_store_data()
    cleaned_df = transform_and_store(data)
    visualize_and_model(cleaned_df)
