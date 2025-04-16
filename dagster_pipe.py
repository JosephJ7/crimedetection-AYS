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
def visualize(context,transformed):
    try:
        table_name = context.op_config["table_name"]
        
        if not transformed :
            logger.warning("Skipping analysis since data transformation failed.")
            return
        
        if table_name == "crime_offence_garda":
            logger.info("Reading cleaned data from PostgreSQL...")
            df = pd.read_sql(f'SELECT * FROM {table_name}', pg_engine)

            logger.info("Generating visualizations...")
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
            

            
            # 3.1 Line chart by quarter
            quarterly = df.groupby(['year', 'quarter_number', 'offence_type'])['count'].sum().reset_index()
            quarterly['quarter'] = quarterly['year'].astype(str) + '-' + quarterly['quarter_number']
            fig7 = px.line(quarterly, x='quarter', y='count', color='offence_type',
                        title="Quarterly Crime Trends by Offence Type")
            fig7.update_layout(xaxis_tickangle=-45)
            fig7.show()

            # 3.2 Bar chart: average crimes per quarter
            avg_quarter = df.groupby(['quarter_number', 'offence_type'])['count'].mean().reset_index()
            fig8 = px.bar(avg_quarter, x='quarter_number', y='count', color='offence_type',
                        title="Average Crime per Quarter by Offence Type")
            fig8.show()

            # 3.3 Box plot: variation in crimes across quarters
            fig9 = px.box(df, x='quarter_number', y='count', color='offence_type',
                        title="Crime Distribution per Quarter (Box Plot)")
            fig9.show()
            
            # Manual tagging of urban vs rural
            urban_divs = ['Dublin Metropolitan Region', 'Cork City', 'Galway']
            df['region_type'] = df['garda_division'].apply(lambda x: 'Urban' if x in urban_divs else 'Rural')

            # Filter violent offences
            violent = df[df['offence_type'].isin(['Homicide offences', 
                                                'Attempts or threats to murder, assaults, harassments and related offences'])]

            # 4.1 Line chart: Urban vs Rural trends for violent crimes
            agg = violent.groupby(['year', 'region_type'])['count'].sum().reset_index()
            fig10 = px.line(agg, x='year', y='count', color='region_type',
                            title="Violent Crimes in Urban vs Rural Areas Over Time")
            fig10.show()

            # 4.2 Facet by offence type
            facet = violent.groupby(['year', 'region_type', 'offence_type'])['count'].sum().reset_index()
            fig11 = px.line(facet, x='year', y='count', color='region_type',
                            facet_col='offence_type', title="Urban vs Rural by Offence Type")
            fig11.show()

            # 4.3 Bar chart for most recent year
            latest = violent[violent['year'] == violent['year'].max()]
            fig12 = px.bar(latest, x='garda_division', y='count', color='region_type',
                        title=f"Violent Crime by Division in {latest['year'].max()}")
            fig12.update_layout(xaxis_tickangle=-45)
            fig12.show()


        else:
            logger.info("Reading cleaned data from PostgreSQL...")
            df = pd.read_sql(f'SELECT * FROM {table_name}', pg_engine)

            logger.info("Generating visualizations...")
            # 1. Line chart of total crimes per age group over time
            age_year_trend = df.groupby(['year', 'suspected_offender_age'])['count'].sum().reset_index()
            fig1 = px.line(age_year_trend, x='year', y='count', color='suspected_offender_age',
                        title="Detected Crimes by Age Group Over Time")
            fig1.show()

            # 2. Heatmap of crimes per age and year
            heatmap_data = df.pivot_table(index='suspected_offender_age', columns='year', values='count', aggfunc='sum')
            fig2 = px.imshow(heatmap_data, color_continuous_scale='Viridis',
                            title="Heatmap: Age Group vs Year (Crime Count)")
            fig2.show()

            # 3. Bar chart of age distribution in the latest year
            latest_year = df['year'].max()
            latest_df = df[df['year'] == latest_year].groupby('suspected_offender_age')['count'].sum().reset_index()
            fig3 = px.bar(latest_df, x='suspected_offender_age', y='count',
                        title=f"Crime Count by Age Group in {latest_year}")
            fig3.show()
            

            # 11. Animated bar chart: Age distribution of crime over time
            fig11 = px.bar(age_year_trend, x='suspected_offender_age', y='count',
                        animation_frame='year', color='suspected_offender_age',
                        title="Crime by Age Group (Animated Over Time)")
            fig11.show()

            # 12. Area chart showing proportional age-based contribution over time
            age_year_trend['total'] = age_year_trend.groupby('year')['count'].transform('sum')
            age_year_trend['proportion'] = age_year_trend['count'] / age_year_trend['total']
            fig12 = px.area(age_year_trend, x='year', y='proportion', color='suspected_offender_age',
                            title="Proportional Contribution of Age Groups to Annual Crime")
            fig12.show()

    except Exception as e:
        logger.error(f"Error in visualize_and_model: {e}")

@job
def data_pipeline():
    fetched  = fetch_and_store_data()
    transformed = transform_and_store(fetched)
    visualize(transformed)