from Create_distributioncenter_Layer import Create_distributioncenter_layer
from Create_vertiport_layer import Create_vertiport_layer
from Node_coupling import Node_coupling

'''
make sure that the df.to_csv and gdf.to_file are not commented out on the
bottom in the relevant python files
'''

Distribution_centers_locations = Create_distributioncenter_layer()
Vertiport_locations = Create_vertiport_layer('low')
Node_coupling(Distribution_centers_locations, Vertiport_locations)
