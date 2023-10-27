import subprocess
import plotly.express as px
import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import requests
import zipfile
from io import BytesIO
pip install pydeck==0.7.1

# Data source URL (Replace with your GitHub Raw URL)
DATA_URL = "https://github.com/kira2906/NYC-Vehicle-Collision-using-Streamlit/raw/main/Motor_Vehicle_Collisions_-_Crashes_compressed.zip"

# Download data from the GitHub repository
response = requests.get(DATA_URL)

# Check if the download was successful
if response.status_code == 200:
    # Create a BytesIO buffer to read the zipped data
    zip_data = BytesIO(response.content)

    # Extract the data file from the zip
    with zipfile.ZipFile(zip_data, 'r') as zip_ref:
        # Assuming your data file is named 'data.csv' inside the zip
        with zip_ref.open('Motor_Vehicle_Collisions_-_Crashes_compressed.csv') as data_file:
            data = pd.read_csv(data_file)

    # Now you can work with the data as usual
else:
    st.error("Failed to download the data. Please check the URL or try again later.")

# Title Section
# Center-align the title using HTML/CSS
st.markdown(
    """
    <h1 style='text-align: center;'>NYC🗽 Vehicle Collision Data Explorer 🚗💥🚗</h1>
    """,
    unsafe_allow_html=True
)

# Insert the GIF
gif_url = "https://media.tenor.com/Cy7rKC7i-6gAAAAC/joseph-gordon-levitt-premium-crush.gif"
st.markdown(f'<p style="text-align:center"><img src="{gif_url}"></p>', unsafe_allow_html=True)
st.markdown(f'<p style="text-align:center">*Developed by Raihan Rasheed*</p>', unsafe_allow_html=True)
st.markdown("""
    This Streamlit application allows you to explore and analyze motor vehicle collision data in New York City (NYC). It provides insights into accident locations, injury and fatality statistics, contributing factors, and common vehicle types involved in collisions.

    ## Data Source
    The data used in this application is sourced from the [NYC Open Data platform](https://data.cityofnewyork.us/Public-Safety/Motor-Vehicle-Collisions-Crashes/h9gi-nx95).

    ## Sections

    ### Section 1 - Geo Spatial Analysis of Injured People

    1. **Map of Injured People**: This section allows you to filter and visualize locations where a specific number of people were injured in vehicle collisions on a map.

    2. **Map of Fatalities**: Similar to the previous section, this one visualizes locations where a certain number of people were killed in collisions.

    3. **Collisions by Time of Day**: This part shows the number of collisions that occurred during a given hour of the day. It includes a histogram and a map.

    ### Section 2 - In-depth Analysis of Accidents in NYC

    1. **Top Dangerous Streets**: You can choose the affected type of people (Pedestrians, Cyclists, or Motorists) and see the top 5 dangerous streets for that type.

    2. **Top Dangerous Boroughs**: Similar to the previous section, but it focuses on the most dangerous boroughs by the affected type of people.

    3. **Most Common Contributing Factors**: It displays the most common contributing factors in vehicle accidents in NYC.

    4. **Most Common Vehicle Types**: This part reveals the most common vehicle types involved in accidents.

    5. **Vehicle Accidents by Type**: You can select a specific vehicle type, and the map will display the locations of accidents involving that type.

    ## How to Use

    Simply run this Streamlit application and explore the various sections by selecting the options available. You can interact with maps, charts, and data to gain insights into motor vehicle collisions in NYC.

    *Note: The application provides visualizations and insights based on available data. Use it for informational purposes and to understand trends in vehicle collisions.*
""")

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

st.write("""
     ---
     ## Section 1 - Geo Spatial Analysis of Injured People
     """)

# Section 1 - Geo Spatial Analysis of Injured People
st.write("### Where are the most people injured in NYC?")
injured_people = st.slider("Number of persons injured in vehicle collisions", 1, 19)
st.map(data.query("injured_persons >= @injured_people")[["latitude", "longitude"]].dropna(how="any"))

st.write("### Where are the most people killed in NYC?")
killed_people = st.slider("Number of persons killed in vehicle collisions", 1, 4)
st.map(data.query("killed_persons >= @killed_people")[["latitude", "longitude"]].dropna(how="any"))

st.write("### How many collisions occur during a given time of day?")
hour = st.slider("Hour to look at", 0, 23)
data = data[data['date/time'].dt.hour == hour]
st.markdown(f'Vehicle collisions between {hour}:00 and {hour + 1}:00')

midpoint = (np.average(data['latitude']), np.average(data['longitude']))
st.pydeck_chart(pdk.Deck(
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

st.write("""
     ---
     ## Section 2 - In-depth Analysis of Accidents in NYC
     """)

# Section 2 - Graphical Analysis of Accidents in NYC
st.write("### Top 5 Dangerous streets by affected type")
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
# Rename the columns
dangerous_streets_count.columns = ['Street Name', 'Number of Incidents']
# Sort by the count in descending order
dangerous_streets_count = dangerous_streets_count.sort_values(by=['Number of Incidents'], ascending=False)

top_5_dangerous_streets = dangerous_streets_count.head(5)
table_html = top_5_dangerous_streets.to_html(index=False, justify='center')
st.markdown(table_html, unsafe_allow_html=True)

st.write("### Top 5 Dangerous Boroughs by affected type")
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

st.write("### Most Common Contributing Factors in Accidents")
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

st.write("### Most Common Vehicle Types in Accidents")
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

st.write("### Where are the most common vehicle accidents by vehicle type in NYC?")
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

st.markdown('''
        ---
#### Find the source code on GitHub
[GitHub Repository](https://github.com/kira2906/NYC-Vehicle-Collision-using-Streamlit/tree/main)

#### Ready to collaborate on data science and ML projects
*If you have similar projects or need assistance with data science and machine learning tasks, feel free to [contact me](mailto:mlsolutions.raihan@gmail.com). I'm available for freelance work and collaboration!*
''')
