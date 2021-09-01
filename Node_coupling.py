import pandas as pd
import geopandas as gpd



time_gap = 10 #seconds

"""
Pseudocode node coupling:
For all Dcenters and Vports compute the necesarry arrival and departure points regarding a 10 second time gap
Couple the new nodes to the vertiports and dcenters
Distribute the planned flights over the these nodes
"""

#retrieve schedule:
schedule_from_D_total_df = pd.read_csv('schedule_from_D_total.csv')
schedule_from_v_total_df = pd.read_csv('schedule_from_v_total.csv')

#retrieve midway points:
nodes_df = gpd.read_file("center_points.gpkg")
nodes = []
for index, row in nodes_df.iterrows():
    nodes.append((list(row.geometry.coords)[0]))
nodes_df = pd.DataFrame.from_records(nodes)    

    




print(schedule_from_v_total_df)

for index, row in schedule_from_v_total_df.iterrows():
    print(row)
















#create flight schedule with nodes
flight_row_v = []
aircraft_id = 0
for flight in schedule_from_v:
    flight_row = []
    #append time of recieving flight plan: 00:00:00
    flight_row.append("00:00:00")
    
    #append aircraft ID:
    flight_row.append(aircraft_id)
    aircraft_id += 1
    
    #append aircraft type:
    flight_row.append("M600")
    
    #append flight departure time
    time_in_seconds = flight[2]
    whole_minutes = math.floor(time_in_seconds/60)   #make this round down
    whole_minutes = str(whole_minutes)
    if len(str(whole_minutes)) == 1:
        whole_minutes = "0" + str(whole_minutes)
    seconds_left = time_in_seconds - int(whole_minutes)*60
    if len(str(seconds_left)) == 1:
        seconds_left = "0" + str(seconds_left)            
    flight_row.append("00:" + str(whole_minutes) + ":"  + str(seconds_left))
    if len(flight) > 0:
        #append origin airport location
        x_loc_sending = list(Vertiports_df.iloc[flight[1]].geometry.coords)[0][0]
        y_loc_sending = list(Vertiports_df.iloc[flight[1]].geometry.coords)[0][1]
        #x_loc_sending = Vertiports_df.iloc[flight[1]]['x']
        #y_loc_sending = Vertiports_df.iloc[flight[1]]['y']
        flight_row.append('(' + str(x_loc_sending) + ', ' + str(y_loc_sending) + ')')

        #append recieving/destination airport locationn
        x_loc_recieving = list(Vertiports_df.iloc[flight[0]].geometry.coords)[0][0]
        y_loc_recieving = list(Vertiports_df.iloc[flight[0]].geometry.coords)[0][1]  
        #x_loc_recieving = Vertiports_df.iloc[flight[0]]['x']
        #y_loc_recieving = Vertiports_df.iloc[flight[0]]['y']    
        flight_row.append('(' + str(x_loc_recieving) + ', ' + str(y_loc_recieving) + ')')
    
    #add priority level (1 for now)
    flight_row.append(1)
    flight_row.append(time_in_seconds)
    flight_row_v.append(flight_row)

flight_row_D = []
for flight in schedule_from_D:
    flight_row = []
    #append time of recieving flight plan: 00:00:00
    flight_row.append("00:00:00")
    
    #append aircraft ID:
    flight_row.append(aircraft_id)
    aircraft_id += 1
    
    #append aircraft type:
    flight_row.append("M600")
    
    #append flight departure time
    time_in_seconds = flight[2]
    whole_minutes = math.floor(time_in_seconds/60)   #make this round down
    whole_minutes = str(whole_minutes)
    if len(str(whole_minutes)) == 1:
        whole_minutes = "0" + str(whole_minutes)
    seconds_left = time_in_seconds - int(whole_minutes)*60
    if len(str(seconds_left)) == 1:
        seconds_left = "0" + str(seconds_left)            
    flight_row.append("00:" + str(whole_minutes) + ":"  + str(seconds_left))
    if len(flight) > 0:
        #append origin airport location
        x_loc_sending = list(Distribution_centers_df.iloc[flight[1]].geometry.coords)[0][0]
        y_loc_sending = list(Distribution_centers_df.iloc[flight[1]].geometry.coords)[0][1]
        #x_loc_sending = Distribution_centers_df.iloc[flight[1]]['x']
        #y_loc_sending = Distribution_centers_df.iloc[flight[1]]['y']
        flight_row.append('(' + str(x_loc_sending) + ', ' + str(y_loc_sending) + ')')

        #append recieving/destination airport locationn
        x_loc_recieving = list(Vertiports_df.iloc[flight[0]].geometry.coords)[0][0]
        y_loc_recieving = list(Vertiports_df.iloc[flight[0]].geometry.coords)[0][1]                
        #x_loc_recieving = Vertiports_df.iloc[flight[0]]['x']
        #y_loc_recieving = Vertiports_df.iloc[flight[0]]['y']
        flight_row.append('(' + str(x_loc_recieving) + ', ' + str(y_loc_recieving) + ')')
    
    #add priority level (1 for now)
    flight_row.append(1)
    flight_row.append(time_in_seconds)
    flight_row_D.append(flight_row)


for i in flight_row_v:
    flight_schedule_unsorted.append(i)
for i in flight_row_D:
    flight_schedule_unsorted.append(i)            


#sort the flights and generate the flight schedule:
flight_schedule_df = pd.DataFrame.from_records(flight_schedule_unsorted)
flight_schedule_df = flight_schedule_df.sort_values(by=[flight_schedule_df.columns[7]])
flight_schedule_df = flight_schedule_df.drop(columns = [ flight_schedule_df.columns[7]])
flight_schedule_df.to_csv('original_vertiports_flight_schedule.csv', header = False, index = False)  
return flight_schedule_df




























