


"""
Loitering mission pseudocode:
1. Read in the initial flight intention
2. select several flights [12, 44, 512]
3. create a polygon around the destination of these flights
4. find all the flights that have a destination or origin in these polygons from the time of departure of the selected flights [12, 44, 512] +- a certain margin 
5. redistribute these flights with the same probility map as for the initial flight intention, without the ports in the loitering polygons

"""



    



negative_margin = 120 #seconds
positive_margin = 720 #seconds













