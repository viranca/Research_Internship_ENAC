import pandas as pd
import geopandas
from shapely.geometry import Polygon, Point
from shapely.ops import cascaded_union
import numpy as np
from math import sqrt

"""
Vertiports:

"""
traffic_level = "very_low"

def Create_vertiport_layer(traffic_level):
    #number of vertiports per municipality
    Innere_Stadt_n = 57
    Leopoldstadt_n = 39
    Landstraße_n = 32
    Wieden_n = 20
    Margareten_n = 18
    Mariahilf_n = 19
    Neubau_n = 20
    Josefstadt_n = 17
    Alsergrund_n= 24
    Favoriten_n = 64
    Simmering_n = 47
    Meidling_n = 26
    Hietzing_n = 76
    Penzing_n = 68
    Rudolfsheim_Fünfhaus_n = 15
    Ottakring_n = 18
    Hernals_n = 23
    Währing_n = 13
    Döbling_n= 50
    Brigittenau_n = 16
    Floridsdorf_n = 89
    Donaustadt_n = 205
    Liesing_n = 65
    
    
    Municipalities = ["Innere_Stadt", "Leopoldstadt", "Landstraße", "Wieden", "Margareten", "Mariahilf", "Neubau", "Josefstadt", "Alsergrund", "Favoriten", "Simmering", "Meidling",
                     "Hietzing", "Penzing", "Rudolfsheim_Fünfhaus", "Ottakring", "Hernals", "Währing", "Döbling", "Brigittenau", "Florisdorf", "Donaustadt", "Liesing"]
    Municipalities_n = [Innere_Stadt_n, Leopoldstadt_n, Landstraße_n, Wieden_n, Margareten_n, Mariahilf_n, Neubau_n, Josefstadt_n, Alsergrund_n, Favoriten_n, Simmering_n, Meidling_n, 
                      Hietzing_n, Penzing_n, Rudolfsheim_Fünfhaus_n, Ottakring_n, Hernals_n, Währing_n, Döbling_n, Brigittenau_n, Floridsdorf_n, Donaustadt_n, Liesing_n]
    Municipalities_d_ultra = [28.34551241, 23.57478382, 28.47042134, 28.62731574, 28.32816526, 28.22108797, 28.61815997, 27.66154569, 27.87915256, 19.29382534, 17.59254575, 27.91842961,
                              8.71283564, 10.97874895, 27.84299785, 27.66436150, 22.65084707, 28.76567204, 14.50567932, 28.18789891, 12.48669838, 6.49472159, 14.18409467]
    Municipalities_d_high = [24.01494801, 19.97308074, 24.12077363, 24.25369806, 24.00025112, 23.90953286, 24.24594108, 23.43547621, 23.61983759, 16.34615758, 14.90479570, 23.65311398,
                             7.38170797, 9.30144008, 23.58920651, 23.43786183, 19.19030099, 24.37091659, 12.28953386, 23.88141436, 10.57900835, 5.50247246, 12.01708021]
    Municipalities_d_medium = [19.68438362, 16.37137766, 19.77112593, 19.88008038, 19.67233699, 19.59797776, 19.87372220, 19.20940673, 19.36052261, 13.39848982, 12.21704566, 19.38779834,
                               6.05058031, 7.62413121, 19.33541517, 19.21136215, 15.72975491, 19.97616114, 10.07338841, 19.57492980, 8.67131832, 4.51022333, 9.85006575]
    Municipalities_d_low = [15.35381922, 12.76967457, 15.42147822, 15.50646269, 15.34442285, 15.28642265, 15.50150331, 14.98333725, 15.10120764, 10.45082206, 9.52929561, 15.12248271,
                            4.71945264, 5.94682235, 15.08162383, 14.98486248, 12.26920883, 15.58140569, 7.85724296, 15.26844524, 6.76362829, 3.51797419, 7.68305128]
    Municipalities_d_verylow = [11.02325483, 9.16797149, 11.07183052, 11.13284501, 11.01650871, 10.97486754, 11.12928443, 10.75726777, 10.84189266, 7.50315430, 6.84154557, 10.85716707,
                                3.38832497, 4.26951348, 10.82783250, 10.75836281, 8.80866275, 11.18665024, 5.64109751, 10.96196069, 4.85593826, 2.52572506, 5.51603682]
    
    if traffic_level == 'ultra':
        Municipalities_d = Municipalities_d_ultra
    elif traffic_level == 'high':
        Municipalities_d = Municipalities_d_high
    elif traffic_level == 'medium':
        Municipalities_d = Municipalities_d_medium
    elif traffic_level == 'low':
        Municipalities_d = Municipalities_d_low
    elif traffic_level == 'very_low':
        Municipalities_d = Municipalities_d_verylow
    else:
        raise ValueError('please check the traffic level spelling')
        
    #Geofence polygon:
    geofence_polygon_list = []
    for i in range(24):
        filename = 'Geofences_polygons/geofence' + str(i+1) + '.csv'
        geofence_df = pd.read_csv(filename)
        Corner_list = []
        for corner in geofence_df:
            corner = corner[1:]
            corner = corner.split(' ')
            corners = [float(i) for i in corner]
            Corner_list.append(corners)  
        geofence_polygon = Polygon(Corner_list)
        #print(geofence_polygon.area)
        geofence_polygon_list.append(geofence_polygon)
    #print(geofence_polygon_list)
    geofence_polygon_list = cascaded_union(geofence_polygon_list)
    
        
    def Create_polygon(municipality):
        filename = 'Municipality_polygons/' + str(municipality) + '.csv'
        #print(filename)
        nb_df = pd.read_csv(filename)
        Corner_list = []
        for corner in nb_df:
            corner = corner[1:]
            corner = corner.split(' ')
            corners = [float(i) for i in corner]
            Corner_list.append(corners)  
        polygon = Polygon(Corner_list)
        return polygon
    
    
    def Create_vertiports(polygon,N):
        xmin, ymin, xmax, ymax = polygon.bounds
        x = xmin 
        y = ymin
        x_loc = []
        y_loc = []
        demand = []
        Relative_size = []
        vertiport_increaser = 0
        while x < xmax:
            #print(x)
            while y < ymax:
                #print(y)
                if polygon.contains(Point(x,y)):
                    if sqrt((float(x) - 601213.43827)**2 + (float(y) - 5339982.41164)**2) <= 7975:
                        if geofence_polygon_list.contains(Point(x,y)) == False:
                            x_loc.append(x)
                            y_loc.append(y)
                            demand.append(Municipalities_d[N])
                            Relative_size.append(np.random.normal(1, 0.05))
                        else:
                            vertiport_increaser += 1
                resolution = sqrt(polygon.area/(Municipalities_n[N] + vertiport_increaser))
                y += resolution
            x += resolution
            y = ymin
        return x_loc, y_loc, demand, Relative_size
        
    
    x_loc = []
    y_loc = []
    demand = []
    Relative_size = []
    N=0
    for municipality in Municipalities:
        polygon = Create_polygon(municipality)
        x_loc_p, y_loc_p, demand_p, Relative_size_p = Create_vertiports(polygon,N)
        N += 1
        x_loc += x_loc_p
        y_loc += y_loc_p
        demand += demand_p
        Relative_size += Relative_size_p
       
    df = pd.DataFrame(
        {'x': x_loc,
         
         'y': y_loc,
         
         'demand': demand,
         
         'Relative_size': Relative_size})
    
    return df
    
    # df.to_csv('Vertiport_locations.csv')
    
    
    # gdf = geopandas.GeoDataFrame(
    #     df, geometry=geopandas.points_from_xy(df.x, df.y, df.demand), crs = 'EPSG:32633')
    
    
    # #print(gdf.head())
    
    
    # gdf.to_file("Vertiports.gpkg", layer='Vertiports', driver="GPKG")
    


        


