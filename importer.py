import pdb
import arcpy
import csv

source = '5MBPLV_ ELECTION2019 (BGY_LEVEL) - EV Mother File Makabayan.csv'

with open(source,'rt') as infile:
    reader = csv.reader(infile)
    lookup = {("%s|%s|%s" % (row[1],row[2],row[3])).lower() : row[7] for row in reader}
        
# Create update cursor for feature class
with arcpy.da.UpdateCursor("D:\gis-training-files\PhilBaseMap_Visayas\PHL_Brgy.shp",
                           ['NAME_1','NAME_2','NAME_3','5MBPLV', "5MBPLV2022"]) as cursor:
    for row in cursor:
        # Update the values in the distance field by multiplying 
        #   the roadtype by 100. Road type is either 1, 2, 3 or 4.
        key = ("%s|%s|%s" % (row[0],row[1],row[2])).lower()
        if key in lookup.keys():
            row[4] = lookup[key]
            cursor.updateRow(row) 