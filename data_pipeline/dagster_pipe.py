from dagster import  op, In, Out, get_dagster_logger,graph
import requests
import pandas as pd
import json
import io
from pyjstat import pyjstat
from config import mongo_db,pg_engine
from data_pipeline.visualizations import *


logger = get_dagster_logger()


# Step 1: Fetch raw data from API and store in MongoDB
@op(out=Out(),config_schema={"url": str, "table_name": str})
def fetch_and_store_data(context):
    try:
        url = context.op_config["url"]
        table_name = context.op_config["table_name"]
        
        logger.info(f"Started Fetching records for table - {table_name}")
        
        response = requests.get(url)
        response.raise_for_status() # will raise an error for 4xx/5xx
        data = response.json() # returns dict datatype
        
        json_str = json.dumps(data)
        json_io = io.StringIO(json_str)

        # Convert JSON-stat to a flat table pandas Dataframe
        dataset = pyjstat.Dataset.read(json_io)
        df = dataset.write('dataframe')
        logger.info(f"Fetched {len(df)} records for table - {table_name}")

        mongo_db[table_name].drop()  # clear old data
        
        # Store the raw data in MongoDB
        records = df.to_dict(orient='records')
        mongo_db[table_name].insert_many(records)
        logger.info(f"Stored data in MongoDB for table - {table_name}")
        
        return True
    except Exception as e:
        logger.error(f"Error in fetch_and_store_data: {e} ")
        return False

# Step 2: Read from MongoDB, ETL, store in PostgreSQL
@op(ins={"fetched": In(bool)},out=Out(bool),config_schema={"table_name": str})
def transform_and_store(context,fetched):
    try:
        table_name = context.op_config["table_name"]
        if not fetched:
            logger.warning("Skipping transformation since data fetch failed.")
            return False
        
        records = list(mongo_db[table_name].find())
        df = pd.DataFrame(records)

        logger.info(f"Starting transformations for table - {table_name}")

        # ETL: Example transformations
        # Drop irrelevant columns
        df.drop(columns=["_id"], inplace=True)
        
        if table_name == "crime_offence_garda":
            df["year"] = df["Quarter"].str.extract(r'(\d{4})').astype(int)
            df["quarter_number"] = df["Quarter"].str.extract(r'(Q[1-4])')
            
            df.sort_values(by=["year", "quarter_number"], inplace=True)
            
            # renaming columns
            new_columns_names =  {"Quarter": "quarter",
                                "Garda Division":"garda_division",
                                "Type of Offence":"offence_type",
                                "value":"count",
                                "STATISTIC":"statistic"}
        else:
            new_columns_names =  {"Statistic":"statistic",
                                "Year":"year",
                                "Offence Group":"offence_group",
                                "Age of Suspected Offender at Time of Offence":"suspected_offender_age",
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
        
        logger.info(f"Finished cleaning for table - {table_name}")
        
        df.to_sql(table_name, pg_engine, if_exists='replace', index=False)
        logger.info(f"Stored cleaned data in PostgreSQL for table - {table_name}")

        return True
    except Exception as e:
        logger.error(f"Error in transform_and_store: {e}")
        return False

# Step 3: Visualizations and Model
@op(ins={"transformed": In(bool)}, config_schema={"table_name": str})
def visualize(context,transformed):
    try:
        table_name = context.op_config["table_name"]
        
        if not transformed :
            logger.warning("Skipping analysis since data transformation failed.")
            return
        
        logger.info(f"Reading cleaned data from PostgreSQL from table - {table_name}...")
        if table_name == "crime_offence_garda":
            df = pd.read_sql(f'SELECT * FROM {table_name}', pg_engine)

            logger.info("Generating visualizations...")
            # --- Trend Analysis ---
            logger.info("Trend Analysis: Crime trends over time per offence")
            overall_crime_trend(df)
            quarterly_crime_trend(df)
            top_garda_divisions(df)
            
            logger.info("Seasonal Trend Analysis: Quarterly Patterns")
            quarterly_crime_trend_by_offence_type(df)
            average_crime_trend_by_offence_type(df)
            crime_distribution_per_quarter(df)

        else:
            df = pd.read_sql(f'SELECT * FROM {table_name}', pg_engine)

            logger.info("Generating visualizations...")
            logger.info("Age-Based Trend Analysis")
            crime_by_age(df)
            crime_age_heatmap(df)
            crime_age_bar_latest(df)
            
            logger.info("Temporal Shifts in Age-Related Crime Patterns")
            crime_age_bar_over_time(df)
            crime_age_area(df)

    except Exception as e:
        logger.error(f"Error in visualize_and_model: {e}")

@graph
def data_pipeline():
    fetched  = fetch_and_store_data()
    transformed = transform_and_store(fetched)
    visualize(transformed)