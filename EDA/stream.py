# assign session: didn't find why it's necessary here. 
# fips code: should county also be included?
# SIC change

# After installation of streamlit, type in terminal: streamlit run stream.py and view in chrome
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import geopandas as gpd
import json
import plotly.express as px


SIC_MAP = {"Livestock":51540000,
           "Livestock, nec":51549900,
           "Auctioning livestock":51549901,
           "Cattle":51549902,
           "Goats":51549903,
           "Hogs":51549904,
           "Sheep":51549905}

# read in data
df = pd.read_csv('auction_info.csv')

# filter data by state and sic code
def get_subset(df, condition_sic, condition_state):

    df_new = df[(df['State'].isin(condition_state)) & (df['SICDescription'].isin(condition_sic))]

    return df_new


## Functions
# revnue and count
def calculate_revenue(df, start_year, end_year):
    # Get revenue and count
    revenue = []
    auction_count = []
    for i in range(start_year,end_year+1):
        sales = "Sales"+str(i)[2:4]
        count = 'NAICS'+str(i)[2:4]
        revenue.append(round(df[sales].sum()/1000000,2))
        auction_count.append(df[count].count())
    # Create a new dataframe of time series data
    df_new = pd.DataFrame({
        'Year': range(start_year, end_year+1),
        'Revenue(Millions)': revenue,
        'Revenue/Auction(Thousands)': [round(a / b * 1000, 2) for a, b in zip(revenue, auction_count)],
        'Count': auction_count
    })
    return df_new


# revenue plot
def revenue_plot(df):
    fig, ax1 = plt.subplots()

    ax1.plot(df['Year'], df['Revenue(Millions)'], 'g-')  # 'g-' is for green solid line
    ax1.set_xlabel('Year')
    ax1.set_ylabel('Total Revenue(Millions)', color='g')

    ax2 = ax1.twinx()  
    ax2.plot(df['Year'], df['Revenue/Auction(Thousands)'], 'b-')  
    ax2.set_ylabel('Revenue/Auction(Thousands)', color='b')
    ax2.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    plt.title("Revenue of auction houses over the years")
    return plt


def count_plot(df):
    fig, ax = plt.subplots()
    ax.plot(df['Year'], df['Count'])  
    ax.set_xlabel('Count of Auction Houses')
    ax.set_ylabel('Total Count')
    ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    return fig


def flux_plot(df, start_year, end_year):
    fig, ax = plt.subplots()
    st.write()
    open_flux = pd.DataFrame(df['OpeningYear'].value_counts()).reset_index().rename(columns={"index":"OpeningYear",
                                                                                             "OpeningYear":"count"})
    close_flux= pd.DataFrame(df['ClosingYear'].value_counts()).reset_index().rename(columns={"index":"ClosingYear",
                                                                                             "ClosingYear":"count"})
    ax.bar(open_flux['OpeningYear'], open_flux['count'], label = 'open')
    ax.bar(close_flux['ClosingYear'], close_flux['count'], label = 'close')
    ax.set_ylabel('Count of auction houses open/close')
    ax.set_xlabel('Year')
    #ax.set_xticks(range(start_year, end_year + 1))
    #ax.set_xticklabels(range(start_year, end_year + 1), rotation=45)
    ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    plt.title('Auction House business flux(1990-2021)')

    plt.legend()
    return plt


def is_operational(year_to_check, opening_year, closing_year):
    if pd.isna(closing_year):
        closing_year = float('10000') # placeholder value for if it has not closed yet
    return opening_year <= year_to_check <= closing_year

def filter_by_operational_year(df, year_to_check):
    return df[df.apply(lambda x: is_operational(year_to_check, x['OpeningYear'], x['ClosingYear']), axis=1)]


def create_choropleth(df):
    # Aggregate data to get the count of auction houses per state
    state_counts = df.groupby('State').size().reset_index(name='AuctionHouseCount')

    # Load GeoJSON and merge with the aggregated data
    us_map = gpd.read_file('states.geojson')
    map_df = us_map.merge(state_counts, how='left', left_on='STUSPS', right_on='State')

    # Convert GeoDataFrame to JSON
    json_data = json.loads(map_df.to_json())

    # Create choropleth map using Plotly
    fig = px.choropleth(map_df,
                        geojson=json_data,
                        locations='STUSPS',
                        color='AuctionHouseCount',
                        featureidkey="properties.STUSPS",
                        hover_data=['NAME', 'AuctionHouseCount'],
                        scope="usa")
    fig.update_geos(fitbounds="locations")
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    return fig



## Create the app
sics = list(set(df['SICDescription']))
states = list(set(df['State']))

st.set_page_config(layout="wide") # whole page config set as fullscreen

with st.sidebar:
    st.title('RAFI Companies Analysis')
    st.subheader('Count, revenues and geolocation', divider='rainbow')
    st.text("")

    # Add a slider for selecting the year range
    year_range = st.slider(
        'Select Year Range',
        1990, 2022, (1990, 2022))

    # Slider for a single year
    selected_year = st.slider(
    'Select a Year For Map',
    min_value=1990,
    max_value=2022,
    value=2022, 
    step=1
    )

    # check for sic
    sic_options = st.multiselect(
        'Select SIC types', 
        sics,
        'Hogs')
    sic_all = st.checkbox('View all SIC types')
    # check for states
    state_option = st.multiselect(
    'Select a state', 
    states,
    'AL')
    state_all = st.checkbox('View all States')

    if sic_all and state_all:
        df2 = df
    elif sic_all:
        df2 = get_subset(df, sics, state_option) # select all sic types
    elif state_all:
        df2 = get_subset(df, sic_options, states)
    else: 
        df2 = get_subset(df, sic_options, state_option) # allows for multiple sic types
    
    df_revenue = calculate_revenue(df2, year_range[0], year_range[1])
    
    # filter for map data using df2
    year_column = 'SIC'+str(selected_year)[-2:]
    df_map = df2[df2[year_column].notnull()]
    # View original data
    with st.expander("View data for this filter"):
        dt = st.dataframe(df2) # used to check data
    # Apply filters to the DataFrame
    df_filtered_for_map = filter_by_operational_year(df2, selected_year)
    

# layout: 2*2 grid + 1 full-width display on bottom
c1, c2 = st.columns(2, gap="large")
c3, c4 = st.columns(2, gap="large") 
c5 = st.columns(1)

with c1:
    plot = st.pyplot(revenue_plot(df_revenue)) #revenue over the years
with c2:
    plot2 = st.pyplot(count_plot(df_revenue)) #count of auction houses
with c3:
    plot = st.map(data = df_map, latitude = 'Latitude', longitude = 'Longitude') # geographical
with c4:
    plot2 = st.pyplot(flux_plot(df2, year_range[0], year_range[1]))
with c5[0]:
    choropleth_fig = create_choropleth(df_filtered_for_map)
    plot = st.plotly_chart(choropleth_fig)