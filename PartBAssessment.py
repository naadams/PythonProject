#Student ID : 13173421
# import necessary modules to run the program
import arcpy
import os
from arcpy.sa import *
# ran into encoding error with "utf-8" characters when trying to write the chinese names to a csv
# found this workaround for python 2.7 
import sys
reload(sys)
sys.setdefaultencoding('utf8')
print("setting up environment")
# set the working folder.  Given the way the files are grouped i assigned different folders to different variables to be
# called later when switching between the raster data and the shapefiles
arcpy.env.overwriteOutput = True
china_folder = R"C:\Users\Dell\Desktop\prog_gis_coursework-2020\prog_gis_coursework\part_b_china_lights\china_data\CHN_adm_shp"
raster_infolder =  R"C:\Users\Dell\Desktop\prog_gis_coursework-2020\prog_gis_coursework\part_b_china_lights\china_data"
arcpy.env.workspace = china_folder
outfolder = arcpy.env.workspace + R"\Results"
# create a results folder to store the output files in
print("checking results folder")
if os.path.exists(outfolder):
    print("Folder Exists")
else:
    print("Creating folder:")
    os.makedirs(outfolder)
results_folder = R"C:\Users\Dell\Desktop\prog_gis_coursework-2020\prog_gis_coursework\part_b_china_lights\china_data\CHN_adm_shp\Results"
# function that loads the spatial analysit if available
print("checking spatial extension")
if arcpy.CheckExtension("spatial") == "Available":
	arcpy.CheckOutExtension("spatial") # acquire license
	print("Spatial analyst exists")
else:
	# function fails if unable to acquire the license
	raise RuntimeError("Spatial Analyst license is not available")

# make lists the field names i'll be creating and writing data to throughout the program
fclist = arcpy.ListFeatureClasses()
field_names = ["ADMIN_LVL", "ADMIN_ID", "ADMIN_NAME", "LUM_SUM93", "LUM_MEAN93",  
              "LUM_SUM13", "LUM_MEAN13", "L_M_CHNG", "L_SUM_CHNG", "AREA_SQKM"]
raster_fields = ["LUM_SUM93", "LUM_MEAN93", "LUM_SUM13", "LUM_MEAN13", "L_M_CHNG", "L_SUM_CHNG"]
# unique name field for each of the provinces. Will transfer the names from these fields to the ADMIN_NAME field
fields = ["NAME_ENGLI","NAME_1","NAME_2", "NAME_3"]
lum_fields = ["LUM_MEAN93", "LUM_MEAN13", "LUM_SUM93", "LUM_SUM13"]

# Project all of the input datasets in order to make a more accurate
# calculation for the AREA.  The raster data must be projected as well
# or it wont calculate the zonal statistics correctly.
# def project_fc():
    # print("projecting the shapefiles and rasters")
    # print("Found {0} feature classes: {1}".format(len(fclist),fclist))
    # raster1993 = raster_infolder + R"\F101993-night_lights\F101993-night_lights.tif"
    # raster2013 = raster_infolder + R"\F101993-night_lights\F182013-night_lights.tif"
    # arcpy.DefineProjection_management(raster1993, "7564.prj")
    # arcpy.DefineProjection_management(raster2013, "7564.prj")
    # for fc in fclist:
        # print("projecting {0} with {1}".format(fc, "7564.prj"))
        # arcpy.DefineProjection_management(fc, "7564.prj")
    
# function to add new fields to each feature class in the working folder
# this will allow each shapefiles attribute table to have standardized field names to write to the csv files
def create_fields():
    print("creating the proper fields")
    for fc in fclist:
        for field in field_names:
            print("creating field name {0} in {1}".format(field, fc))
            # assign the fields different data types depending on what information theyll be storing
            if field == "ADMIN_NAME":
                arcpy.AddField_management(fc, field, "TEXT")
            elif field == "ADMIN_LVL" or field == "ADMIN_ID":
                arcpy.AddField_management(fc, field, "LONG")
            else:
                arcpy.AddField_management(fc, field, "DOUBLE")

# function for calculating values for the recently created fields
def calculate_vals():
    #initialize 2 variables.  lvl will be a counter for the administrative level field
    # index is used in the search cursor to pull the correct name field from each shapefile
    lvl = 0
    index = 0
    print("calculating the values for the new fields")
    # 3 loops to calculate and write all the values
    for fc in fclist:
        print("Updating field values in {0}".format(fc))
        # open an update cursor for the fields to populate with values
        cursor = arcpy.da.UpdateCursor(fc, ["ADMIN_LVL", "ADMIN_ID", "AREA_SQKM", "ADMIN_NAME"])
        # this search cursor can calculate the polygon areas and since the name fields are all called
        # something different in each shapefile as you loop through each shapefile the fields[index] pulls
        # the appropriate name field for each.
        cursor2 = arcpy.da.SearchCursor(fc, ["SHAPE@AREA", fields[index]])
        # intialize a counting variable for the Admin_ID field
        admin = 1
        # loop through the update cursor. the row should be 4 empty values so you will assign the values in order
        # according to how the fields are ordered
        for row in cursor:
            # first two fields updated are the ADMIN_LVL and the ADMIN_ID 
            # admin lvl starts at 0 and admin id starts at 1
            row[0] = lvl
            row[1] = admin
            # this loop uses the search cursor to calculate the area of each polygon and pull the appropriate name
            # then assign that value to a variable to be called later in the update cursor loop
            for i in cursor2:
                area =i[0]
                name = i[1]
                # used a break here to exit the loop because otherwise it just overwrites the value on each iteration
                break
            # noticed the area values were off by a factor of 1000, so adjusted the values
            # now you have the proper values for all 4 of the fields in the update cursor
            row[2] = area * 10000
            row[3] = name
            # update the row with the 4 values
            cursor.updateRow(row)
            # add 1 on each iteration through the row in cursor loop to the ID field 
            admin = admin + 1
        print("{0} successfully updated".format(fc))
        # add one to the Admin lvl ID on each iteration through the fc in fclist loop
        # add one to the index variable so you are indexing the fields list properly
        # and you get the corresponding name field depending on which FC you're in
        lvl = lvl + 1
        index = index + 1
    # clean up the cursors
    del cursor
    del cursor2
# function for carrying out the zonal statistics on the luminosity rasters
def calc_lum_vals():
    # access and store the 1993 and 2013 raster data using arcpy.Raster()
    # tried to use mostly relative paths so but couldnt figure out a way around having the raster path here
    print("Accessing raster data from 1993")
    raster1993 = raster_infolder + R"\F101993-night_lights\F101993-night_lights.tif"
    raster1993 = arcpy.Raster(raster1993)
    print("Accessing raster data from 2013")
    raster2013 = raster_infolder + R"\F182013-night_lights\F182013-night_lights.tif"
    raster2013 = arcpy.Raster(raster2013)
    # initialize a variable for the output file names
    level = 0
    # looping through all the fc's
    for fc in fclist:
        # USed the table option for the zonal statistics because it put all the information 
        # for the created fields into a table to be looped through
        print("Calculating raster statistics for year 1993 in feature class {0}".format(fc))
        # Use the "level" variable for the output names to identify the admin_lvl for each raster table
        # this block of code creates tables for the SUM and MEAN in 1993 and 2013 for each admin lvl
        # it uses the newly created ADMIN_ID as a unique variable defining an area to do the zonal statistics on
        outtable = outfolder + R"\SUM1993_" + str(level)
        sum_1993 = arcpy.sa.ZonalStatisticsAsTable(fc, "ADMIN_ID", raster1993, outtable, "DATA","SUM")
        outtable= outfolder + R"\MEAN1993_" + str(level)
        mean_1993 = arcpy.sa.ZonalStatisticsAsTable(fc, "ADMIN_ID", raster1993, outtable, "DATA", "MEAN")
        print("Calculating raster statistics for year 2013 in feature class {0}".format(fc))
        outtable = outfolder + R"\SUM2013_" + str(level)
        sum_2013 = arcpy.sa.ZonalStatisticsAsTable(fc, "ADMIN_ID", raster2013, outtable, "DATA", "SUM")
        outtable = outfolder + R"\MEAN2013_" + str(level)
        mean_2013 = arcpy.sa.ZonalStatisticsAsTable(fc, "ADMIN_ID", raster2013, outtable, "DATA", "MEAN")
        level = level + 1
    # clean up temp rasters
    del raster1993
    del raster2013
    del sum_1993
    del mean_1993
    del sum_2013
    del mean_2013

# this function updates the mean and sum values for 1993 and 2013
def update_lum_vals():
    # intialize an array to store all the mean and sum values in
    val = []
    # change the workspace to the results folder because thats where the tables that were created earlier were saved
    arcpy.env.workspace = results_folder
    # put the tables in a list to be looped through.  Using the sort arrainges the tables in the correct order
    # so the list is storing all the mean values first starting in 1993 to 2013 and then the sum values
    tables = arcpy.ListTables()
    tables.sort()
    print("update the luminosity fields")
    # start a loop through each table.  The only value in the table you need is the SUM or MEAN value 
    # it can be pulled from the table by indexing the row at the 4th position.
    for table in tables:
        cursor2 = arcpy.da.SearchCursor(table, "*")
        print("adding luminosity values from {0} to an array".format(table))
        for row in cursor2:
            val.append(row[4])
    del cursor2
    # change the workspace back to the folder with the shapefiles in it so you can loop through them
    # initialize a variable to be used to index the val list. This will pull the value from the list
    # and add it to the corresponding field in the shapefile
    i = 0
    arcpy.env.workspace = china_folder
    # Loop through the list called lum_fields which contains the field names of the luminosity fields 
    # you want to update.  
    for field in lum_fields: # for MEAN1993 in the lum_fields list
        for fc in fclist: # for china_adm_shp in the feature class list
            print("updating {0} values in {1}".format(field, fc))
            # Open an update cursor on the given field in the loop
            cursor = arcpy.da.UpdateCursor(fc, field) # update the current field in lum_fields
            # nested loop grabs the value from the val list and adds it to the appropriate field
            for row in cursor: # for each row in the shapefile 
                row[0] = val[i] # update the "field" with the corresponding value from the array
                cursor.updateRow(row)
                # just add 1 to the i variable so it indexes the next value in the list each time
                i = i+1
    del cursor
    # After the mean and sum values have been added you need to calculate the percent change from 93-2013
    for fc in fclist:
        print("calculating the percent change in luminosity for {0}".format(fc))
        # open an update cursor for the fields you're updating
        cursor = arcpy.da.UpdateCursor(fc, ["L_M_CHNG", "L_SUM_CHNG"])
        # open a search cursor to access the values youll use to calculate the change
        cursor2 = arcpy.da.SearchCursor(fc, lum_fields)
        for row in cursor2:
            # formula for calculating a percent change is ((x2-x1)/x1) * 100
            # take the 2013 value - 1993 value and divide by the 1993 value, * 100 to make it a percent figure
            m_chng = ((row[1]-row[0])/row[0]) * 100
            s_change = ((row[3]-row[2])/row[2]) * 100
            # use a loop to add these values to the fields selected in the update cursor
            for change in cursor:
                cursor.updateRow([m_chng, s_change])
                # again break out of the loop each time so you arent overwriting the value each time
                break
        print("percent change values in {0} successfully calculated".format(fc))
    del cursor
    del cursor2    
# now that you have all the values calculated and standardized across each shapefile you can write them to a csv
def write_csv():
    # for each shapefile 
    for fc in fclist:
        # formatting, split the fc name at the "." and then index the variable you assigned it to so you have the first part of 
        # the name, then add a .csv to the end when it saves
        x = fc.split(".")
        outpath = results_folder + "/" + x[0] + ".csv"
        # create the csv file with the name you set previously, and set its status to "write"
        csv = open(outpath, "w")
        # open a cursor to search for all the values from the fields you created and populated
        cursor = arcpy.da.SearchCursor(fc, field_names)
        print("set up header for {0}.csv".format(x[0]))
        # creates a header with the field names at the top of each csv file
        for field in field_names:
            csv.write(field + ",")
        csv.write("\n")
        print("header for {0}.csv created".format(x[0]))
        print("writing values from {0} to {1}.csv".format(fc, x[0]))
        # Got some weird encoding errors here and never totally sorted it out
        # trying to convert the names to a string had some errors because of the
        # special characters in the chinese names. I had to convert to a string as it was the only way to concenate with the commas
        # These nested loops take each value in the rows and writes it to the csv file
        # followed by a comma and then a line break at the end of each row
        for row in cursor:
            for val in row:
                val =str(val) 
                csv.write(val + ",")
            csv.write("\n")
        print("values for {0} successful, check {1} for file".format(fc, outpath))
        csv.close()
    del cursor
# export the maps.  I had to manually create the map document and wasnt sure what the assignment meant by "show the luminosity"
# So I overlayed the raster file from 2013 and then added the luminosity "SUM" value in yellow on top of each province
# Using a chloropleth only gave a range, and adding individual values gave a legend that had 31 catagories so this seemed like
# a good compromise
def create_maps():
    fc = "CHN_adm1.shp"
    # open a cursor on the name and ID to be used in saving the PDFs and the title of each map
    cursor = arcpy.da.SearchCursor(fc, ["ADMIN_NAME", "ADMIN_ID"])
    # open the map document
    mxd = china_folder + R"\ChinaProvinces.mxd"
    mapdoc = arcpy.mapping.MapDocument(mxd)
    # multiple layers in the map document but the layer that is being used to zoom to features is the 1st layer so you can
    # index it at the 0 position
    lyr = arcpy.mapping.ListLayers(mapdoc)[0]
    df = arcpy.mapping.ListDataFrames(mapdoc)[0]
    elemlist = arcpy.mapping.ListLayoutElements(mapdoc)
    title = elemlist[0]
    print("Creating maps")
    # this loops through each province in the shapefile
    for row in cursor:
        # the first value in the row is the name of the province, assign it to a variable 
        province = row[0]
        # update the title each iteration through the loop with the name of the province
        title.text = "Total Luminosity Amount in {0}, China (2013)".format(province)
        # select attributes based on their admin names
        clause = '"ADMIN_NAME" = \''+ province + '\''
        # function that creates a new selection each time through the loop on a new province
        arcpy.SelectLayerByAttribute_management(lyr, "NEW_SELECTION", clause)
        # zooms and centers on the selected province
        df.zoomToSelectedFeatures()
        # save and export the file as a pdf with the ID of the corresponding name
        outfile = outfolder + R"\province_" + str(row[1]) + "_lum2013.pdf"
        arcpy.mapping.ExportToPDF(mapdoc, outfile)
        print("map for {0} created".format(province))
    del mapdoc

#project_fc()
create_fields()
calculate_vals()
calc_lum_vals() 
update_lum_vals()     
write_csv()
create_maps()