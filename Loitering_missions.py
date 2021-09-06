import geopandas
import pandas as pd
import re
import numpy as np

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
selected_flight_labels = [12, 44, 512]
negative_time_margin = 120 #seconds
positive_time_margin = 720 #seconds
loiter_area_side = 1500 #meter: square 500 by 500 meter



flightintention_df = pd.read_csv('Initial_flight_intention.csv')

def dist(x1, y1, x2 , y2):
    dist = ((x1 - x2)**2 + (y1 - y2)**2) ** 0.5
    return dist

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
#print(selected_flights)
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
#print(loiter_missions)
#start_time, end_time, x_min, x_max, y_min, y_max
    
#%%    
#find departing flights to remove from intention
to_be_removed = []
for loiter_mission in loiter_missions:
    for index, row in flightintention_df.iterrows():
        if row[3] >= loiter_mission[0] and row[3] <= float(loiter_mission[1]):
            if float(row[4][0]) >= loiter_mission[2] and float(row[4][0]) <= loiter_mission[3]:
                if float(row[4][1]) >= loiter_mission[4] and float(row[4][1]) <= loiter_mission[5]:
                    to_be_removed.append(index)
                    
#find arriving flights to remove from intention   


                 
print(len(to_be_removed))


































