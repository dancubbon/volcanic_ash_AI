###This program will loop through your vaa html folder
#For each, it will identify the set of .DAT files to read, and then read them
#It will then, for each set of .DAT files, create an array of numbers for each pixel in the image
#These numbers will be 0 for not ash, 1 for ash, and 2 for outside the disk of the earth
#It will do this by first calculating a brightness temperature difference for each pixel
#This overestimates the amount of ash in the image, so we use the vaac polygons to mask out
#Areas which we know do not contain ash
#The program should output pairs of image data, along with the array value associated with each pixel
#Note!!!!! Running this program dumps a lot of data into your hidden /temp folder like a lot of data

# Note!!! This program doesn't do the stuff i just mentioned but it does have useful functions

from VAA_HTML import download_command
from VAA_HTML import coords_file_pairs
from pathlib import Path as Filepath
from satpy import Scene
from pyresample import create_area_def
import geopandas as gp
import numpy as np
import glob
from matplotlib import pyplot as plt
import matplotlib.path
from pyproj import Proj
from MASK_MAKER import makemask
from MASK_MAKER import makemask2

datapath = "D:\Test_download_folder"
htmlpath = "D:\HTML_analysis_folder"


def make_scene(fileformat,datfilepath): #fileformat is "*YYYYMMDD_HHMM*"
    filelist = glob.glob(str(Filepath(datfilepath + "\\" + fileformat)))
    scn = Scene(filelist, reader='ahi_hsd')
    return scn

def generate_ash_map(vapath, datpath, index, region, type):
    # vapath: type str. filepath of vaac html files
    # datpath: type str. filepath of himawari8 .dat/bz2 files
    # index: type int. which html file to load in
    # region: type str. "full" or "partial"
    # type type str. "no_wv_correction" or "static_wv_correction" or "dynamic_wv_correction"
    coords = (coords_file_pairs(vapath))[index][1]
    filefmt = (coords_file_pairs(vapath))[index][0]
    print("Loading himawari8 data from: " + str((coords_file_pairs(vapath))[index][0]))
    print("Polygon coordinates found: " + str(coords))
    xcoords = (list(zip(*coords)))[0]
    ycoords = (list(zip(*coords)))[1]
    print("Creating scene...")
    scene = make_scene(filefmt, datpath)
    scene.load(['B14', 'B15'])
    print("Scene successfully loaded: ")
    t11 = scene['B14'].values[:, :]
    t12 = scene['B15'].values[:, :]
    if type == "no_wv_correction":
        btd = t11-t12
        print("Uncorrected btd generated.")
    elif type == "static_wv_correction":
        btd = t11 - t12 - np.exp(6. * (t11 / 320.) - 4.5)
        print("Corrected btd generated.")
    elif type == "dynamic_wv_correction":
        btd = t11 - t12 - np.exp(6. * (t11 / 320.) - (4.0 + np.cos(xcoords[1])))
        print("Dynamic corrected btd generated.")
    else:
        btd = t11-t12
        print("Invalid entry. Uncorrected btd generated.")
    msq = makemask(coords, scene)[1] #this is a plot region if you only want to look at the region of the polygon
    std_msq = makemask(coords, scene)[2]
    if region == "full":
        btd_masked = np.ma.array(btd, mask=makemask(coords, scene)[0] == False)
        ash_map = np.ma.masked_greater_equal(btd_masked, 0)
        ash_map_export = -np.sign(ash_map)
    elif region == "partial":
        print("Partial region selected. r1r2c1c2 coordinates are: ")
        print(str(msq))
        btd_masked = np.ma.array(btd, mask=makemask(coords, scene)[0] == False)
        ash_map = np.ma.masked_greater_equal(btd_masked, 0)
        ash_map = -np.sign(ash_map)
        ash_map_export = ash_map[msq[0]:msq[1],msq[2]:msq[3]]
    elif region == "standard":
        print("Partial region selected. r1r2c1c2 coordinates are: ")
        print(str(std_msq))
        btd_masked = np.ma.array(btd, mask=makemask(coords, scene)[0] == False)
        ash_map = np.ma.masked_greater_equal(btd_masked, 0)
        ash_map = -np.sign(ash_map)
        ash_map_export = ash_map[std_msq[0]:std_msq[1], std_msq[2]:std_msq[3]]
    else:
        btd_masked = np.ma.array(btd, mask=makemask(coords, scene)[0] == False)
        ash_map = np.ma.masked_greater_equal(btd_masked, 0)
        ash_map_export = -np.sign(ash_map)
    return ash_map_export,filefmt


def generate_btd_map(vapath,datpath,index,region,type):
    coords = (coords_file_pairs(vapath))[index][1]
    filefmt = (coords_file_pairs(vapath))[index][0]
    print("Loading himawari8 data from: " + str((coords_file_pairs(vapath))[index][0]))
    print("Polygon coordinates found: " + str(coords))
    xcoords = (list(zip(*coords)))[0]
    ycoords = (list(zip(*coords)))[1]
    print("Creating scene...")
    scene = make_scene(filefmt, datpath)
    scene.load(['B14', 'B15'])
    print("Scene successfully loaded: ")
    t11 = scene['B14'].values[:, :]
    t12 = scene['B15'].values[:, :]
    if type == "no_wv_correction":
        btd = t11 - t12
        print("Uncorrected btd generated.")
    elif type == "static_wv_correction":
        btd = t11 - t12 - np.exp(6. * (t11 / 320.) - 4.5)
        print("Corrected btd generated.")
    elif type == "dynamic_wv_correction":
        btd = t11 - t12 - np.exp(6. * (t11 / 320.) - (4.25 + 0.5*np.cos(xcoords[1])))
        print("Dynamic corrected btd generated.")
    else:
        btd = t11 - t12
        print("Invalid entry. Uncorrected btd generated.")
    msq = makemask(coords, scene)[1]
    std_msq = makemask(coords, scene)[2]
    if region == "full":
        btd_map = btd
    elif region == "partial":
        print("Partial region selected. r1r2c1c2 coordinates are: ")
        print(str(msq))
        btd_map = btd[msq[0]:msq[1], msq[2]:msq[3]]
    elif region == "standard":
        btd_map = btd[std_msq[0]:std_msq[1], std_msq[2]:std_msq[3]]
    else:
        btd_map = btd
    return btd_map ,filefmt


def generate_btd_and_ash_map(vapath,datpath,index,region,type):
    coords = (coords_file_pairs(vapath))[index][1]
    filefmt = (coords_file_pairs(vapath))[index][0]
    print("Loading himawari8 data from: " + str((coords_file_pairs(vapath))[index][0]))
    print("Polygon coordinates found: " + str(coords))
    xcoords = (list(zip(*coords)))[0]
    ycoords = (list(zip(*coords)))[1]
    print("Creating scene...")
    scene = make_scene(filefmt, datpath)
    scene.load(['B14', 'B15'])
    print("Scene successfully loaded: ")
    t11 = scene['B14'].values[:, :]
    t12 = scene['B15'].values[:, :]
    if type == "no_wv_correction":
        btd = t11 - t12
        print("Uncorrected btd generated.")
    elif type == "static_wv_correction":
        btd = t11 - t12 - np.exp(6. * (t11 / 320.) - 4.5)  # 4.5 = b. increasing b decreases the water vapour correction
        print("Corrected btd generated.")
    elif type == "dynamic_wv_correction":
        btd = t11 - t12 - np.exp(6. * (t11 / 320.) - (4.25 + 0.5*np.cos(xcoords[1])))
        print("Dynamic corrected btd generated.")
    else:
        btd = t11 - t12
        print("Invalid entry. Uncorrected btd generated.")
    msq = makemask(coords, scene)[1]
    std_msq = makemask(coords, scene)[2]
    if region == "full":
        btd_map = btd
    elif region == "partial":
        print("Partial region selected. r1r2c1c2 coordinates are: ")
        print(str(msq))
        btd_map = btd[msq[0]:msq[1], msq[2]:msq[3]]
    elif region == "standard":
        btd_map = btd[std_msq[0]:std_msq[1], std_msq[2]:std_msq[3]]
    else:
        btd_map = btd
    if region == "full":
        btd_masked = np.ma.array(btd, mask=makemask(coords, scene)[0] == False)
        ash_map = np.ma.masked_greater_equal(btd_masked, 0)
        ash_map_export = -np.sign(ash_map)
    elif region == "partial":
        print("Partial region selected. r1r2c1c2 coordinates are: ")
        print(str(msq))
        btd_masked = np.ma.array(btd, mask=makemask(coords, scene)[0] == False)
        ash_map = np.ma.masked_greater_equal(btd_masked, 0)
        ash_map = -np.sign(ash_map)
        ash_map_export = ash_map[msq[0]:msq[1],msq[2]:msq[3]]
    elif region == "standard":
        print("Partial region selected. r1r2c1c2 coordinates are: ")
        print(str(std_msq))
        btd_masked = np.ma.array(btd, mask=makemask(coords, scene)[0] == False)
        ash_map = np.ma.masked_greater_equal(btd_masked, 0)
        ash_map = -np.sign(ash_map)
        ash_map_export = ash_map[std_msq[0]:std_msq[1], std_msq[2]:std_msq[3]]
    else:
        btd_masked = np.ma.array(btd, mask=makemask(coords, scene)[0] == False)
        ash_map = np.ma.masked_greater_equal(btd_masked, 0)
        ash_map_export = -np.sign(ash_map)
    return btd_map,ash_map_export,filefmt



my_btd_and_ash_map = generate_btd_and_ash_map(htmlpath,datapath,0,"standard","static_wv_correction")
plt.imsave("btd_map.png", my_btd_and_ash_map[0],vmin=-5, vmax=5, cmap='RdBu')
plt.imsave("ash_map.png", my_btd_and_ash_map[1],vmin=-5, vmax=5, cmap='RdBu')













