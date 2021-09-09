import pandas as pd
import geopandas 
import numpy as np
from statistics import mean
import math


##load distribution centers and vertiport locations + average hourly demand
Distribution_centers_df = pd.read_csv('Distribution_centers_locations.csv')
Vertiports_df = pd.read_csv('Vertiport_locations.csv')

Distribution_centers_df = Distribution_centers_df.drop(['Unnamed: 0', 'Latitude', 'Longitude'], axis = 1)
Vertiports_df = Vertiports_df.drop(['Unnamed: 0'], axis = 1)

#%%
"""
Distribution centers Dataframe format:
,Unnamed: 0,x,y,Relative_size,Number_of_ports,geometry,node_x_send_1,node_y_send_1,node_x_send_2,node_y_send_2,node_x_send_3,node_y_send_3

Vertiports Dataframe format:
Label, x_location, y_location, Municipal_demand, relative_vport_size, 

"""
##input variables (independent variables for schedule)
#total demand (very high, high, medium, low, very low)
#proportion of traffic from Dcenters (30, 50, 80)
#number of loitering missions and radius 

#rogue aircraft (1%, 3%, 5%, 8%, 10%) #this will be added manually after

##Fixed variables:
#proportion of vertiport demand that will come from distribution centers:
Percentage_Dcenters = 0.85
Percentage_closest_Dcenters = 0.80
Number_of_Dcenters_per_vertiport = 5
timesteps = 3600 #3600



"""
##Method pseudo code:
    
for every vertiport in Vertipors_df:
    1. Find the four closest Distribution centers and make them very important (increase their priority temporarily).
    2. Compute the lambda's (demand rates) for vertiports and for distribution centers:
        - Percentage_Dcenter will come from Distribution centers:
            * Based on the relative size and distance, divide the lambda across all the distribution centers.
        - The remaining percentage will come from other vertiports:
            * Based on the relative size and distance, divide the lambda across all the vertiports. 
    3. Draw from a poisson process with the previously obtained lambda's in a timeframe of all timesteps.
    4. Save the labels of the recieving and sending points at every time.
Based on this create the flight schedule in the requested format.
        
"""


def dist(x1, y1, x2 , y2):
    dist = ((x1 - x2)**2 + (y1 - y2)**2) ** 0.5
    return dist


def Distance_distribution_centers(x1, y1):
    dist_list = []
    for index, row in Distribution_centers_df.iterrows():
        x2 = row['x']
        y2 = row['y']
        dist_D_center = dist(x1, y1, x2 , y2)
        dist_list.append(dist_D_center)
    return dist_list

def Create_distribution_center_priority(Distribution_centers_df, dist_list):
    relative_size_list = []
    for index, row in Distribution_centers_df.iterrows():
        relative_size_d = row['Relative_size']
        relative_size_list.append(relative_size_d)
    
    #find the Index/label of the closest D centers:
    K = Number_of_Dcenters_per_vertiport
    four_closest_index = sorted(range(len(dist_list)), key = lambda sub: dist_list[sub])[:K]
    
    priority_sum = 0
    for Dcenter in range(len(relative_size_list)):
        priority_sum +=relative_size_list[Dcenter]
        #print(priority_sum)
        #17.12042308855761    
    
    #increase the relative size of the K-closest D centers:
    non_closest_index = list(range(len(relative_size_list)))
    non_closest_index = [x for x in non_closest_index if x not in four_closest_index]
    for close_Dcenter in four_closest_index:
        #non_closest_index.pop(close_Dcenter)
        relative_size_list[close_Dcenter]  = relative_size_list[close_Dcenter] * priority_sum * (Percentage_closest_Dcenters/Number_of_Dcenters_per_vertiport) 
    #decrease the relative size of the non K-closest D centers:
    for non_close_Dcenter in non_closest_index:
        relative_size_list[non_close_Dcenter]  = relative_size_list[close_Dcenter] * priority_sum * ((1-Percentage_closest_Dcenters)/(16 - Number_of_Dcenters_per_vertiport)) 
    
    #compute priority
    priority_list = []
    dist_percentage_list = []
    for Dcenter_i in range(len(relative_size_list)):
        dist_percent = (dist_list[Dcenter_i]/sum(dist_list))
        dist_percentage_list.append(dist_percent)
        
    for Dcenter_i in range(len(relative_size_list)):
        priority = (relative_size_list[Dcenter_i]/sum(relative_size_list) ) + (dist_percentage_list[Dcenter_i] - mean(dist_percentage_list))
        priority_list.append(priority)
    
    #replace negative values with zero, perhaps reduce the other priorities accordingly in the future.
    priority_list_Dcenters = [0 if i<0 else i for i in priority_list]
    return priority_list_Dcenters
    
#repeat Create_distribution_center_priority for vertiports.
def Create_vertiport_priority(Vertiports_df):
    relative_size_list = []
    for index, row in Vertiports_df.iterrows():
        relative_size_d = row['Relative_size']
        relative_size_list.append(relative_size_d)
        
    priority_list_vertiports = []
    for vertiport in range(len(relative_size_list)):
        priority_percentage = relative_size_list[vertiport]/sum(relative_size_list)
        priority_list_vertiports.append(priority_percentage)

    return priority_list_vertiports
    

   
def Make_poisson_tableu_schedule(priority_list_vertiports, Vertiports_df, Distribution_centers_df):
    label_recieving_vertiport = 0
    label_recieving_vertiport2 = 0
    flight_schedule_unsorted = []
    schedule_from_v_total = []
    schedule_from_D_total = []
    aircraft_id = 0
    for recieving_vertiport in range(len(priority_list_vertiports)):
        #Retrieve municipal demand
        Total_demand = Vertiports_df.iloc[recieving_vertiport]['demand']
        #compute lambda and make initial split
        Total_lambda = (Total_demand/3600)
        Total_lambda_vertiports = (1-Percentage_Dcenters) * Total_lambda
        Total_lambda_Dcenters = Percentage_Dcenters * Total_lambda
        
        #recompute the Dcenter priority list
        x1 = Vertiports_df.iloc[recieving_vertiport]['x']
        y1 = Vertiports_df.iloc[recieving_vertiport]['y']
        dist_list = Distance_distribution_centers(x1, y1)
        priority_list_Dcenters = Create_distribution_center_priority(Distribution_centers_df, dist_list)
             
        #Distribute lambda over all vertiports and Dcenters based on their priority lists
        Lambda_list_vertiports = Total_lambda_vertiports * np.array(priority_list_vertiports)
        Lambda_list_Dcenters = Total_lambda_Dcenters * np.array(priority_list_Dcenters)
        
        #for each entry in the vertiport lambda lists run a poisson process over the timesteps
        label_sending_vertiport = 0
        schedule_from_v = []
        for vertiport_lambda in Lambda_list_vertiports:
            Traffic_i = np.random.poisson(vertiport_lambda ,timesteps)
            timestep_index = 0
            for timestep_traffic in Traffic_i:
                flight =[]
                if timestep_traffic == 1:
                    flight.append(label_recieving_vertiport)
                    flight.append(label_sending_vertiport)
                    flight.append(timestep_index)
                    #schedule_from_v.append(flight)
                    #flight.append(list(Vertiports_df.iloc[label_sending_vertiport].geometry.coords)[0][0])
                    #flight.append(list(Vertiports_df.iloc[label_sending_vertiport].geometry.coords)[0][1])
                    #flight.append(list(Vertiports_df.iloc[label_recieving_vertiport].geometry.coords)[0][0])
                    #flight.append(list(Vertiports_df.iloc[label_recieving_vertiport].geometry.coords)[0][1])                    
                    #schedule_from_v_total.append(flight)
                timestep_index += 1
            label_sending_vertiport += 1
        label_recieving_vertiport += 1

        #for each entry in the Dcenter lambda lists run a poisson process over the timesteps      
        label_sending_dcenter = 0
        schedule_from_D = []
        for dcenter_lambda in Lambda_list_Dcenters:
            Traffic_i = np.random.poisson(dcenter_lambda ,timesteps)
            timestep_index = 0
            for timestep_traffic in Traffic_i:
                flight =[]
                if timestep_traffic == 1:
                    flight.append(label_recieving_vertiport2)
                    flight.append(label_sending_dcenter)
                    flight.append(timestep_index)
                    schedule_from_D.append(flight)
                    #flight.append(list(Distribution_centers_df.iloc[label_sending_dcenter].geometry.coords)[0][0])
                    #flight.append(list(Distribution_centers_df.iloc[label_sending_dcenter].geometry.coords)[0][1])
                    #flight.append(list(Vertiports_df.iloc[label_recieving_vertiport2].geometry.coords)[0][0])
                    #flight.append(list(Vertiports_df.iloc[label_recieving_vertiport2].geometry.coords)[0][1])
                    #schedule_from_D_total.append(flight)
                timestep_index += 1
            label_sending_dcenter += 1
        label_recieving_vertiport2 += 1
        
        
        flight_row_v = []
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
                #port location:
                x_loc_sending = Vertiports_df.iloc[flight[1]]['node_x_send'] 
                y_loc_sending = Vertiports_df.iloc[flight[1]]['node_y_send']              
                
                #find closest node to port location
                #tree = spatial.KDTree(nodes)
                #index_closest = tree.query(x_loc_sending_port, y_loc_sending_port)[1]

                #append origin node location
                #x_loc_sending = nodes[index_closest][0]
                #y_loc_sending = nodes[index_closest][1]
                
                flight_row.append('(' + str(x_loc_sending) + ', ' + str(y_loc_sending) + ')')
                
                #find closest node to port location
                
                #append recieving/destination airport locationn
                x_loc_recieving = Vertiports_df.iloc[flight[0]]['node_x_recieve'] 
                y_loc_recieving = Vertiports_df.iloc[flight[0]]['node_y_recieve']                 
                #x_loc_recieving = Vertiports_df.iloc[flight[0]]['x']
                #y_loc_recieving = Vertiports_df.iloc[flight[0]]['y']    
                flight_row.append('(' + str(x_loc_recieving) + ', ' + str(y_loc_recieving) + ')')
            
            #add priority level (1 for now)
            flight_row.append(1)
            flight_row.append(time_in_seconds)
            flight_row_v.append(flight_row)
    
        flight_row_D = []
        port_selector = 0
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
                if port_selector == 0:
                    x_loc_sending = Distribution_centers_df.iloc[flight[1]]['node_x_send_1']
                    y_loc_sending = Distribution_centers_df.iloc[flight[1]]['node_y_send_1']
                    port_selector += 1
                elif port_selector == 1:
                    x_loc_sending = Distribution_centers_df.iloc[flight[1]]['node_x_send_2']
                    y_loc_sending = Distribution_centers_df.iloc[flight[1]]['node_y_send_2']
                    port_selector += 1
                else:
                    x_loc_sending = Distribution_centers_df.iloc[flight[1]]['node_x_send_3']
                    y_loc_sending = Distribution_centers_df.iloc[flight[1]]['node_y_send_3']
                    port_selector = 0                   
                flight_row.append('(' + str(x_loc_sending) + ', ' + str(y_loc_sending) + ')')

                #append recieving/destination airport locationn
                x_loc_recieving = Vertiports_df.iloc[flight[0]]['node_x_recieve'] 
                y_loc_recieving = Vertiports_df.iloc[flight[0]]['node_y_recieve']                
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
    flight_schedule_df.to_csv('Initial_flight_intention.csv', header = False, index = False)
    
    #df = pd.DataFrame(schedule_from_D_total) 
    #df.to_csv('schedule_from_D_total.csv', header = False) 
    #df = pd.DataFrame(schedule_from_v_total) 
    #df.to_csv('schedule_from_v_total.csv', header = False)     
    return flight_schedule_df
    

priority_list_vertiports = Create_vertiport_priority(Vertiports_df)
Schedule = Make_poisson_tableu_schedule(priority_list_vertiports, Vertiports_df, Distribution_centers_df)






