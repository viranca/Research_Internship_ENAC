import pandas as pd
import geopandas
from shapely.geometry import Polygon, Point
from shapely.ops import cascaded_union
import numpy as np
from math import sqrt

"""
Vertiports:

"""
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
Municipalities_d = [29.52657543, 16.37137766, 28.75800135, 28.40011482, 29.50850548, 28.64319826, 28.39103171, 29.68726494, 29.04078392, 13.39848982, 12.21704566, 29.65192688,
                    6.050580305, 7.624131212, 28.35860892, 26.68244743, 15.72975491, 27.65930003, 10.07338841, 29.3623947, 8.671318321, 4.510223325, 9.850065746]

#%%
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


    
#%%

    
def Create_polygon(municipality):
    filename = 'Municipality_polygons/' + str(municipality) + '.csv'
    print(filename)
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

df.to_csv('Vertiport_locations.csv')


gdf = geopandas.GeoDataFrame(
    df, geometry=geopandas.points_from_xy(df.x, df.y, df.demand), crs = 'EPSG:32633')


#print(gdf.head())


gdf.to_file("Vertiports.gpkg", layer='Vertiports', driver="GPKG")


        


