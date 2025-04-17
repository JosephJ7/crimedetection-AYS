import plotly.express as px

def overall_crime_trend(df):
    overall_trend = df.groupby("year")["count"].sum().reset_index()
    overall_trend["count_10k"] = overall_trend["count"] / 10000
    fig1 = px.line(overall_trend, x="year", y="count_10k",
                title="Overall Crime Trend in Ireland (Yearly)",
                labels={"count_10k": "Total Recorded Crimes (in 10k)", "year": "Year"},
                markers=True)
    fig1.update_traces(line=dict(width=3))
    return fig1

def quarterly_crime_trend(df):
    quarter_trend = df.groupby(["year", "quarter_number"])["count"].sum().reset_index()
    fig2 = px.line(quarter_trend, x="year", y="count", color="quarter_number",
                title="Crime Trends by Quarter Over Years",
                labels={"count": "Crime Count", "year": "Year", "quarter_number": "Quarter"})
    fig2.update_traces(mode="lines+markers")
    return fig2

def top_garda_divisions(df):
    top_divisions = df.groupby("garda_division")["count"].sum().nlargest(5).reset_index()
    fig3 = px.pie(top_divisions,names="garda_division",values="count",hole=0.3, title="Top 5 Garda Divisions by Total Offences (Donut Chart)",color_discrete_sequence=px.colors.sequential.YlOrBr)
    fig3.update_traces(textinfo="percent+value")
    return fig3

def quarterly_crime_trend_by_offence_type(df):
    quarterly = df.groupby(['year', 'quarter_number', 'offence_type'])['count'].sum().reset_index()
    quarterly['quarter'] = quarterly['year'].astype(str) + '-' + quarterly['quarter_number']
    fig7 = px.line(quarterly, x='quarter', y='count', color='offence_type',
                title="Quarterly Crime Trends by Offence Type")
    fig7.update_layout(xaxis_tickangle=-45)
    return fig7

def average_crime_trend_by_offence_type(df):
    avg_quarter = df.groupby(['quarter_number', 'offence_type'])['count'].mean().reset_index()
    fig8 = px.bar(avg_quarter, x='quarter_number', y='count', color='offence_type',
                title="Average Crime per Quarter by Offence Type")
    return fig8

def crime_distribution_per_quarter(df):
    fig9 = px.box(df, x='quarter_number', y='count', color='offence_type',
                title="Crime Distribution per Quarter")
    return fig9

# def top_garda_divisions(df):
#     # Manual tagging of urban vs rural
#     urban_divs = ['Dublin Metropolitan Region', 'Cork City', 'Galway']
#     df['region_type'] = df['garda_division'].apply(lambda x: 'Urban' if x in urban_divs else 'Rural')

#     # Filter violent offences
#     violent = df[df['offence_type'].isin(['Homicide offences', 
#                                         'Attempts or threats to murder, assaults, harassments and related offences'])]

#     # 4.1 Line chart: Urban vs Rural trends for violent crimes
#     agg = violent.groupby(['year', 'region_type'])['count'].sum().reset_index()
#     fig10 = px.line(agg, x='year', y='count', color='region_type',
#                     title="Violent Crimes in Urban vs Rural Areas Over Time")
#     fig10.show()

#     # 4.2 Facet by offence type
#     facet = violent.groupby(['year', 'region_type', 'offence_type'])['count'].sum().reset_index()
#     fig11 = px.line(facet, x='year', y='count', color='region_type',
#                     facet_col='offence_type', title="Urban vs Rural by Offence Type")
#     fig11.show()

#     # 4.3 Bar chart for most recent year
#     latest = violent[violent['year'] == violent['year'].max()]
#     fig12 = px.bar(latest, x='garda_division', y='count', color='region_type',
#                 title=f"Violent Crime by Division in {latest['year'].max()}")
#     fig12.update_layout(xaxis_tickangle=-45)
#     fig12.show()


## table name crime_offence_age
def crime_by_age(df):
    # Line chart of total crimes per age group over time
    age_year_trend = df.groupby(['year', 'suspected_offender_age'])['count'].sum().reset_index()
    fig1 = px.line(age_year_trend, x='year', y='count', color='suspected_offender_age',
                        title="Detected Crimes by Age Group Over Time")    
    return fig1

def crime_age_heatmap(df):
    # Heatmap of crimes per age and year
    heatmap_data = df.pivot_table(index='suspected_offender_age', columns='year', values='count', aggfunc='sum')
    fig2 = px.imshow(heatmap_data, color_continuous_scale='Viridis',
                    title="Heatmap: Age Group vs Year (Crime Count)")
    return fig2

def crime_age_bar_latest(df):
    # Bar chart of age distribution in the latest year
    latest_year = df['year'].max()
    latest_df = df[df['year'] == latest_year].groupby('suspected_offender_age')['count'].sum().reset_index()
    fig3 = px.bar(latest_df, x='suspected_offender_age', y='count',
                title=f"Crime Count by Age Group in {latest_year}")
    return fig3

def crime_age_bar_over_time(df):
    # Animated bar chart: Age distribution of crime over time
    age_year_trend = df.groupby(['year', 'suspected_offender_age'])['count'].sum().reset_index()
    fig11 = px.bar(age_year_trend, x='suspected_offender_age', y='count',
                animation_frame='year', color='suspected_offender_age',
                title="Crime by Age Group (Animated Over Time)")   
    return fig11

def crime_age_area(df):
    # Area chart showing proportional age-based contribution over time
    age_year_trend = df.groupby(['year', 'suspected_offender_age'])['count'].sum().reset_index()
    age_year_trend['total'] = age_year_trend.groupby('year')['count'].transform('sum')
    age_year_trend['proportion'] = age_year_trend['count'] / age_year_trend['total']
    fig12 = px.area(age_year_trend, x='year', y='proportion', color='suspected_offender_age',
                    title="Proportional Contribution of Age Groups to Annual Crime")
    return fig12
