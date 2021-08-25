# -*- coding: utf-8 -*-
"""
Created on Thu Jun  3 11:47:30 2021

@author: andub
"""
import osmnx as ox
import numpy as np
import BlueskySCNTools
from beta_path_planning import PathPlanner

# Initialize stuff
bst = BlueskySCNTools.BlueskySCNTools()

# Step 1: Import the graph we will be using
G = ox.io.load_graphml('Viranca.graphml')
nodes, edges = ox.graph_to_gdfs(G)
print('Graph loaded!')

# Step 2: Initalize the Path Planner class and read the flights
path_planner = PathPlanner(G)
flights = np.genfromtxt('preliminary_flight_schedule.csv', delimiter = ',', dtype = str)

traffic, routes, turnslist = bst.Viranca2Scn(G, flights, path_planner)
print('Traffic read!')

# Step 3: Loop through traffic, add to dictionary
scenario_dict = dict()
for i, flight in enumerate(traffic):
    # First get the route and turns
    route,turns= routes[i], turnslist[i]
    route = np.array(route)
    # Create dictionary
    scenario_dict[flight[0]] = dict()
    # Add start time
    scenario_dict[flight[0]]['start_time'] = flight[1]
    #Add lats
    scenario_dict[flight[0]]['lats'] = route[:,1]
    #Add lons
    scenario_dict[flight[0]]['lons'] = route[:,0]
    #Add turnbool
    scenario_dict[flight[0]]['turnbool'] = turns
    #Add alts
    scenario_dict[flight[0]]['alts'] = None

print('All paths created!')

# Step 4: Create scenario file from dictionary
bst.Dict2Scn('Scenarios/Test_Scenario.scn', scenario_dict)

print('Scenario file created!')