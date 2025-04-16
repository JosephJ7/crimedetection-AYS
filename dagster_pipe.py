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


# Step 1: Fetch raw data from API and store in MongoDB
@op(out=Out(),config_schema={"url": str, "table_name": str})
def fetch_and_store_data(context):
    try:
        url = context.op_config["url"]
        table_name = context.op_config["table_name"]
        
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
@op(ins={"fetched": In(bool)},out=Out(bool),config_schema={"table_name": str})
def transform_and_store(context,fetched):
    try:
        table_name = context.op_config["table_name"]
        if not fetched:
            logger.warning("Skipping transformation since data fetch failed.")
            return False
        
        records = list(mongo_db[table_name].find())
        df = pd.DataFrame(records)

        logger.info("Starting transformations")

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
        
        logger.info("Finished cleaning")
        
        df.to_sql(table_name, pg_engine, if_exists='replace', index=False)
        logger.info("Stored cleaned data in PostgreSQL")

        return True
    except Exception as e:
        logger.error(f"Error in transform_and_store: {e}")
        return False

# Step 3: Visualizations and Model
@op(ins={"transformed": In(bool)}, config_schema={"table_name": str})
def visualize_and_model(context,transformed):
    try:
        table_name = context.op_config["table_name"]
        
        if not transformed :
            logger.warning("Skipping analysis since data transformation failed.")
            return
        
        logger.info("Reading cleaned data from PostgreSQL...")
        df = pd.read_sql(f'SELECT * FROM {table_name}', pg_engine)
        logger.info(f"Data :{df.head()}")

        logger.info("Generating visualizations and running model...")
        if table_name == "crime_offence_garda":
            # --- Trend Analysis ---
            logger.info("Trend Analysis: Crime trends over time per offence")
            
            overall_trend = df.groupby("year")["count"].sum().reset_index()
            overall_trend["count_10k"] = overall_trend["count"] / 10000

            fig1 = px.line(overall_trend, x="year", y="count_10k",
                        title="Overall Crime Trend in Ireland (Yearly)",
                        labels={"count_10k": "Total Recorded Crimes (in 10k)", "year": "Year"},
                        markers=True)
            fig1.update_traces(line=dict(width=3))
            fig1.show()
            
            quarter_trend = df.groupby(["year", "quarter_number"])["count"].sum().reset_index()

            fig2 = px.line(quarter_trend, x="year", y="count", color="quarter_number",
                        title="Crime Trends by Quarter Over Years",
                        labels={"count": "Crime Count", "year": "Year", "quarter_number": "Quarter"})
            fig2.update_traces(mode="lines+markers")
            fig2.show()

            top_divisions = df.groupby("garda_division")["count"].sum().nlargest(5).reset_index()

            fig3 = px.pie(top_divisions,names="garda_division",values="count",hole=0.3, title="Top 5 Garda Divisions by Total Offences (Donut Chart)",color_discrete_sequence=px.colors.sequential.YlOrBr)

            fig3.update_traces(textinfo="percent+value")
            fig3.show()



        # # --- Regional Pattern Analysis ---
        # logger.info("Regional Pattern Analysis: Crime by Garda Division and Offence")
        # regional_df = df.groupby(['garda_division', 'offence_type'])['count'].sum().reset_index()
        # fig = px.bar(regional_df, x='garda_division', y='count', color='offence_type',title="Total Crime by Garda Division and Offence Type")
        # fig.update_layout(xaxis_tickangle=-45)
        # fig.show()
        
        # # --- Seasonal Trend Analysis ---
        # logger.info("Seasonal Trend Analysis: Offence type by quarter")
        # seasonal_df = df.groupby(['quarter_number', 'offence_type'])['count'].mean().reset_index()
        # fig = px.bar(seasonal_df, x='quarter_number', y='count', color='offence_type',title="Average Quarterly Crime by Offence Type")
        # fig.show()

        # # --- Urban-Rural Comparison (Manual Tag) ---
        # # Note: You would ideally have a column or mapping that classifies divisions as urban/rural.
        # # For now, we’ll mock a classification:
        # urban_divisions = ['Dublin Metropolitan Region', 'Cork City', 'Galway']
        # df['region_type'] = df['garda_division'].apply(
        #     lambda x: 'Urban' if x in urban_divisions else 'Rural'
        # )

        # violent_crimes = ['Attempts or threats to murder, assaults, harassments and related offences','Homicide offences']

        # urban_rural_df = df[df['offence_type'].isin(violent_crimes)].groupby(
        #     ['year', 'region_type', 'offence_type'])['count'].sum().reset_index()

        # fig = px.line(urban_rural_df, x='year', y='count',color='region_type', facet_col='offence_type',title="Urban vs Rural Trends for Violent Crimes Over Time")
        # fig.show()


    except Exception as e:
        logger.error(f"Error in visualize_and_model: {e}")

@job
def data_pipeline():
    fetched  = fetch_and_store_data()
    transformed = transform_and_store(fetched)
    visualize_and_model(transformed)



# # Plot with Seaborn
        # numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
        # if len(numeric_cols) >= 2:
        #     sns.pairplot(df[numeric_cols[:4]])
        #     plt.suptitle("Seaborn Pairplot", y=1.02)
        #     plt.show()
        #     # plt.savefig("seaborn_pairplot.png")

        #     # Plotly scatter
        #     fig = px.scatter(df, x=numeric_cols[0], y=numeric_cols[1], title='Plotly Scatter')
        #     fig.show() 
            
        #     fig = px.histogram(df, x=df.columns[0])
        #     fig.show() 
            # fig.write_html("plotly_scatter.html")

            # Linear Regression
            # X = df[[numeric_cols[0]]]
            # y = df[numeric_cols[1]]
            # model = LinearRegression()
            # model.fit(X, y)
            # r2 = model.score(X, y)
            # logger.info(f"Linear Regression R² score: {r2:.4f}")