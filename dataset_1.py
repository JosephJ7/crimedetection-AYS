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
    try:
        logger.info(f"Started Fetching records")
        
        response = requests.get(url)
        response.raise_for_status() # will raise an error for 4xx/5xx
        data = response.json() # returns dict datatype
        
        json_str = json.dumps(data)
        json_io = io.StringIO(json_str)

        # Convert JSON-stat to a flat table pandas Dataframe
        dataset = pyjstat.Dataset.read(json_io)
        df = dataset.write('dataframe')
        logger.info(f"Fetched {len(df)} records")

        mongo_db[table_name].drop()  # clear old data
        
        # Store the raw data in MongoDB
        records = df.to_dict(orient='records')
        mongo_db[table_name].insert_many(records)
        logger.info("Stored data in MongoDB")
        
        return True
    except Exception as e:
        logger.error(f"Error in fetch_and_store_data: {e}")
        return False

# Step 2: Read from MongoDB, ETL, store in PostgreSQL
@op(ins={"fetched": In(bool)},out=Out(bool))
def transform_and_store(fetched):
    try:
        if not fetched:
            logger.warning("Skipping transformation since data fetch failed.")
            return False
        
        records = list(mongo_db[table_name].find())
        df = pd.DataFrame(records)

        logger.info("Starting transformations")

        # ETL: Example transformations
        # Drop irrelevant columns
        df.drop(columns=["_id","STATISTIC"], inplace=True)
        
        # renaming columns
        new_columns_names =  {"Quarter": "quarter",
                            "Garda Division":"garda_division",
                            "Type of Offence":"offence_type",
                            "value":"count"}
        df.rename(columns=new_columns_names, inplace=True)
        
        # Drop duplicates
        df.drop_duplicates(inplace=True)
        
        # Handle missing values
        df.fillna(0, inplace=True)

        # Convert datatypes
        df["count"] = pd.to_numeric(df["count"], errors="coerce")
        
        # no negative count
        df = df[df["count"] >= 0]
        
        df["year"] = df["quarter"].str.extract(r'(\d{4})').astype(int)
        df["quarter_number"] = df["quarter"].str.extract(r'(Q[1-4])')

        logger.info("Finished cleaning")
        
        df.sort_values(by=["year", "quarter_number"], inplace=True)

        df.to_sql(table_name, pg_engine, if_exists='replace', index=False)
        logger.info("Stored cleaned data in PostgreSQL")

        return True
    except Exception as e:
        logger.error(f"Error in transform_and_store: {e}")
        return False

# Step 3: Visualizations and Model
@op(ins={"transformed": In(bool)})
def visualize_and_model(transformed):
    try:
        logger.info("Reading cleaned data from PostgreSQL...")
        df = pd.read_sql(f'SELECT * FROM {table_name}', pg_engine)
        logger.info(f"Data :{df.head()}")
        if df.empty():
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
    except Exception as e:
        logger.error(f"Error in visualize_and_model: {e}")

@job
def data_pipeline():
    fetched  = fetch_and_store_data()
    transformed = transform_and_store(fetched)
    visualize_and_model(transformed)
