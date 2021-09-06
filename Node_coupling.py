import pandas as pd
import geopandas as gpd
from scipy import spatial
import geopandas
from shapely.geometry import Polygon, Point
from shapely.ops import cascaded_union

#retrieve midway points:
nodes_df = gpd.read_file("center_points.gpkg")
nodes = []
for index, row in nodes_df.iterrows():
    nodes.append((list(row.geometry.coords)[0]))


##load distribution centers and vertiport locations + average hourly demand
Distribution_centers_df = pd.read_csv('Distribution_centers_locations.csv')
Vertiports_df = pd.read_csv('Vertiport_locations.csv')
df = Vertiports_df
gdf = geopandas.GeoDataFrame(
    df, geometry=geopandas.points_from_xy(df.x, df.y, df.demand), crs = 'EPSG:32633')
Vertiports_longlat = gdf.to_crs(crs = 'EPSG:4326', inplace = True)

df = Distribution_centers_df
gdf = geopandas.GeoDataFrame(
    df, geometry=geopandas.points_from_xy(df.x, df.y), crs = 'EPSG:32633')
Distribution_centers_longlat = gdf.to_crs(crs = 'EPSG:4326', inplace = True)


#constrained airspace polygon
constrained_airspace_df = pd.read_csv("constrained_airspace.csv")
Corner_list = []
j = 0
for corner in constrained_airspace_df:
    if j == 114:
        corner = "602136.759781778 5345414.06896959"
    corner = corner[:]
    corner = corner.split(' ')
    corners = [float(i) for i in corner]
    Corner_list.append(corners)  
    j += 1
#print(Corner_list)    
constrained_airspace_polygon = Polygon(Corner_list)
#constrained_airspace_polygon_list = list(constrained_airspace_polygon)


#retrieve midway points:
nodes_df = geopandas.read_file("center_points.gpkg")
nodes = []
for index, row in nodes_df.iterrows():
    nodes.append((list(row.geometry.coords)[0]))
nodes_df = pd.DataFrame.from_records(nodes)   
nodes_df.to_csv('Nodes_center_points.csv', header = False)

#%%
#append nodes to distribution centers:
Dcenter_nodelist_x_send_1 = []
Dcenter_nodelist_y_send_1 = []
Dcenter_nodelist_x_send_2 = []
Dcenter_nodelist_y_send_2 = []
Dcenter_nodelist_x_send_3 = []
Dcenter_nodelist_y_send_3 = []
for index, row in Distribution_centers_df.iterrows():
    x_port = list(row.geometry.coords)[0][0]
    y_port = list(row.geometry.coords)[0][1]
    #print(x_port, y_port)
    x = row['x']
    y = row['y']
    if constrained_airspace_polygon.contains(Point(x,y)):
        tree = spatial.KDTree(nodes)
        index_closest = tree.query([x_port, y_port])[1]
        x_node_send_1 = nodes[index_closest][0]
        y_node_send_1 = nodes[index_closest][1]
        nodes.pop(index_closest)
        tree = spatial.KDTree(nodes)
        index_closest = tree.query([x_port, y_port])[1]
        x_node_send_2 = nodes[index_closest][0]
        y_node_send_2 = nodes[index_closest][1]
        nodes.pop(index_closest) 
        tree = spatial.KDTree(nodes)
        index_closest = tree.query([x_port, y_port])[1]
        x_node_send_3 = nodes[index_closest][0]
        y_node_send_3 = nodes[index_closest][1]
        nodes.pop(index_closest) 
        Dcenter_nodelist_x_send_1.append(x_node_send_1)
        Dcenter_nodelist_y_send_1.append(y_node_send_1)
        Dcenter_nodelist_x_send_2.append(x_node_send_2)
        Dcenter_nodelist_y_send_2.append(y_node_send_2)
        Dcenter_nodelist_x_send_3.append(x_node_send_3)
        Dcenter_nodelist_y_send_3.append(y_node_send_3)
    else:
        Dcenter_nodelist_x_send_1.append(x_port)
        Dcenter_nodelist_y_send_1.append(y_port)
        Dcenter_nodelist_x_send_2.append(x_port - 0.000450000000)
        Dcenter_nodelist_y_send_2.append(y_port)
        Dcenter_nodelist_x_send_3.append(x_port + 0.000450000000)
        Dcenter_nodelist_y_send_3.append(y_port)       
Distribution_centers_df['node_x_send_1'] = Dcenter_nodelist_x_send_1
Distribution_centers_df['node_y_send_1'] = Dcenter_nodelist_y_send_1
Distribution_centers_df['node_x_send_2'] = Dcenter_nodelist_x_send_2
Distribution_centers_df['node_y_send_2'] = Dcenter_nodelist_y_send_2
Distribution_centers_df['node_x_send_3'] = Dcenter_nodelist_x_send_3
Distribution_centers_df['node_y_send_3'] = Dcenter_nodelist_y_send_3
Distribution_centers_df.to_csv('Distribution_centers_locations.csv')


#append nodes to vertiports:
vertiport_nodelist_x_send = []
vertiport_nodelist_y_send = []
vertiport_nodelist_x_recieve = []
vertiport_nodelist_y_recieve = []
for index, row in Vertiports_df.iterrows():
    x_port = list(row.geometry.coords)[0][0]
    y_port = list(row.geometry.coords)[0][1]
    #print(x_port, y_port)
    x = row['x']
    y = row['y']
    if constrained_airspace_polygon.contains(Point(x,y)):
        tree = spatial.KDTree(nodes)
        index_closest = tree.query([x_port, y_port])[1]
        x_node_send = nodes[index_closest][0]
        y_node_send = nodes[index_closest][1]
        nodes.pop(index_closest)
        tree = spatial.KDTree(nodes)
        index_closest = tree.query([x_port, y_port])[1]
        x_node_recieve = nodes[index_closest][0]
        y_node_recieve = nodes[index_closest][1]
        nodes.pop(index_closest)    
        vertiport_nodelist_x_send.append(x_node_send)
        vertiport_nodelist_y_send.append(y_node_send)
        vertiport_nodelist_x_recieve.append(x_node_recieve)
        vertiport_nodelist_y_recieve.append(y_node_recieve)
    else:
        vertiport_nodelist_x_send.append(x_port)
        vertiport_nodelist_y_send.append(y_port)
        vertiport_nodelist_x_recieve.append(x_port - 0.000450000000)
        vertiport_nodelist_y_recieve.append(y_port)
Vertiports_df['node_x_send'] = vertiport_nodelist_x_send
Vertiports_df['node_y_send'] = vertiport_nodelist_y_send
Vertiports_df['node_x_recieve'] = vertiport_nodelist_x_recieve
Vertiports_df['node_y_recieve'] = vertiport_nodelist_y_recieve
Vertiports_df.to_csv('Vertiport_locations.csv')






















































#%%
"""
#backup of working code
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


"""

























