import geopandas
import pandas as pd
import re
import numpy as np
from random import randrange
from shapely.geometry import Polygon, Point
import random
import math

"""
Loitering mission pseudocode:
1. Read in the initial flight intention
2. select several flights [12, 44, 512]
3. create a polygon around the destination of these flights
4. find all the flights that have a destination or origin in these polygons from the time of departure of the selected flights [12, 44, 512] +- a certain margin 
5. redistribute these flights with the same probility map as for the initial flight intention, without the ports in the loitering polygons

#find flight in flight intention
#retreive departure timestamp and node
#retrieve arrival node
#compute distance
#compute time bounds with margins
#determine loitering polygon based on arrival node 
#determine the number of flights that depart or arrive in this polygon during the lotering time
#remove these flights
#run Make_poisson_tableu_schedule for the number of removed flights, but only for the loitering time and without the lotering area
#add the new flights to the intention in the correct line
"""

#input
negative_time_margin = 120 #seconds
positive_time_margin = 720 #seconds
loiter_area_side = 1500 #meter: square 500 by 500 meter
number_of_loitering_missions = 5

def Loitering_missions(traffic_level, Percentage_Dcenters, negative_time_margin, positive_time_margin, loiter_area_side, number_of_loitering_missions, sample):
    flightintention_df = pd.read_csv('Initial_flight_intention.csv')
    Distribution_centers_df = pd.read_csv('Distribution_centers_locations.csv')
    #Distribution_centers_df = Distribution_centers_df.drop(['Unnamed: 0', 'Latitude', 'Longitude'], axis = 1)
    
    def dist(x1, y1, x2 , y2):
        dist = ((x1 - x2)**2 + (y1 - y2)**2) ** 0.5
        return dist
    
    #converting the constrained airspace csv to the right crs:
    constrained_airspace_df = geopandas.read_file("updated_constrained_airspace.gpkg")
    #print(list(constrained_airspace_df.geometry.exterior[0].coords))
    Corner_list = []
    x_loc = []
    y_loc = []
    for corner in list(constrained_airspace_df.geometry.exterior[0].coords):
        corner = str(corner)
        corner = corner[1:-1]
        corner = corner.split(', ')
        corners = [float(i) for i in corner]
        Corner_list.append(corners)  
        x_loc.append(float(corner[0]))
        y_loc.append(float(corner[1]))
    df = pd.DataFrame(
        {'x': x_loc,
         'y': y_loc,})      
    gdf = geopandas.GeoDataFrame(
        df, geometry=geopandas.points_from_xy(df.x, df.y), crs = 'EPSG:32633')
    gdf.to_crs(crs = 'EPSG:4326', inplace = True)
    Corner_list = []
    for index, row in gdf.iterrows():
        Corner_list.append((list(row.geometry.coords)[0]))
    
    #create contstrained airspace Polygon
    constrained_airspace_polygon = Polygon(Corner_list)    

    """
    This was for the old constrained airspace:
    constrained_airspace_df = pd.read_csv("constrained_airspace.csv")
    Corner_list = []
    j = 0
    x_loc = []
    y_loc = []
    for corner in constrained_airspace_df:
        if j == 114:
            corner = "602136.759781778 5345414.06896959"
        corner = corner[:]
        corner = corner.split(' ')
        corners = [float(i) for i in corner]
        Corner_list.append(corners)  
        x_loc.append(float(corner[0]))
        y_loc.append(float(corner[1]))
        j += 1  
    df = pd.DataFrame(
        {'x': x_loc,
         'y': y_loc,})      
    gdf = geopandas.GeoDataFrame(
        constrained_airspace_df, geometry=geopandas.points_from_xy(df.x, df.y), crs = 'EPSG:32633')
    gdf.to_crs(crs = 'EPSG:4326', inplace = True)
    Corner_list = []
    for index, row in gdf.iterrows():
        Corner_list.append((list(row.geometry.coords)[0]))
    
    #create contstrained airspace Polygon
    constrained_airspace_polygon = Polygon(Corner_list)
    """
    
    #Transform string locations in flightintention to floats:
    sending_nodes = []
    recieving_nodes = []
    for index, row in flightintention_df.iterrows():
        sending_nodes.append(row[4])
        recieving_nodes.append(row[5])
    sending_nodes = list(set(sending_nodes))
    recieving_nodes = list(set(recieving_nodes))
    sending_nodes_float = []
    for i in sending_nodes:
        sending_nodes_float.append(re.findall("\d+\.\d+",i))
    recieving_nodes_float = []
    for i in recieving_nodes:
        recieving_nodes_float.append(re.findall("\d+\.\d+",i))   
    #print(sending_nodes_float, recieving_nodes_float)
    sending_nodes_float_x = []
    sending_nodes_float_y = []
    for i in sending_nodes_float:
        sending_nodes_float_x.append(i[0])
        sending_nodes_float_y.append(i[1])
    recieving_nodes_float_x = []
    recieving_nodes_float_y = []
    for i in recieving_nodes_float:
        recieving_nodes_float_x.append(i[0])
        recieving_nodes_float_y.append(i[1])
    
    
    list_of_potential_loiter = []
    for destination in range(len(recieving_nodes_float_x)):
        #print(destination)
        x = float(recieving_nodes_float_x[destination])
        y = float(recieving_nodes_float_y[destination])
        for index, row in Distribution_centers_df.iterrows():
            x_d = row['x']
            y_d = row['y']
            distance = dist(x, y, x_d, y_d)*111111
            if distance >= loiter_area_side/2:
                if constrained_airspace_polygon.contains(Point(x,y)):
                    #print("true")
                    list_of_potential_loiter.append(destination)
    list_of_potential_loiter = list(dict.fromkeys(list_of_potential_loiter))
    selected_flight_labels = random.sample(list_of_potential_loiter, number_of_loitering_missions)

    
    #retrieve flight info
    selected_flights = []
    for index, row in flightintention_df.iterrows():
        timestamp = row[3]
        timestamp = float(timestamp[0:2])*60*60 + float(timestamp[3:5])*60 + float(timestamp[6:8])
        row[3] = timestamp
        flightintention_df.iat[index, 3] = timestamp
        send_loc = row[4]
        send_loc = re.findall("\d+\.\d+",send_loc)    
        row[4] = send_loc
        flightintention_df.iat[index, 4] = send_loc
        recieve_loc = row[5]
        recieve_loc = re.findall("\d+\.\d+",recieve_loc)  
        row[5] = recieve_loc
        flightintention_df.iat[index, 5] = recieve_loc
        for label in selected_flight_labels:
            if row[1] == label:
                flight = []
                flight.append(index)  
                flight.append(row[1])
                flight.append(row[3])
                x_send = float(row[4][0])
                y_send = float(row[4][1])            
                flight.append(x_send)
                flight.append(y_send)
                x_rec = float(row[5][0])
                y_rec = float(row[5][1])           
                flight.append(x_rec)
                flight.append(y_rec)
                distance = dist(x_send, y_send, x_rec, y_rec)
                flight.append(distance * 111111)
                selected_flights.append(flight)
                
                #add loitering to flight intention     start time, duration, polygon                
                x_min = x_rec - ((loiter_area_side/2)/111111)
                x_max = x_rec + ((loiter_area_side/2)/111111)
                y_min = y_rec - ((loiter_area_side/2)/111111)
                y_max = y_rec + ((loiter_area_side/2)/111111)  
                start_time = row[3]
                flightintention_df.iat[index, 7] = start_time
                flightintention_df.iat[index, 8] = positive_time_margin
                flightintention_df.iat[index, 9] = x_min
                flightintention_df.iat[index, 10] = x_max
                flightintention_df.iat[index, 11] = y_min
                flightintention_df.iat[index, 12] = y_max
                #flightintention_df.iat[index, 9] = '(' + str(x_min) + ', ' + str(y_min) + '), ' + '(' + str(x_min) + ', ' + str(y_max) + '), ' + '(' + str(x_max) + ', ' + str(y_min) + '), ' + '(' + str(x_max) + ', ' + str(y_max) + ')' 
    #print('selected_flights', selected_flights)
    #line_number, label, timestamp, x_send, y_send, x_rec, y_rec, distance
    
    #print(flightintention_df.columns)
    #reveal_time, label, actype, timestamp, xy_send, xy_rec, priority
    
    #generate the loiter missions
    loiter_missions = []
    for flight in selected_flights:
        loiter_mission = []
        x_rec = flight[5]
        y_rec = flight[6]
        x_min = x_rec - ((loiter_area_side/2)/111111)
        x_max = x_rec + ((loiter_area_side/2)/111111)
        y_min = y_rec - ((loiter_area_side/2)/111111)
        y_max = y_rec + ((loiter_area_side/2)/111111)  
        start_time = flight[2] - negative_time_margin
        end_time = flight[2] + positive_time_margin
        loiter_mission.append(start_time)
        loiter_mission.append(end_time)
        loiter_mission.append(x_min)
        loiter_mission.append(x_max)
        loiter_mission.append(y_min)
        loiter_mission.append(y_max)   
        loiter_missions.append(loiter_mission)
    #print('loiter_missions', loiter_missions)
    #start_time, end_time, x_min, x_max, y_min, y_max
    
    
    #find departing flights to remove from intention
    to_be_removed = []
    to_be_removed_departing_index = []
    to_be_removed_departing = []
    for loiter_mission in loiter_missions:
        for index, row in flightintention_df.iterrows():
            if row[3] >= loiter_mission[0] and row[3] <= float(loiter_mission[1]):
                if float(row[4][0]) >= loiter_mission[2] and float(row[4][0]) <= loiter_mission[3]:
                    if float(row[4][1]) >= loiter_mission[4] and float(row[4][1]) <= loiter_mission[5]:
                        
                        to_be_removed_departing_index.append(index)
                        flight = []
                        for datapoint in row:
                            flight.append(datapoint)
                        to_be_removed_departing.append(flight)
                        to_be_removed.append(index)
                        
    #find arriving flights to remove from intention   
    to_be_removed_arriving_index = []
    to_be_removed_arriving = []
    for loiter_mission in loiter_missions:
        for index, row in flightintention_df.iterrows():
            if row[3] >= loiter_mission[0] and row[3] <= float(loiter_mission[1]):
                if float(row[5][0]) >= loiter_mission[2] and float(row[5][0]) <= loiter_mission[3]:
                    if float(row[5][1]) >= loiter_mission[4] and float(row[5][1]) <= loiter_mission[5]:
                        to_be_removed_arriving_index.append(index)
                        flight = []
                        for datapoint in row:
                            flight.append(datapoint)
                        to_be_removed_arriving.append(flight)
                        to_be_removed.append(index)
                        
    #Replace the conflicting locations with new locations.
    flightintention_loiter_df = flightintention_df.drop(to_be_removed, axis = 0)
    for index, row in flightintention_df.iterrows():
        flightintention_df.iat[index, 4] = '(' + str(flightintention_df.iloc[index, 4])[1:-1].replace("'", "") + ')'
        flightintention_df.iat[index, 5] = '(' + str(flightintention_df.iloc[index, 5])[1:-1].replace("'", "") + ')'
        if index in to_be_removed_departing_index:
            random_loc_selector = randrange(0, len(flightintention_loiter_df))
            new_loc = '(' + str(flightintention_loiter_df.iloc[random_loc_selector, 4])[1:-1].replace("'", "") + ')'
            flightintention_df.iat[index, 4] = new_loc
        if index in to_be_removed_arriving_index:
            random_loc_selector = randrange(0, len(flightintention_loiter_df))
            new_loc = '(' + str(flightintention_loiter_df.iloc[random_loc_selector, 5])[1:-1].replace("'", "") + ')'
            flightintention_df.iat[index, 5] = new_loc
            
        #append flight departure time
        time_in_seconds = int(row[3])
        whole_minutes = math.floor(time_in_seconds/60)   
        whole_minutes = str(whole_minutes)
        if len(str(whole_minutes)) == 1:
            whole_minutes = "0" + str(whole_minutes)
        seconds_left = time_in_seconds - int(whole_minutes)*60
        if len(str(seconds_left)) == 1:
            seconds_left = "0" + str(seconds_left)   
        flight_timestamp = "00:" + str(whole_minutes) + ":"  + str(seconds_left)    
        flightintention_df.iat[index, 3] = flight_timestamp    

        
        
    #print(flightintention_df)
    filename = 'Final_flight_intentions/' + 'Flight_intention_' + traffic_level + '_' + str(Percentage_Dcenters*100) + '_' + str(number_of_loitering_missions) + '_' + str(sample) + '.csv'
    flightintention_df.to_csv(filename, header = False, index = False)





