
### ###
#This code will take VAAC HTML files as an input (These provide information to the aviation industry about areas to
#avoid due to volcanic ash) and will output a list of latitude-longitude vertices which form a polygon around which
#the ash is located. It will also output the names of himawari .DAT files you would need to download
### ###

import codecs

import distributed.dashboard.components
from bs4 import BeautifulSoup
import numpy as np
import glob
import os
import datetime as dt
from pathlib import Path as Filepath

### coords_file_pair ###

# Takes the location of your vaac html files as input
# Outputs the list of vertices for the vaac polygon along with the .DAT general filetype

htmlpath = "D:\HTML_analysis_folder"


def coords_file_pairs(filepath):

    # We get an OS standardised filepath in which to search for the .html files
    vaac_dir = str(Filepath(str(filepath)))

    # This next line might not work in linux, in which case replace the \\ with a /
    html_file_list = glob.glob(str(Filepath(vaac_dir + "\\" + "*.html")))

    himawari_fileformat_list = []  # will be list of fileformats

    # ultimately we will want to output something which will make it easy to pair the vaac html file with the himawari
    # .DAT files along with all of the vertices of the vaac polygon, so I initialise a list here to do that.
    # there's probably a more appropriate way to do it with dictionaries or tuples or something

    output_list = []
    j = 0  # this is an iteration variable. j will be the jth html file in the html file directory

    for file in html_file_list:
        with codecs.open(file, 'r') as f:  # codecs might not be required here, or rather io might be better?
            html = f.read() # This sets the variable html as the contents of fn_vacc (rather than the file itself)

        soup = BeautifulSoup(html, features="html.parser")
        div = soup.find('div')
        # This extracts the main bit of text from soup (ignoring the main title and lines and stuff)
        vaac = [str(s) for s in div.contents if str(s) != '<br/>' and str(s) != str('\n')]
        date_time_info_pub = vaac[3]
        # this is the line in the vaac that gives the time which the vaac was issued NOT the observation time
        # the polygon is issued for a ash cloud as it was 40 minutes before the publishing time of the vaac warning

        date_time_info_obs = vaac[13]  # this is the line in the vaac containing the observation time information
        polygon_info = vaac[14] + vaac[15] + vaac[16]  # these lines contain information about the polygon vertices
        # We import the obs time and the pub date and time
        # Import pub & obs time into two variables hr and min
        pub_date = date_time_info_pub[5:13]
        pub_time = date_time_info_pub[14:18]
        obs_time = date_time_info_obs[15:19]  # This is the time we need to use to match to the Himawari data

        # create datetime obj for pub_date
        pub_date = dt.datetime.strptime(pub_date + pub_time, '%Y%m%d%H%M')
        # now calculate the time delta between the two times
        FMT = '%H%M'
        # stands for hours and minutes and indicates how to read the string
        # e.g if format was 23:20 put %H:%M if 23-20 put %H-%M etc
        pub_time = dt.datetime.strptime(pub_time, FMT)
        if obs_time == "":
            output_list.append(["*19700101_0000*",[],file])
        else:
            obs_time = dt.datetime.strptime(obs_time, FMT)

            # have to do different methods if goes from 23 --> 0 to avoid negative vals
            if pub_time.hour > obs_time.hour:  # i.e 14 > 13
                tdelta = pub_time - obs_time
            else:
                tdelta = obs_time - pub_time - dt.timedelta(days=1)
                # add a day because it works for some reason thats kinda makes sense
            tdelta = abs(tdelta)

            # now subtracting the time difference from pub to obtain obs date
            obs_date = pub_date - tdelta

            # I now work on converting the polygon's coordinates into a useable format:
            # First of all I need to remove the information that is not coordinates.

            words = polygon_info.split(" ") # Splits the string into a list of all the 'words'
            # we must now check if the string is of the form Nxxxx or Exxxxx etcetera
            bad_words = []
            for word in words:
                if len(word) > 6 or len(word) < 5 or word[0] not in ["N","E","S","W"]:  # this is ridiculous
                    bad_words.append(word)
                if "MOV" in words:
                    if words.index(word) > words.index("MOV"):  # If MOV is in the vaac then the coordinates after it are forecasts
                        bad_words.append(word)

            coords = [x for x in words if x not in bad_words]   # these are the actual coordinates as a list
            # we can make these more useful by converting them to numbers and by separating to latitudes and longitudes

            latitudes = []
            longitudes = []

            for coord in coords:
                if coord[0] == "N":
                    latitudes.append(float(coord[1:3])+float(1/60)*float(coord[3:5]))
                if coord[0] == "S":
                    latitudes.append(-float(coord[1:3])-float(1/60)*float(coord[3:5]))
                if coord[0] == "E":
                    longitudes.append(float(coord[1:4])+float(1/60)*float(coord[4:6]))
                if coord[0] == "W":
                    longitudes.append(-float(coord[1:4])-float(1/60)*float(coord[4:6]))

            # we now have a list of latitudes and longitudes. the vertices have the same list index in each
            # i.e latitudes[x],longitudes[x] forms a vertex

            himawari_fileformat_list.append("*" + str(obs_date.strftime('%Y%m%d_%H%M')) + "*" )
            # The himawari data files will
            # contain this somewhere in the filename.
            # the ith item of the html list corresponds to the ith item of the fileformat list

            output_list.append([himawari_fileformat_list[j],list(zip(latitudes,longitudes)),file])  # this is a bit clunky

            j=j+1   # add one to the iteration variable which tells you which html file you're looking at this loop around
            # this isn't very pythonic though. I should probably use enumerate. this works though.

    return output_list

# element of output_list looks like ['*20210223_2150*',[(30,140),(32,142),...],'directory/my_file.html']



###download_command
###takes the filepath where you store your html folders as input
###tells you commands which you put in your console to download the right .DAT files


def download_command(filepath, dat_dir):
    # We get an OS standardised filepath in which to search for the .html files
    vaac_dir = str(Filepath(str(filepath)))

    # This next line might not work in linux, in which case replace the \\ with a /
    html_file_list = glob.glob(str(Filepath(vaac_dir + "\\" + "*.html")))

    himawari_download_list = []  # will be list of download commands
    # ultimately we will want to output something which will make it easy to pair the vaac html file with the himawari
    # .DAT files along with all of the vertices of the vaac polygon, so I initialise a list here to do that.
    # there's probably a more appropriate way to do it with dictionaries or tuples or something

    output_list = []
    j = 0  # this is an iteration variable. j will be the jth html file in the html file directory

    for file in html_file_list:
        with codecs.open(file, 'r') as f:  # codecs might not be required here, or rather io might be better?
            html = f.read()  # This sets the variable html as the contents of fn_vacc (rather than the file itself)

        soup = BeautifulSoup(html,
                             features="html.parser")  # This gives us the BeautifulSoup-ifyed version (Pythonic?), read by default parser (can't get lxml to work?)
        div = soup.find('div')  # This extracts the main bit of text from soup (ignoring the main title and lines and stuff)
        vaac = [str(s) for s in div.contents if str(s) != '<br/>' and str(s) != str('\n')]
        date_time_info_pub = vaac[3]  # this is the line in the vaac that gives the time which the vaac was issued NOT the observation time
        # the polygon is issued for a ash cloud as it was 40 minutes before the publishing time of the vaac warning

        date_time_info_obs = vaac[13]  # this is the line in the vaac containing the observation time information
        polygon_info = vaac[14] + vaac[15]  # these lines contain information about the polygon vertices

        # We import the obs time and the pub date and time
        # Import pub & obs time into two variables hr and min
        pub_date = date_time_info_pub[5:13]
        pub_time = date_time_info_pub[14:18]
        obs_time = date_time_info_obs[15:19]  # This is the time we need to use to match to the Himawari data
        # create datetime obj for pub_date

        pub_date = dt.datetime.strptime(pub_date + pub_time, '%Y%m%d%H%M')
        # now calculate the time delta between the two times
        FMT = '%H%M'
        # stands for hours and minutes and indicates how to read the string
        # e.g if format was 23:20 put %H:%M if 23-20 put %H-%M etc
        pub_time = dt.datetime.strptime(pub_time, FMT)
        obs_time = dt.datetime.strptime(obs_time, FMT)

        # have to do different methods if goes from 23 --> 0 to avoid negative vals
        if pub_time.hour > obs_time.hour:  # i.e 14 > 13
            tdelta = pub_time - obs_time
        else:
            tdelta = obs_time - pub_time - dt.timedelta(days=1)
            # add a day because it works for some reason thats kinda makes sense

        tdelta = abs(tdelta)

        # now subtracting the time difference from pub to obtain obs date
        obs_date = pub_date - tdelta

        ###I now work on converting the polygon's coordinates into a useable format:
        ###First of all I need to remove the information that is not coordinates.

        words = polygon_info.split(" ")  # Splits the string into a list of all the 'words'
        # we must now check if the string is of the form Nxxxx or Exxxxx etcetera
        bad_words = []
        for word in words:
            if len(word) > 6 or len(word) < 5 or word[0] not in ["N", "E", "S", "W"]:
                bad_words.append(word)

        coords = [x for x in words if x not in bad_words]  # these are the actual coordinates as a list
        # we can make these more useful by converting them to numbers and by separating to latitudes and longitudes

        latitudes = []
        longitudes = []

        for coord in coords:
            if coord[0] == "N":
                latitudes.append(float(coord[1:3]) + float(1 / 60) * float(coord[3:5]))
            if coord[0] == "S":
                latitudes.append(-float(coord[1:3]) - float(1 / 60) * float(coord[3:5]))
            if coord[0] == "E":
                longitudes.append(float(coord[1:4]) + float(1 / 60) * float(coord[4:6]))
            if coord[0] == "W":
                longitudes.append(-float(coord[1:4]) - float(1 / 60) * float(coord[4:6]))

        # we now have a list of latitudes and longitudes. the vertices have the same list index in each
        # i.e latitudes[x],longitudes[x] forms a vertex

        if coords != []:
            himawari_download_list.append("aws s3 sync --no-sign-request \"s3://noaa-himawari8/AHI-L1b-FLDK/" + str(
                obs_date.strftime('%Y/%m/%d/%H%M/')) + "\" \"" + dat_dir + "\"")

        j = j + 1  # add one to the iteration variable which tells you which html file you're looking at this loop around

    return himawari_download_list


# himawari_download_list is just a list of aws commands


def download_list_reduced(filepath):
    himawari_zone_lat_boundaries = [90, 54, 37, 24, 12, 0, -12, -24, -37, -54, -90]
    segment_names = ["*S0110*", "*S0210*", "*S0310*", "*S0410*", "*S0510*",
                     "*S0610*", "*S0710*", "*S0810*", "*S0910*", "*S1010"]
    tolerance = 0.5
    segment_lat_range = [((90+tolerance),(54-tolerance)),((54+tolerance),(37-tolerance)),
                         ((37+tolerance),(24-tolerance)),((24+tolerance),(12-tolerance)),
                         ((12+tolerance),(0-tolerance)),((0+tolerance),(-12-tolerance)),
                         ((-12+tolerance),(-24-tolerance)),((-24+tolerance),(-37-tolerance)),
                         ((-37+tolerance),(-54-tolerance)),((-54+tolerance),(-90-tolerance))]
    # if anyone else ever looks at this code please figure out how to do this as a list comprehension
    html_data = coords_file_pairs(filepath)
    for coords_file_pair in coords_file_pairs(filepath):
        print (coords_file_pair[0])
        print (coords_file_pair[1])
    filefmt_segments_list = []
    for pair in html_data:
        required_segments = set()
        coords = pair[1]
        filefmt = pair[0]
        if coords == []:
            filefmt_segments_list.append([filefmt,"no segments"])
        else:
            lats = (list(zip(*coords)))[0]
            maxlat = max(lats)
            minlat = min(lats)
            for lat_range in segment_lat_range:
                if float(lat_range[0]) > float(maxlat) > float(lat_range[1]):
                    required_segments.add(segment_names[segment_lat_range.index(lat_range)])
                if float(lat_range[0]) > float(minlat) > float(lat_range[1]):
                    required_segments.add(segment_names[segment_lat_range.index(lat_range)])
            for segment in required_segments:
                #segment_download_command = "--exclude \"*\" --include" + "\""  + str(segment) + "\""
                filefmt_segments_list.append([filefmt,segment])
    return filefmt_segments_list

# this isn't yet a fully fledged list of aws commands but rather an element looks like
# ['20210329_1230','S0310']
# the vast vast majority need only S0110,S0210,S0310 since these cover most of the tokyo vaac area
# this applies as long as the latitude is above about 24 degrees north
# this raises questions about how well this will generalise to eruptions near the equator
# where the properties of the atmosphere may be a little different


def get_ash_area_at_subsurface_point(vapath, index):  # note this is very approximate
    coords = (coords_file_pairs(vapath))[index][1]
    filefmt = (coords_file_pairs(vapath))[index][0]
    if coords == []:
        return 0,0,filefmt
    else:
        # print("Polygon coordinates found: " + str([str(np.round(x,2)) for x in coords]))
        lats = (list(zip(*coords)))[0]  # unzips list of coordinate tuples into lats and lons
        lons = (list(zip(*coords)))[1]
        minlat = min(lats)
        maxlat = max(lats)
        minlon = min(lons)
        maxlon = max(lons)
        if maxlon < 0:
            maxlon = 360.0 + maxlon
        if minlon < 0:
            minlon = 360.0 + minlon
        deltalonrad = 3.1416*(maxlon - minlon)/180
        deltalatrad = 3.1416*(maxlat - minlat)/180
        max_delta = max(deltalonrad,deltalatrad)
        cover_square_size_max = int((max_delta*3200))
        area = (6400**2)*np.sin((3.1416*(minlat+maxlat))/360)*deltalonrad*deltalatrad
        pixel_count = int(area/4)
        return pixel_count, cover_square_size_max, filefmt


def purge_list(vapath, minsize, maxsize, delete):
    del_list = []
    vadata = coords_file_pairs(vapath)
    for i in range(len(vadata)):
        square_size = get_ash_area_at_subsurface_point(vapath,i)[1]
        if square_size < minsize or square_size > maxsize:
            del_list.append(vadata[i][2])
    if delete:
        for file in del_list:
            os.remove(file)
    else:
        for file in del_list:
            print("remove " + str(file))


#purge_list("D:\HTML_analysis_folder",32,600,True)  # maximum size currently at 512
# but maximum size may be increased a bit higher since the actual pixel size is always
# less than the program says by a little bit. More so near the poles.
# The True/False part of the input to the function tells you if you want the html files
# To be automatically deleted. set it to False if you want to check which files are going
# to get deleted before actually deleting them.

#for i in range(len(coords_file_pairs(htmlpath))):
    #print(get_ash_area_at_subsurface_point(htmlpath,i))

#print(download_list_reduced(htmlpath))
