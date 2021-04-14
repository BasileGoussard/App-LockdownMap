#!/usr/bin/env python
# coding: utf-8

# In[33]:


#Data analysis
import pandas as pd 
pd.options.mode.chained_assignment = None  # default='warn'
import geopandas as gpd 

#Adress to location
import geopy 

#Open Street Map connection
import osmnx as ox

#Interactive widget
# from ipywidgets import interact_manual
# import ipywidgets as widgets

#Kepler mapping 
import keplergl
# from keplergl import KeplerGl

#Reading the config file
import json
import time

#Plotting
from geopy.extra.rate_limiter import RateLimiter

#Application
import streamlit as st
import streamlit.components.v1 as components


def main(adress):
    
    #Transform the input adress to a dataframe
    df_adress = pd.DataFrame({'adress' :  adress}, index = {0})
    
    #Init the geocoding and limit the rate 
    locator = geopy.geocoders.Nominatim(user_agent="mygeocoder")
    geocode = RateLimiter(locator.geocode, min_delay_seconds=0.1)
    
    #For the production
    try :
        
        st.text('adress found ! 👌 ')
        st.text('☕☕☕ Prepare yourself a coffee the map will arrive in 2 minute ! ☕☕☕')
        
        allowed_distance = 10000

        #Apply the geocoding to retrieve the lat & long
        df_adress["loc"]  = df_adress["adress"].apply(geocode)
        df_adress["lat"]  = df_adress["loc"].apply(lambda x : x[1][0])
        df_adress["lon"]  = df_adress["loc"].apply(lambda x : x[1][1])
        df_adress["city"] = df_adress["loc"].apply(lambda x : x[0].split(',')[4])

        #Create the geodataframe
        gdf = gpd.GeoDataFrame(df_adress, geometry = gpd.points_from_xy(df_adress.lon, df_adress.lat), crs = 'EPSG:4326')
        gdf['allowed_distance'] = allowed_distance
        
        

        #Create the max distance authorized
        gdf_lockdown = gpd.GeoDataFrame(df_adress, geometry = gpd.points_from_xy(df_adress.lon, df_adress.lat), crs = 'EPSG:4326')
        gdf_lockdown = gdf_lockdown.to_crs('EPSG:2154')
        gdf_lockdown['geometry'] = gdf_lockdown['geometry'].buffer(allowed_distance)
        gdf_lockdown = gdf_lockdown.to_crs('EPSG:4326')
    
        #Retrieve the value from osm, transform it to a geodataframe, reset the index and keep only the right columns
        gdf_city_edge = ox.graph_to_gdfs(ox.graph_from_polygon(gdf_lockdown['geometry'][0], network_type='drive'), nodes= False)[['name', 'highway', 'geometry']]   
    
        #Memory optimisations
        gdf_city_edge['highway'] = gdf_city_edge['highway'].apply(lambda x : str(x) )
        gdf_city_edge['highway'] = gdf_city_edge['highway'].astype("category") 
    
        gdf_city_edge['name'] = gdf_city_edge['name'].apply(lambda x : str(x) )
        gdf_city_edge['name'] = gdf_city_edge['name'].astype("category")


        available_street = gdf_city_edge['name'].copy().reset_index()['name'].drop_duplicates().dropna()

        st.sidebar.text('If the street is inside the list ')
        st.sidebar.text('the location is at less than 10km !')
        st.sidebar.selectbox('Available streets:', available_street)

        with open('config.json') as f:
            config = json.load(f)
            
        config['config']['mapState']['latitude'] = df_adress["lat"][0]
        config['config']['mapState']['longitude'] = df_adress["lon"][0]
        config['config']['mapStyle']['styleType'] = 'satellite'
     
        st.text('Map loading...')
  
        #Some modification on the confg file (use config = config to retrieve th last version)
        #kepler_map = keplergl.KeplerGl(height=400, data={"city lockdown": gdf_city_edge_reduce.copy(), "location" : gdf.drop(['loc'], axis = 1).copy(), "lockdown" : gdf_lockdown.drop(['loc'], axis = 1).copy()}, config = config)._repr_html_()
       
        #Init the map
        kepler_map = keplergl.KeplerGl(height=400)
    
        #Adding the data
        kepler_map.add_data(data=gdf_city_edge, name='city lockdown')
        kepler_map.add_data(data=gdf.drop(['loc'], axis = 1), name='location')
        kepler_map.add_data(data=gdf_lockdown.drop(['loc'], axis = 1), name = 'lockdown')
    
        #Adding the config
        kepler_map.config = config

        #Transform to a html file
        kepler_map_html = kepler_map._repr_html_()
    
        return(kepler_map_html)

    except : 
        
        print('location not found ! 😲')  


#Header
st.title('Interactive lockdown map from your location')

#Subheader
st.subheader('Made with ❤️  by Basile Goussard')

#User input
user_input = st.text_input("Your location", 'Planches, Trouville')

#Building the map
components.html(main(user_input), width=700, height=700)