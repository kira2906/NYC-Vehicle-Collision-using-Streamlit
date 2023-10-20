import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk

import subprocess
# Upgrade pip using subprocess
subprocess.run(["/home/adminuser/venv/bin/python", "-m", "pip", "install", "--upgrade", "pip"])

import subprocess

# Define the pip command
pip_command = ['pip', 'install', 'plotly']

# Run the pip command as a subprocess
try:
    subprocess.run(pip_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print("plotly has been successfully installed.")
except subprocess.CalledProcessError as e:
    print("Error while installing plotly:", e)
    
import plotly.express as px

# Importing Data
DATA_URL = "D:\Data Science\IBM DATA SCIENCE\Projects\Data Science Web App with Streamlit and Python\Motor_Vehicle_Collisions_-_Crashes.csv"

# Title Section
st.title("Motor Vehicle Collisions in New York City")
st.markdown("This application is a Streamlit dashboard that can be used to analyze motor vehicle collisions in NYC")
st.markdown("Data Source: https://data.cityofnewyork.us/Public-Safety/Motor-Vehicle-Collisions-Crashes/h9gi-nx95")

# Data Cleansing
@st.cache_data(persist=True)


def load_data(nrows):
    data = pd.read_csv(DATA_URL, nrows=nrows, parse_dates=[['CRASH_DATE', 'CRASH_TIME']])
    data.dropna(subset=['LATITUDE', 'LONGITUDE'], inplace=True)
    data = data[(data['LATITUDE'] != 0) & (data['LONGITUDE'] != 0)]
    data.rename(str.lower, axis='columns', inplace=True)
    data.rename(columns={'crash_date_crash_time': 'date/time'}, inplace=True)
    return data

# Truncating Data for page performance
data = load_data(100000)
original_data = data

# Section 1 - Geo Spatial Analysis of Injured People
st.header("Where are the most people injured in NYC?")
injured_people = st.slider("Number of persons injured in vehicle collisions", 1, 19)
st.map(data.query("injured_persons >= @injured_people")[["latitude", "longitude"]].dropna(how="any"))

st.header("Where are the most people killed in NYC?")
killed_people = st.slider("Number of persons killed in vehicle collisions", 1, 19)
st.map(data.query("killed_persons >= @killed_people")[["latitude", "longitude"]].dropna(how="any"))

st.header("How many collisions occur during a given time of day?")
hour = st.slider("Hour to look at", 0, 23)
data = data[data['date/time'].dt.hour == hour]
st.markdown(f'Vehicle collisions between {hour}:00 and {hour + 1}:00')

midpoint = (np.average(data['latitude']), np.average(data['longitude']))
st.write(pdk.Deck(
    map_style="mapbox://styles/mapbox/light-v9",
    initial_view_state={
        'latitude': midpoint[0],
        'longitude': midpoint[1],
        'zoom': 11,
        'pitch': 50,
    },
    layers=[
        pdk.Layer(
            "HexagonLayer",
            data=data[['date/time', 'latitude', 'longitude']],
            get_position=['longitude', 'latitude'],
            radius=100,
            pickable=True,
            extruded=True,
            elevation_scale=4,
            elevation_range=[0, 1000],
        ),
    ]
))

st.subheader(f'Breakdown by minute between {hour}:00 and {hour + 1}:00')
filtered = data[(data['date/time'].dt.hour >= hour) & (data['date/time'].dt.hour < (hour + 1))]
hist = np.histogram(filtered['date/time'].dt.minute, bins=60, range=(0, 60))[0]
chart_data = pd.DataFrame({'minute': range(60), 'crashes': hist})
fig = px.bar(chart_data, x='minute', y='crashes', hover_data=['minute', 'crashes'], height=400)
st.write(fig)

# Section 2 - Graphical Analysis of Accidents in NYC
st.header('Top 5 Dangerous streets by affected type')
select = st.selectbox('Affected Type of People', 
                      ['Pedestrians', 'Cyclists', 'Motorists'])
if select == 'Pedestrians':
    dangerous_streets = original_data.query('injured_pedestrians >= 1')[['on_street_name', 'injured_pedestrians']]
elif select == 'Cyclists':
    dangerous_streets = original_data.query('injured_cyclists >= 1')[['on_street_name', 'injured_cyclists']]
else:
    dangerous_streets = original_data.query('injured_motorists >= 1')[['on_street_name', 'injured_motorists']]
# Group by street name and calculate the count
dangerous_streets_count = dangerous_streets.groupby('on_street_name').count().reset_index()
# Sort by the count in descending order
dangerous_streets_count = dangerous_streets_count.sort_values(by=['injured_pedestrians'], ascending=False)
# Rename the columns
dangerous_streets_count.columns = ['Street Name', 'Number of Incidents']
top_5_dangerous_streets = dangerous_streets_count.head(5)
table_html = top_5_dangerous_streets.to_html(index=False, justify='center')
st.markdown(table_html, unsafe_allow_html=True)

st.header('Top 5 Dangerous Boroughs by affected type')
select_typeforboroughs = st.selectbox('Affected Type of People', 
                                      ['Pedestrians', 'Cyclists', 'Motorists'], 
                                      key='unique_key_here')
if select_typeforboroughs == 'Pedestrians':
    borough_data = original_data.query('injured_pedestrians >= 1')[['borough', 'injured_pedestrians']].dropna(how='any')
elif select_typeforboroughs == 'Cyclists':
    borough_data = original_data.query('injured_cyclists >= 1')[['borough', 'injured_cyclists']].dropna(how='any')
else:
    borough_data = original_data.query('injured_motorists >= 1')[['borough', 'injured_motorists']].dropna(how='any')
# Group by borough and calculate the count
borough_data_count = borough_data['borough'].value_counts().reset_index()
borough_data_count.columns = ['Borough', 'Number of Incidents']
# Sort by the count in descending order
borough_data_count = borough_data_count.sort_values(by='Number of Incidents', ascending=False)
# Display the top 5 dangerous boroughs without the index column
st.markdown(borough_data_count.head(5).to_html(index=False, justify='center'), unsafe_allow_html=True)

st.header("Most Common Contributing Factors in Accidents")
# Extract contributing factor columns from the data in lowercase
contributing_factors = ['contributing_factor_vehicle_1', 
                        'contributing_factor_vehicle_2', 
                        'contributing_factor_vehicle_3']
# Combine contributing factor data from multiple columns into a single list
factor_counts = pd.concat([data[column] for column in contributing_factors], ignore_index=True)
# Remove 'Unspecified' values
factor_counts = factor_counts[factor_counts != 'Unspecified'].dropna()
# Count the frequency of each contributing factor
factor_counts = factor_counts.value_counts().reset_index(name='count').rename(columns={'index': 'Contributing Factor'})
# Display the bar chart
fig = px.bar(factor_counts.head(10), x='Contributing Factor', y='count', labels={'Contributing Factor': 'Factor', 'count': 'Frequency'})
st.plotly_chart(fig)

st.header("Most Common Vehicle Types in Accidents")
# Define the columns for vehicle types
vehicle_type_columns = ['vehicle_type_1', 
                        'vehicle_type_2', 
                        'vehicle_type_3', 
                        'vehicle_type_4', 
                        'vehicle_type_5']
# Combine vehicle type data from multiple columns into a single list
vehicle_type_counts = pd.concat([data[column] for column in vehicle_type_columns], ignore_index=True)
# Count the frequency of each vehicle type
vehicle_type_counts = vehicle_type_counts.value_counts().reset_index(name='count').rename(columns={'index': 'Vehicle Type'})
# Rename specific vehicle types
renaming_mapping = {
    'PASSENGER VEHICLE': 'SEDAN/HATCHBACK',
    'Sedan': 'SEDAN/HATCHBACK',
    'Taxi': 'TAXI',
    'Station Wagon/Sport Utility Vehicle': 'SPORT UTILITY / STATION WAGON',
    'Pick-up Truck': 'PICK-UP TRUCK'
}
vehicle_type_counts['Vehicle Type'] = vehicle_type_counts['Vehicle Type'].replace(renaming_mapping)
# Display the pie chart
fig = px.pie(vehicle_type_counts.head(10), names='Vehicle Type', values='count', hole=0.5,
             labels={'Vehicle Type': 'Type', 'count': 'Frequency'})
st.plotly_chart(fig)

st.header("Where are the most common vehicle accidents by vehicle type in NYC?")
for column in vehicle_type_columns:
    data[column] = data[column].replace(renaming_mapping)
# Create a list of unique vehicle types
unique_vehicle_types = pd.concat([data[column] for column in vehicle_type_columns]).value_counts().head(5).index
# Filter out 'unspecified' and empty values
unique_vehicle_types = [vtype for vtype in unique_vehicle_types if vtype and vtype != 'unspecified']
# Allow the user to select a vehicle type
select_vehicle_type = st.selectbox('Select Type of Vehicle', unique_vehicle_types)
# Filter data based on the selected vehicle type
filtered_data = data[
    (data['vehicle_type_1'] == select_vehicle_type) |
    (data['vehicle_type_2'] == select_vehicle_type) |
    (data['vehicle_type_3'] == select_vehicle_type) |
    (data['vehicle_type_4'] == select_vehicle_type) |
    (data['vehicle_type_5'] == select_vehicle_type)
]
# Display the map
st.map(filtered_data[['latitude', 'longitude']].dropna(how="any"))

if st.checkbox("Show Raw Data", False):
    st.subheader('Raw Data')
    st.write(data)
