
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

###coords_file_pair###

#Takes the location of your vaac html files as input
#Outputs the list of vertices for the vaac polygon along with the .DAT general filetype

def coords_file_pairs(filepath):

    #We get an OS standardised filepath in which to search for the .html files
    vaac_dir = str(Filepath(str(filepath)))

    #This next line might not work in linux, in which case replace the \\ with a /
    html_file_list = glob.glob(str(Filepath(vaac_dir + "\\" + "*.html")))
    #print(str(html_file_list))

    himawari_fileformat_list = []#will be list of fileformats

    #ultimately we will want to output something which will make it easy to pair the vaac html file with the himawari
    #.DAT files along with all of the vertices of the vaac polygon, so I initialise a list here to do that.
    #there's probably a more appropriate way to do it with dictionaries or tuples or something

    output_list = []
    j = 0 #this is an iteration variable. j will be the jth html file in the html file directory

    for file in html_file_list:
        with codecs.open(file, 'r') as f: # codecs might not be required here, or rather io might be better?
            html = f.read() # This sets the variable html as the contents of fn_vacc (rather than the file itself)

        soup = BeautifulSoup(html, features="html.parser") # This gives us the BeautifulSoup-ifyed version (Pythonic?), read by default parser (can't get lxml to work?)
        div = soup.find('div') # This extracts the main bit of text from soup (ignoring the main title and lines and stuff)
        vaac = [str(s) for s in div.contents if str(s) != '<br/>' and str(s) != str('\n')]
        date_time_info_pub = vaac[3] #this is the line in the vaac that gives the time which the vaac was issued NOT the observation time
        #the polygon is issued for a ash cloud as it was 40 minutes before the publishing time of the vaac warning

        date_time_info_obs = vaac[13] #this is the line in the vaac containing the observation time information
        polygon_info = vaac[14] + vaac[15] + vaac[16] #these lines contain information about the polygon vertices
        print ("polygon info source from html: " + str(polygon_info))

        # We import the obs time and the pub date and time
        # Import pub & obs time into two variables hr and min
        pub_date = date_time_info_pub[5:13]
        pub_time = date_time_info_pub[14:18]
        obs_time = date_time_info_obs[15:19] #This is the time we need to use to match to the Himawari data

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

        words = polygon_info.split(" ") #Splits the string into a list of all the 'words'
        #we must now check if the string is of the form Nxxxx or Exxxxx etcetera
        bad_words = []
        for word in words:
            if len(word) > 6 or len(word) < 5 or word[0] not in ["N","E","S","W"]: #this is ridiculous
                bad_words.append(word)
            if "MOV" in words:
                if words.index(word) > words.index("MOV"): #If MOV is in the vaac then the coordinates after it are forecasts
                    bad_words.append(word)







        coords = [x for x in words if x not in bad_words] #these are the actual coordinates as a list
        #we can make these more useful by converting them to numbers and by separating to latitudes and longitudes

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

        #we now have a list of latitudes and longitudes. the vertices have the same list index in each
        #i.e latitudes[x],longitudes[x] forms a vertex

        himawari_fileformat_list.append("*" + str(obs_date.strftime('%Y%m%d_%H%M')) + "*" ) #The himawari data files will
        #contain this somewhere in the filename. the ith item of the html list corresponds to the ith item of the fileformat list

        output_list.append([himawari_fileformat_list[j],list(zip(latitudes,longitudes))]) #this is a bit clunky

        j=j+1 #add one to the iteration variable which tells you which html file you're looking at this loop around

    return output_list



###download_command
###takes the filepath where you store your html folders as input
###tells you commands which you put in your console to download the right .DAT files

def download_command(filepath):
    # We get an OS standardised filepath in which to search for the .html files
    vaac_dir = str(Filepath(str(filepath)))

    # This next line might not work in linux, in which case replace the \\ with a /
    html_file_list = glob.glob(str(Filepath(vaac_dir + "\\" + "*.html")))

    himawari_download_list = []  # will be list of download commands

    dat_dir = str(Filepath(str(input("Enter the filepath in which you want to store your .DAT files: "))))

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
        div = soup.find(
            'div')  # This extracts the main bit of text from soup (ignoring the main title and lines and stuff)
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
