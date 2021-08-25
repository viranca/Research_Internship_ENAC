# -*- coding: utf-8 -*-
"""
Created on Tue Jun  1 09:50:37 2021

@author: andub
"""
import numpy as np
import random
import osmnx as ox
import networkx as nx
nm = 1852
ft = 1/0.3048

class BlueskySCNTools():
    def Viranca2Scn(self, G, flights, path_planner):
        # First of all, the flights are weird. We want origins, destinations,
        # start times
        traffic = []
        routes = []
        turnslist = []
        
        for idx, flight in enumerate(flights):
            print(f'Flights done: {idx} out of {len(flights)}, or {int(idx/len(flights)*100)}%.')
            # Extract origins and destinations
            originlon = float(flight[4].replace('"(', ''))
            originlat = float(flight[5].replace(')"', ''))
            destlon = float(flight[6].replace('"(', ''))
            destlat = float(flight[7].replace(')"', ''))
            # Get origin and destination nodes
            orig_node = ox.nearest_nodes(G, originlon, originlat)
            dest_node = ox.nearest_nodes(G, destlon, destlat)
            # Do the path planning
            lats, lons, turns= path_planner.route(orig_node, dest_node)
            route = []
            for i in range(len(lats)):
                route.append((lons[i],lats[i]))
                
            # Add origin and destination to route in case it isn't there already
            route.insert(0, (originlon, originlat))
            turns.insert(0, True)
            route.append((destlon, destlat))
            turns.append(True)
            # Convert time to seconds
            routes.append(route)
            turnslist.append(turns)
            time = self.time2time(flight[3])
            traffic.append((f'D{idx}', time))
        
        return traffic, routes, turnslist

    def Drone2Scn(self, drone_id, start_time, lats, lons, turnbool, alts = None):
        """Converts arrays to Bluesky scenario files. The first
        and last waypoints will be taken as the origin and 
        destination of the drone.
    
        Parameters
        ----------
        drone_id : str
            The ID of the drone to be created
            
        start_time : int [sec]
            The simulation time in seconds at which the drone starts its 
            journey.
            
        turn_speed : float [kts]
            The speed with which to turn at turn waypoints in knots.
            
        lats : float array/list [deg]
            The lattitudes of the waypoints.
            
        lons : float array/list [deg]
            The longitudes of the waypoints.
            
        turnbool : bool array/list
            True if waypoint is a turn waypoint, else false.
            
        alts : float array/list, optional [ft]
            Defines the required altitude at waypoints.

        edge_ids: string array/list
            Each entry is the edge id. Only gets used if airspace=True

        airspace: Boolean, optional
            Flag that decides to use ADDWPTM2 command.
    
        """
        
        # Define the lines list to be returned
        lines = []
        
        # Speeds
        turn_speed = 10 # [kts]
        cruise_speed = 30 # [kts]
        speed_dist = 30 # [m]
        turn_dist = 30 # [m]
        speeds, turnbool = self.TurnSpeedBuffer(lats, lons, turnbool, alts, 
                            turn_speed, cruise_speed, speed_dist, turn_dist)
        
        # First, define some strings we will often be using
        trn = f'ADDWPT {drone_id} FLYTURN\n'
        trn_spd = f'ADDWPT {drone_id} TURNSPEED {turn_speed}\n'
        fvr = f'ADDWPT {drone_id} FLYBY\n'
        lnav = f'LNAV {drone_id} ON\n'
        vnav = f'VNAV {drone_id} ON\n'
        # Convert start_time to Bluesky format
        start_time = round(start_time)
        m, s = divmod(start_time, 60)
        h, m = divmod(m, 60)
        start_time_txt = f'{h:02d}:{m:02d}:{s:02d}>'
        
        # Everyone starts at 25ft above ground
        # First, we need to create the drone, Matrice 600 going 30 kts for now.
        # Let's calculate its required heading.
        qdr = self.qdrdist(lats[0], lons[0], lats[1], lons[1], 'qdr')

        cre_text = f'CRE {drone_id} M600 {lats[0]} {lons[0]} {qdr} 25 {turn_speed}\n'
        
        lines.append(start_time_txt + cre_text)
        
        # Then we need to for loop through all the lats
        prev_wpt_turn = False
        for i in range(1, len(lats)):
            if turnbool[i] == 1 or turnbool[i] == True:
                # We have a turn waypoint
                if prev_wpt_turn == False:
                    # The previous waypoint was not a turn one, we need to enter
                    # turn waypoint mode.
                    lines.append(start_time_txt + trn)
                    lines.append(start_time_txt + trn_spd)
            else:
                # Not a turn waypoint
                if prev_wpt_turn == True:
                    # We had a turn waypoint initially, change to flyover mode
                    lines.append(start_time_txt + fvr)

            # Airspace is off
            # Add the waypoint normally
            if alts is not None:
                wpt_txt = f'ADDWPT {drone_id} {lats[i]} {lons[i]} {alts[i]} {cruise_speed}\n'
            else:
                wpt_txt = f'ADDWPT {drone_id} {lats[i]} {lons[i]} ,, {cruise_speed}\n'
            
            lines.append(start_time_txt + wpt_txt)
            
            # Set prev waypoint type value
            prev_wpt_turn = turnbool[i]
        
        # Delete aircraft at destination waypoint
        lines.append(start_time_txt + f'{drone_id} ATDIST {lats[-1]} {lons[-1]} {16/nm} DEL {drone_id}\n')
        # Enable vnav and lnav
        lines.append(start_time_txt + vnav)
        lines.append(start_time_txt + lnav)

        return lines
    
    def Dict2Scn(self, filepath, dictionary, resometh = None, airspace = False):
        """Creates a scenario file from dictionary given that dictionary
        has the correct format.
    
        Parameters
        ----------
        filepath : str
            The file path and name of the scn file. 
            
        dictionary : dict
            This dictionary needs the format needed to use the Drone2Scn function.
            Drone_id is used as a main key, and then a sub dictionary is defined
            with the other variables.
            
            Example:
                dictionary = dict()
                dictionary['drone_id'] = dict()
                dictionary['drone_id']['start_time'] = start_time
                dictionary['drone_id']['lats'] = lats
                dictionary['drone_id']['lons'] = lons
                dictionary['drone_id']['truebool'] = turnbool
                dictionary['drone_id']['alts'] = alts
                
            Set alts as None if no altitude constraints are needed.
        
        airsace : bool
            A flag that decides to use the ADDWPT2 command that contains information 
            about airspace structure
    
        """
        if filepath[-4:] != '.scn':
            filepath = filepath + '.scn'
        
        with open(filepath, 'w+') as f:
            # Start with a hold so all the commands are added to the stack.
            #f.write('00:00:00>HOLD\n00:00:00>PAN 48.223775 16.337976\n00:00:00>ZOOM 50\n')
            # Add CR stuff
            # Add flights
            for drone_id in dictionary:
                try:
                    start_time = dictionary[drone_id]['start_time']
                    lats = dictionary[drone_id]['lats']
                    lons = dictionary[drone_id]['lons']
                    turnbool = dictionary[drone_id]['turnbool']
                    alts = dictionary[drone_id]['alts']
                except:
                    print('Key error. Make sure the dictionary is formatted correctly.')
                    return
                lines = self.Drone2Scn(drone_id, start_time, lats, lons, turnbool, alts)
                f.write(''.join(lines))
            # Add the final hold command
            f.write('01:05:00>HOLD\n')

    def Graph2Traf(self, G, concurrent_ac, aircraft_vel, max_time, dt, min_dist, 
                   orig_nodes = None, dest_nodes = None):
        """Creates random traffic using the nodes of graph G as origins and
        destinations.
    
        Parameters
        ----------
        G : graphml
            OSMNX graph, can be created using create_graph.py
            
        concurrent_ac : int
            The approximate number of aircraft flying at the same time.
            
        aircraft_vel : int/float [m/s]
            The approximate average velocity of aircraft
            
        max_time : int [s]
            The timespan for aircraft generation.
            
        dt : int [s]
            The time step to use. A smaller time step is faster but the number
            of concurrent aircraft will be less stable. 
            
        min_dist : int/float [m]
            The minimum distance a mission should have. This filters out the
            very short missions. 
            
        orig_nodes : list
            List of nodes to serve as the origin nodes. If not given, origin
            nodes will be taken randomly from existing ones.
            
        dest_nodes : list
            List of nodes to serve as destination nodes. If not given, destination
            nodes will be taken randomly from existing ones.
            
        Output
        ------
        (ID, start_time, origin, destination, path_length)
        
        ID : str
            The flight ID.
            
        start_time : int [s]
            The simulation time at which the flight should start.
            
        origin : (lat,lon) [deg]
            The origin of the flight.
            
        destination : (lat,lon) [deg]
            The destination of the flight
            
        length : float [m]
            The approximate length of the path.
    
        """
        nodes = []

        for node in G.nodes:
            nodes.append((G.nodes[node]['y'], G.nodes[node]['x'], node))
            
        # Some parameters
        timestep = 0
        ac_no = 1
        start_time = 0
        
        trafgen = []
        trafdist = np.empty((0,2))
        
        # Check if origins or destinations were given, otherwise just stick to
        # randomly spawning in network.
        if orig_nodes == None:
            origins = nodes.copy()
        else:
            # Create the origins list
            origins = []
            for node in nodes:
                if node[2] in orig_nodes:
                    origins.append(node)
                    
        # Do the same for destinations
        if dest_nodes == None:
            destinations = nodes.copy()
        else:
            # Create the origins list
            destinations = []
            for node in nodes:
                if node[2] in dest_nodes:
                    destinations.append(node)
        
        # This loop is for time steps
        while start_time <= max_time:
            possible_origins = origins.copy()
            possible_destinations = destinations.copy()
            
            # We want to keep track of what aircraft might have reached their
            # destinations.
            # Skip first time step
            if timestep > 0:
                for aircraft in trafdist:
                    i = np.where(np.all(trafdist==aircraft,axis=1))[0]
                    # Subtract a dt*speed from length for each aircraft
                    dist = float(aircraft[1]) - aircraft_vel * dt
                    if dist < 0:
                        # Aircraft probably reached its destination
                        trafdist = np.delete(trafdist, i, 0)
                    else:
                        trafdist[i, 1] = dist
            
            # Amount of aircraft we need to add
            decrement_me = concurrent_ac - len(trafdist)
            # This loop is for each wave
            while decrement_me > 0:
                # Pick a random node from possible_origins
                idx_origin = random.randint(0, len(possible_origins)-1)
                origin = possible_origins[idx_origin]
                # Do the same thing for destination
                idx_dest = random.randint(0, len(possible_destinations)-1)
                destination = possible_destinations[idx_dest]
                # Let's see how close they are
                orig_node = ox.distance.nearest_nodes(G, origin[1], origin[0])
                target_node = ox.distance.nearest_nodes(G, destination[1], destination[0])
                try:
                    length = nx.shortest_path_length(G=G, source=orig_node, target=target_node, weight='length')
                except:
                    # There is no solution to get from one node to the other
                    print('No path found for these two waypoints. Trying again.')
                    continue
                
                if length < min_dist:
                    # Distance is too short, try again
                    continue
                # Remove destinations and origins
                possible_origins.pop(idx_origin)
                possible_destinations.pop(idx_dest)
                # Append the new aircraft
                trafgen.append(('D'+str(ac_no), start_time, origin, destination, length))
                trafdist = np.vstack([trafdist, ['D'+str(ac_no),  length]])
                ac_no += 1
                decrement_me -= 1  
            # Go to the next time step
            timestep += 1
            start_time += dt
            
        return trafgen
    
    def Graph2Traf2(self, G, concurrent_ac, aircraft_vel, max_time, dt, min_dist, 
                   orig_points = None, dest_points = None):
        """Creates random traffic using the nodes of graph G as origins and
        destinations.
    
        Parameters
        ----------
        G : graphml
            OSMNX graph, can be created using create_graph.py
            
        concurrent_ac : int
            The approximate number of aircraft flying at the same time.
            
        aircraft_vel : int/float [m/s]
            The approximate average velocity of aircraft
            
        max_time : int [s]
            The timespan for aircraft generation.
            
        dt : int [s]
            The time step to use. A smaller time step is faster but the number
            of concurrent aircraft will be less stable. 
            
        min_dist : int/float [m]
            The minimum distance a mission should have. This filters out the
            very short missions. 
            
        orig_points : list
            List of points to serve as the origin nodes. If not given, origin
            nodes will be taken randomly from existing ones.
            
        dest_points : list
            List of points to serve as destination nodes. If not given, destination
            nodes will be taken randomly from existing ones.
            
        Output
        ------
        (ID, start_time, origin, destination, path_length)
        
        ID : str
            The flight ID.
            
        start_time : int [s]
            The simulation time at which the flight should start.
            
        origin : (lat,lon) [deg]
            The origin of the flight.
            
        destination : (lat,lon) [deg]
            The destination of the flight
            
        length : float [m]
            The approximate length of the path.
    
        """
        nodes = []

        for node in G.nodes:
            nodes.append((G.nodes[node]['y'], G.nodes[node]['x'], node))
            
        # Some parameters
        timestep = 0
        ac_no = 1
        start_time = 0
        
        trafgen = []
        trafdist = np.empty((0,2))

        # Create orig_nodes and dest_nodes by using osmnx closest node
        # These two should be np arrays with each row being one point lon lat
        orig_nodes = ox.nearest_nodes(G, orig_points[:,0], orig_points[:,1])
        
        if dest_points is not None:
            dest_nodes = ox.nearest_nodes(G, dest_points[:,0], dest_points[:,1])
            destinations = []
            for node in nodes:
                if node[2] in dest_nodes:
                    destinations.append(node)
        else:
            destinations = nodes.copy()

        origins = []
        for node in nodes:
            if node[2] in orig_nodes:
                origins.append(node)

        # This loop is for time steps
        while start_time <= max_time:
            possible_origins = origins.copy()
            possible_destinations = destinations.copy()
            
            # We want to keep track of what aircraft might have reached their
            # destinations.
            # Skip first time step
            if timestep > 0:
                for aircraft in trafdist:
                    i = np.where(np.all(trafdist==aircraft,axis=1))[0]
                    # Subtract a dt*speed from length for each aircraft
                    dist = float(aircraft[1]) - aircraft_vel * dt
                    if dist < 0:
                        # Aircraft probably reached its destination
                        trafdist = np.delete(trafdist, i, 0)
                    else:
                        trafdist[i, 1] = dist
            
            # Amount of aircraft we need to add
            decrement_me = concurrent_ac - len(trafdist)
            # This loop is for each wave
            while decrement_me > 0:
                # Pick a random node from possible_origins
                idx_origin = random.randint(0, len(possible_origins)-1)
                origin = possible_origins[idx_origin]
                # Do the same thing for destination
                idx_dest = random.randint(0, len(possible_destinations)-1)
                destination = possible_destinations[idx_dest]
                # Let's see how close they are
                orig_node = ox.distance.nearest_nodes(G, origin[1], origin[0])
                target_node = ox.distance.nearest_nodes(G, destination[1], destination[0])
                try:
                    length = nx.shortest_path_length(G=G, source=orig_node, target=target_node, weight='length')
                except:
                    # There is no solution to get from one node to the other
                    print('No path found for these two waypoints. Trying again.')
                    continue
                
                if length < min_dist:
                    # Distance is too short, try again
                    continue
                # Remove destinations and origins
                possible_origins.pop(idx_origin)
                possible_destinations.pop(idx_dest)
                # Append the new aircraft
                trafgen.append(('D'+str(ac_no), start_time, origin, destination, length))
                trafdist = np.vstack([trafdist, ['D'+str(ac_no),  length]])
                ac_no += 1
                decrement_me -= 1  
            # Go to the next time step
            timestep += 1
            start_time += dt
            
        return trafgen
    
    def qdrdist(self, latd1, lond1, latd2, lond2, mode):
        """ Calculate bearing and distance, using WGS'84
            In:
                latd1,lond1 en latd2, lond2 [deg] :positions 1 & 2
            Out:
                qdr [deg] = heading from 1 to 2
                d [m]    = distance from 1 to 2 in m """
    
        # Haversine with average radius for direction
    
        # Check for hemisphere crossing,
        # when simple average would not work
    
        # res1 for same hemisphere
        res1 = self.rwgs84(0.5 * (latd1 + latd2))
    
        # res2 :different hemisphere
        a    = 6378137.0       # [m] Major semi-axis WGS-84
        r1   = self.rwgs84(latd1)
        r2   = self.rwgs84(latd2)
        res2 = 0.5 * (abs(latd1) * (r1 + a) + abs(latd2) * (r2 + a)) / \
            (np.maximum(0.000001,abs(latd1) + abs(latd2)))
    
        # Condition
        sw   = (latd1 * latd2 >= 0.)
    
        r    = sw * res1 + (1 - sw) * res2
    
        # Convert to radians
        lat1 = np.radians(latd1)
        lon1 = np.radians(lond1)
        lat2 = np.radians(latd2)
        lon2 = np.radians(lond2)
    
        
        #root = sin1 * sin1 + coslat1 * coslat2 * sin2 * sin2
        #d    =  2.0 * r * np.arctan2(np.sqrt(root) , np.sqrt(1.0 - root))
        # d =2.*r*np.arcsin(np.sqrt(sin1*sin1 + coslat1*coslat2*sin2*sin2))
    
        # Corrected to avoid "nan" at westward direction
        d = r*np.arccos(np.cos(lat1)*np.cos(lat2)*np.cos(lon2-lon1) + \
                     np.sin(lat1)*np.sin(lat2))
    
        # Bearing from Ref. http://www.movable-type.co.uk/scripts/latlong.html
        coslat1 = np.cos(lat1)
        coslat2 = np.cos(lat2)
    
    
        qdr = np.degrees(np.arctan2(np.sin(lon2 - lon1) * coslat2,
            coslat1 * np.sin(lat2) - np.sin(lat1) * coslat2 * np.cos(lon2 - lon1)))
        
        if mode == 'qdr':
            return qdr
        elif mode == 'dist':
            return d
        else:
            return qdr, d
    
    def rwgs84(self, latd):
        """ Calculate the earths radius with WGS'84 geoid definition
            In:  lat [deg] (latitude)
            Out: R   [m]   (earth radius) """
        lat    = np.radians(latd)
        a      = 6378137.0       # [m] Major semi-axis WGS-84
        b      = 6356752.314245  # [m] Minor semi-axis WGS-84
        coslat = np.cos(lat)
        sinlat = np.sin(lat)
    
        an     = a * a * coslat
        bn     = b * b * sinlat
        ad     = a * coslat
        bd     = b * sinlat
    
        # Calculate radius in meters
        r = np.sqrt((an * an + bn * bn) / (ad * ad + bd * bd))
    
        return r
    
    def TurnSpeedBuffer(self, lats, lons, turnbool, alts, turnspeed, cruisespeed, speed_dist, turn_dist):
        """ Filters out waypoints that are very close to turn waypoints.
        

        Parameters
        ----------
        lats : array
            Waypoint latitudes
        lons : array
            Waypoint longitudes
        turnbool : bool array
            Whether waypoint is a turn waypoint or not.
        alts : array
            Altitude at waypoints.
        turnspeed : int [kts]
            The speed at which we are turning.
        cruisespeed : int[kts]
            The speed at which we are cruising.
        turndist : int [m]
            The buffer distance around a turn waypoint to filter for.

        Returns
        -------
        speeds : array
            The required speed at each waypoint.

        """
        # The buffer for waypoints after the turn doesn't need to be as big as
        # the buffer for before. Same with speed_dist
        future_turn_dist = turn_dist
        future_speed_dist = speed_dist
        # Number of waypoints
        num_wpts = len(lats)
        # Array that holds the speeds
        speeds = [cruisespeed] * num_wpts
        # Copy the turnbool over
        turnbool_new = turnbool.copy()
        for i in range(num_wpts):
            if turnbool[i] == 0 or turnbool[i] == False:
                # We're only interested in turn waypoints
                continue
            # If we get here, it's a turn waypoint
            speeds[i] = turnspeed
            # What we want to do is check both future and previous waypoints
            # to see if they are too close to the turn waypoint.
            # First, let's check previous waypoints
            cumulative_distance = 0
            # Initialize the iterator
            j = i - 1
            while j >= 0:
                dist2wpt = self.qdrdist(lats[j], lons[j], lats[j+1], lons[j+1], 'dist')
                cumulative_distance += dist2wpt
                if cumulative_distance < turn_dist:
                    turnbool_new[j] = 1
                if cumulative_distance < speed_dist:
                    speeds[j] = turnspeed
                    j = j - 1
                else:
                    break
            
            # Check future waypoints
            cumulative_distance = 0
            # Initialize the iterator
            j = i + 1
            while j < num_wpts:
                dist2wpt = self.qdrdist(lats[j], lons[j], lats[j-1], lons[j-1], 'dist')
                cumulative_distance += dist2wpt
                if cumulative_distance < future_turn_dist:
                    turnbool_new[j] = 1
                if cumulative_distance < future_speed_dist:
                    speeds[j] = turnspeed
                    j = j + 1
                else:
                    break                
              
        return speeds, turnbool_new

    def kwikdist(self, lata, lona, latb, lonb):
        """
        Quick and dirty dist [m]
        In:
            lat/lon, lat/lon [deg]
        Out:
            dist [m]
        """
    
        re      = 6371000.  # radius earth [m]
        dlat    = np.radians(latb - lata)
        dlon    = np.radians(((lonb - lona)+180)%360-180)
        cavelat = np.cos(np.radians(lata + latb) * 0.5)
    
        dangle  = np.sqrt(dlat * dlat + dlon * dlon * cavelat * cavelat)
        dist    = re * dangle
    
        return dist
    
    def time2time(self, timestr):
        ftr = [3600,60,1]
        return sum([a*b for a,b in zip(ftr, map(int,timestr.split(':')))])
