'''
FAST PATH PLANNER
'''

import osmnx as ox
from shapely.geometry import  LineString
import ast

class PathPlanner():
    def __init__(self, G, angle_cutoff=30):
        self.G = G
        # get edge geodataframe
        gdfs = ox.graph_to_gdfs(self.G)
        self.node_gdf = gdfs[0]
        self.edge_gdf = gdfs[1]

        # get edge indices
        self.edge_idx = list(self.edge_gdf.index.values)

        # get angle cutoff to label turns as turnbool
        self.angle_cutoff = angle_cutoff

    def route(self, origin_node, dest_node):

        # get route as a list of osmids
        osmid_route = ox.shortest_path(self.G, origin_node, dest_node)

        # get_correct_order of edges inside graph and reverese linestring geometry if necessary
        edge_geom_list = []
        for idx in range(len(osmid_route) - 1):

            edge_to_find = (osmid_route[idx], osmid_route[idx + 1], 0)

            # See if edge is in graph otherwise reverese u,v
            if edge_to_find in self.edge_idx:
                edge = edge_to_find
            else:
                edge = (edge_to_find[1], edge_to_find[0], 0)
            
            # check if geometry is in correct direction. if not flip geometry
            # use node of route to check in which  if it lines up with edge linestring
            line_geom = list(self.edge_gdf.loc[edge, 'geometry'].coords)

            lat_node = self.node_gdf.loc[osmid_route[idx], 'y']
            lon_node = self.node_gdf.loc[osmid_route[idx], 'x']

            if not (lon_node == line_geom[0][0] and lat_node == line_geom[0][1]):
                wrong_geom = line_geom
                wrong_geom.reverse()
                line_geom = list(LineString(wrong_geom).coords)

            # append edge and geometry for later use
            edge_geom_list.append((edge, line_geom))

        # calculate succesive interior angles and see which nodes are turn nodes
        int_angle_list = []
        turn_node_list = []
        for idx in range(len(edge_geom_list) - 1):
            current_edge = edge_geom_list[idx][0]
            next_edge = edge_geom_list[idx + 1][0]

            int_angle_dict = ast.literal_eval(self.edge_gdf.loc[current_edge, 'edge_interior_angle'])
            
            # get interior angle. search in current_edge
            try:
                interior_angle = int_angle_dict[next_edge]
            except KeyError:
                next_edge = (next_edge[1], next_edge[0], 0)
                interior_angle = int_angle_dict[next_edge]
            
            # get osmids of turn nodes
            if interior_angle < 180 - self.angle_cutoff:
                node_1 = current_edge[0]
                node_2 = current_edge[1]

                node_3 = next_edge[0]
                node_4 = next_edge[1]

                if node_1 == node_3 or node_1 == node_4:
                    node_to_append = node_1
                else:
                    node_to_append = node_2
                
                turn_node_list.append(node_to_append)

            int_angle_list.append(interior_angle)     

        # create list of lat lon for path finding
        lat_list = []
        lon_list = []
        lon_lat_list = []   # this is used for searching for turn nodes
        for edge_geo in edge_geom_list:
            edge = edge_geo[0]
            geom = edge_geo[1]

            # add all geometry info. adds the first node and second to last
            for idx in range(len(geom) - 1):
                lon = geom[idx][0]
                lat = geom[idx][1]

                lon_list.append(lon)
                lat_list.append(lat)
                lon_lat_list.append(f'{lon}-{lat}')
        
        # add destination node to lists becasue for loop above does not
        lon_dest = self.node_gdf.loc[dest_node, 'x']
        lat_dest = self.node_gdf.loc[dest_node, 'y']
        lon_list.append(lon_dest)
        lat_list.append(lat_dest)
        lon_lat_list.append(f'{lon_dest}-{lat_dest}')


        # find indices of turn_nodes
        turn_indices = []
        for turn_node in turn_node_list:
            
            # Find lat lon of current turn node
            lat_node = self.node_gdf.loc[turn_node, 'y']
            lon_node = self.node_gdf.loc[turn_node, 'x']

            index_turn = lon_lat_list.index(f'{lon_node}-{lat_node}')
            turn_indices.append(index_turn)

        # create turnbool. true if waypoint is a turn waypoint, else false
        turnbool = []
        for idx in range(len(lat_list)):
            if idx in turn_indices:
                turn_flag = True
            else:
                turn_flag = False
            
            turnbool.append(turn_flag)
                
        return lat_list, lon_list, turnbool
