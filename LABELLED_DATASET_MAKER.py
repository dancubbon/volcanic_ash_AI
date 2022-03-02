# This program will loop through your vaa html folder
# For each, it will identify the set of .DAT files to read, and then read them
# It will then, for each set of .DAT files, create an array of numbers for each pixel in the image
# These numbers will be 0 for not ash, 1 for ash, and 2 for outside the disk of the earth
# It will do this by first calculating a brightness temperature difference for each pixel
# This overestimates the amount of ash in the image, so we use the vaac polygons to mask out
# Areas which we know do not contain ash
# The program should output pairs of image data, along with the array value associated with each pixel
# Note!!!!! Running this program dumps a lot of data into your hidden /temp folder like a lot of data
# Do %appdata% to get to this folder on windows

# Note!!! This program doesn't quite do the stuff i just mentioned but it does have useful functions

from VAA_HTML import download_command
from VAA_HTML import get_vaac_data
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
from PIL import Image


datapath = "E:\\RAIKOKE\\PAPER_DATA\\"
htmlpath = "E:\\RAIKOKE\\HTML"
all_channels = ['B01','B02','B03','B04','B05','B06','B07','B08','B09','B10','B11','B12','B13','B14','B15','B16']

v_dict = {'NISHINOSHIMA': '28409600', 'SAKURAJIMA (AIRA CALDERA)': '28208001', 'KARYMSKY': '30013000', 'EBEKO': '29038000',
          'KLYUCHEVSKOY': '30026000', 'SHEVELUCH': '30027000', 'SUWANOSEJIMA': '28203000', 'BEZYMIANNY': '30025000',
          'SATSUMA-IOJIMA (KIKAI CALDERA)': '28206000', 'ASOSAN': '28211000', 'KUCHINOERABUJIMA': '28205000',
          'TAAL': '27307000', 'SEMISOPOCHNOI': '31106000', 'PAGAN': '28417000', 'CHIRINKOTAN' : '29026000',
          'FUKUTOKU-OKA-NO-BA': '28413000', 'SARYCHEV PEAK': '29024000', 'SINABUNG': '26108000', 'RAIKOKE': '29025000',
          'NOTICE': '00000000',
          'TEST': '10000001'}

n_dict = {value:key for key,value in v_dict.items()}


# lots of functions here take 'region' and 'type' as inputs
# region can be 'full' for the whole disk , 'partial' for the rectangle which just encloses the ash
# or 'standard' for a square centred on the middle of the vaac polygon
# type is the type of water vapour correction which can be 'no_wv_correction'
# or 'static_wv_correction' or 'contextual_wv_correction' or 'iterative_wv_correction'
# b = 4.5 works well near the tropics and indeed pretty well for all the volcanoes in the tokyo vaac area
# b = 4.7-4.8 might work better near the poles but this remains to be seen
# either way, keep b between around 4.4 and 4.9. the ash detection is VERY sensitive to this.



def make_scene(fileformat,datfilepath): #fileformat is "*YYYYMMDD_HHMM*"
    filelist = glob.glob(str(Filepath(datfilepath + "\\" + fileformat)))
    if filelist == []:
        print("No Himawari8 data found.")
        return "empty"
    else:
        scn = Scene(filelist, reader='ahi_hsd')
        return scn


def generate_ash_map(vapath, datpath, index, region, type):
    # vapath: type str. filepath of vaac html files
    # datpath: type str. filepath of himawari8 .dat/bz2 files
    # index: type int. which html file to load in
    # region: type str. "full" or "partial"
    # type type str. "no_wv_correction" or "static_wv_correction" or "dynamic_wv_correction"
    coords = (get_vaac_data(vapath))[index][1]
    filefmt = (get_vaac_data(vapath))[index][0]
    print("Loading himawari8 data from: " + str((get_vaac_data(vapath))[index][0]))
    print("Polygon coordinates found: " + str(np.round(coords,2)))
    xcoords = (list(zip(*coords)))[0]
    ycoords = (list(zip(*coords)))[1]
    print("Creating scene...")
    scene = make_scene(filefmt, datpath)
    scene.load(['B14', 'B15'])
    print("Scene successfully loaded: ")
    b14 = scene['B14'].values[:, :]
    b15 = scene['B15'].values[:, :]
    msq = makemask(coords, scene)[1] #this is a plot region if you only want to look at the region of the polygon
    std_msq = makemask(coords, scene)[2]
    if type == "no_wv_correction":
        btd = b14-b15
        print("Uncorrected btd generated.")
    elif type == "static_wv_correction":
        btd_uncorrected = b14 - b15
        btd_uncorrected = btd_uncorrected[std_msq[0]:std_msq[1], std_msq[2]:std_msq[3]]
        b14_square = scene['B14'].values[std_msq[0]:std_msq[1], std_msq[2]:std_msq[3]]
        idx, idy = np.where(b14_square == np.nanmax(b14_square))
        i, j = idx[0], idy[0]  # only take first solution
        btd_Tmax = btd_uncorrected[i, j]
        b14_max = b14_square[i, j]
        b = 6. - np.log(btd_Tmax)
        btd = b14 - b15 - np.exp(6. * (b14 / b14_max) - b)
    elif type == "dynamic_wv_correction":
        btd = b14 - b15 - np.exp(6. * (b14 / 320.) - (4.0 + np.cos(xcoords[1])))
        print("Dynamic corrected btd generated.")
    else:
        btd = b14-b15
        print("Invalid entry. Uncorrected btd generated.")
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
    coords = (get_vaac_data(vapath))[index][1]
    filefmt = (get_vaac_data(vapath))[index][0]
    print("Loading himawari8 data from: " + str((get_vaac_data(vapath))[index][0]))
    print("Polygon coordinates found: " + str(coords))
    xcoords = (list(zip(*coords)))[0]
    ycoords = (list(zip(*coords)))[1]
    print("Creating scene...")
    scene = make_scene(filefmt, datpath)
    scene.load(['B14', 'B15'])
    print("Scene successfully loaded: ")
    b14 = scene['B14'].values[:, :]
    b15 = scene['B15'].values[:, :]
    msq = makemask(coords, scene)[1]
    std_msq = makemask(coords, scene)[2]
    if type == "no_wv_correction":
        btd = b14 - b15
        print("Uncorrected btd generated.")
    elif type == "static_wv_correction":
        btd_uncorrected = b14 - b15
        btd_uncorrected = btd_uncorrected[std_msq[0]:std_msq[1], std_msq[2]:std_msq[3]]
        b14_square = scene['B14'].values[std_msq[0]:std_msq[1], std_msq[2]:std_msq[3]]
        idx, idy = np.where(b14_square == np.nanmax(b14_square))
        i, j = idx[0], idy[0]  # only take first solution
        btd_Tmax = btd_uncorrected[i, j]
        b14_max = b14_square[i, j]
        b = 6. - np.log(btd_Tmax)
        btd = b14 - b15 - np.exp(6. * (b14 / b14_max) - b)
    elif type == "dynamic_wv_correction":
        btd = b14 - b15 - np.exp(6. * (b14 / 320.) - (4.25 + 0.5*np.cos(xcoords[1])))
        print("Dynamic corrected btd generated.")
    else:
        btd = b14 - b15
        print("Invalid entry. Uncorrected btd generated.")

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


def generate_btd_and_ash_map(vapath, datpath, index, region, type):
    # Retrieve coordinates and fileformat
    data = get_vaac_data(vapath)
    coords = data[index][1]
    filefmt = data[index][0]
    volc_code = data[index][2][10 + len(vapath):18 + len(vapath)]
    volc_name = n_dict[volc_code]
    print("Loading himawari8 data from: " + volc_name + " on " + str(data[index][0][1:14]))
    # print("Polygon coordinates found: " + str(np.round(coords,2)))

    # Load in scene
    print("Creating scene...")
    scene = make_scene(filefmt, datpath)

    # Check if there is available data
    if coords == [] or scene == "empty":
        print("No coordinates found: returning empty map.")
        empty = np.zeros((512,512))
        return empty, empty, filefmt

    print("Loading data from scene...")
    # Load in scene
    scene.load(['B14', 'B15'])
    print("Scene successfully loaded: ")

    # Load in the 11 micrometer and 12 micrometer brightness temperatures
    b14 = scene['B14'].values[:, :]
    b15 = scene['B15'].values[:, :]

    # Load in the relevant areas
    std_msq = makemask(coords, scene)[2]
    msq = makemask(coords, scene)[1]

    # Check what type of water vapour correction the user wishes to use
    if type == "no_wv_correction":
        btd = b14 - b15
        b14_square = scene['B14'].values[std_msq[0]:std_msq[1], std_msq[2]:std_msq[3]]
        b15_square = scene['B15'].values[std_msq[0]:std_msq[1], std_msq[2]:std_msq[3]]
        b14_notnan = b14_square[~np.isnan(b14_square)]
        b15_notnan = b15_square[~np.isnan(b15_square)]
        plt.hist(b14_notnan, bins=100, alpha=0.5, label="T11")
        plt.hist(b15_notnan, bins=100, alpha=0.5, label="T12")
        plt.title("11, 12 micron brightness temperatures \n" + str(volc_name) + " " + str(filefmt[1:14]))
        plt.legend()
        plt.savefig("Histogram_" + str(volc_name) + " " + str(filefmt[1:14]) + "_11_12_micron.png")
        plt.show()

        btd_square = btd[std_msq[0]:std_msq[1], std_msq[2]:std_msq[3]]
        btd_uncorrected_notnan = btd_square[~np.isnan(btd_square)]
        plt.hist(btd_uncorrected_notnan, bins=100, alpha=0.5, label="btd_raw")
        plt.title("raw btd \n" + str(volc_name) + " " + str(filefmt[1:14]))
        plt.legend()
        plt.savefig("Histogram_" + str(volc_name) + " " + str(filefmt[1:14]) + "_btds.png")
        plt.show()

        print("Uncorrected btd generated.")
    elif type == "static_wv_correction":
        btd = b14 - b15 - np.exp(6. * (b14 / 320.0) - 4.5)
    elif type == "contextual_wv_correction":
        btd_uncorrected = b14 - b15
        btd_uncorrected = btd_uncorrected[std_msq[0]:std_msq[1], std_msq[2]:std_msq[3]]
        b14_square = scene['B14'].values[std_msq[0]:std_msq[1], std_msq[2]:std_msq[3]]
        b15_square = scene['B15'].values[std_msq[0]:std_msq[1], std_msq[2]:std_msq[3]]
        idx, idy = np.where(b14_square == np.nanpercentile(b14_square,98))
        i, j = idx[0], idy[0]  # only take first solution
        btd_Tmax = btd_uncorrected[i, j]
        print("btd_Tmax = " + str(btd_Tmax) + " K")
        b14_max = b14_square[i, j]
        print("B14 max: " + str(b14_max) + "K")
        b = 6. - np.log(np.abs(btd_Tmax))
        print("b parameter: " + str(b))
        btd = b14 - b15 - np.exp(6. * (b14 / b14_max) - b)

        b14_notnan = b14_square[~np.isnan(b14_square)]
        b15_notnan = b15_square[~np.isnan(b15_square)]
        plt.hist(b14_notnan, bins=100, alpha=0.5, label="T11")
        plt.hist(b15_notnan, bins=100, alpha=0.5, label="T12")
        plt.title("11, 12 micron brightness temperatures \n" + str(volc_name) + " " + str(filefmt[1:14]))
        plt.legend()
        plt.savefig("Histogram_" + str(volc_name) + " " + str(filefmt[1:14]) + "_11_12_micron.png")
        plt.show()

        btd_square = btd[std_msq[0]:std_msq[1], std_msq[2]:std_msq[3]]
        btd_uncorrected_notnan = btd_uncorrected[~np.isnan(btd_uncorrected)]
        btd_corrected_notnan = btd_square[~np.isnan(btd_square)]
        plt.hist(btd_corrected_notnan, bins=100, alpha=0.5, label="btd_corrected")
        plt.hist(btd_uncorrected_notnan, bins=100, alpha=0.5, label="btd_raw")
        plt.title("raw and corrected btd \n" + str(volc_name) + " " + str(filefmt[1:14]))
        plt.legend()
        plt.savefig("Histogram_" + str(volc_name) + " " + str(filefmt[1:14]) + "_btds.png")
        plt.show()

    elif type == "iterative_wv_correction":
        b_step = 0.02
        btd_uncorrected = b14 - b15
        btd_uncorrected = btd_uncorrected[std_msq[0]:std_msq[1], std_msq[2]:std_msq[3]]
        btd_uncorrected_notnan = btd_uncorrected[~np.isnan(btd_uncorrected)]
        plt.hist(btd_uncorrected_notnan, bins=100, alpha=0.5, label="btd_raw")

        b14_square = scene['B14'].values[std_msq[0]:std_msq[1], std_msq[2]:std_msq[3]]
        b15_square = scene['B15'].values[std_msq[0]:std_msq[1], std_msq[2]:std_msq[3]]
        idx, idy = np.where(b14_square == np.nanpercentile(b14_square, 98))
        i, j = idx[0], idy[0]  # only take first solution
        btd_Tmax = btd_uncorrected[i, j]
        print("btd_Tmax = " + str(btd_Tmax) + " K")
        b14_max = b14_square[i, j]
        print("B14 max: " + str(b14_max) + "K")
        b0 = 6. - np.log(np.abs(btd_Tmax))
        print("b parameter: " + str(b0))
        btd = b14 - b15 - np.exp(6. * (b14 / b14_max) - b0)
        print("Dynamic corrected btd generated.")
        area = makemask(coords, scene)[3]
        btd_masked = np.ma.array(btd, mask=makemask(coords, scene)[0] == False)
        ash_map = np.ma.masked_greater_equal(btd_masked, 0.0)
        ash_map_boolean = -np.sign(ash_map)
        ash_pixel_count = np.count_nonzero(ash_map_boolean == 1.0)
        print("Ash pixels detected on first iteration: " + str(ash_pixel_count))
        ash_fraction = ash_pixel_count / area
        ash_map_new_boolean = ash_map_boolean
        ash_pixel_count_new = ash_pixel_count
        k = 0

        btd_square = btd[std_msq[0]:std_msq[1], std_msq[2]:std_msq[3]]
        btd_corrected_notnan = btd_square[~np.isnan(btd_square)]
        plt.hist(btd_corrected_notnan, bins=100, alpha=0.5, label="btd_corrected_first_try")

        if ash_fraction > 0.3 and ash_fraction < 0.85:
            print("Ash fraction good. Outputting ash map...")
        while ash_fraction < 0.3 or ash_fraction > 0.85:  # note this could end up in an infinite loop
            k += 1
            if ash_fraction < 0.3:
                print("Too little ash. Decreasing b (increasing wv correction).")
                b0 -= b_step
                btd = b14 - b15 - np.exp(6. * (b14 / b14_max) - b0)
                btd_masked = np.ma.array(btd, mask=makemask(coords, scene)[0] == False)
                ash_map_new = np.ma.masked_greater_equal(btd_masked, 0)
                ash_map_new_boolean = -np.sign(ash_map_new)
                ash_pixel_count_new = np.count_nonzero(ash_map_new_boolean == 1.0)
                print("Ash pixel count: " + str(ash_pixel_count_new))
                ash_fraction = ash_pixel_count_new / area
            if ash_fraction > 0.85:
                print("Too much ash. Increasing b (decreasing wv correction).")
                b0 += b_step
                btd = b14 - b15 - np.exp(6. * (b14 / b14_max) - b0)
                btd_masked = np.ma.array(btd, mask=makemask(coords, scene)[0] == False)
                ash_map_new = np.ma.masked_greater_equal(btd_masked, 0)
                ash_map_new_boolean = -np.sign(ash_map_new)
                ash_pixel_count_new = np.count_nonzero(ash_map_new_boolean == 1.0)
                print("Ash pixel count: " + str(ash_pixel_count_new))
                ash_fraction = ash_pixel_count_new / area
            if k > 50:
                print("Ash percentage too sensitive. (Loop taking too long) ")
                btd_masked = np.ma.array(btd, mask=makemask(coords, scene)[0] == False)
                ash_map_new = np.ma.masked_greater_equal(btd_masked, 0)
                ash_map_new_boolean = -np.sign(ash_map_new)
                ash_pixel_count_new = np.count_nonzero(ash_map_new_boolean == 1.0)
                ash_fraction = ash_pixel_count_new / area
                break
        ash_map_export = ash_map_new_boolean[std_msq[0]:std_msq[1], std_msq[2]:std_msq[3]]
        btd_map = btd[std_msq[0]:std_msq[1], std_msq[2]:std_msq[3]]


        btd_shifted_notnan = btd_map[~np.isnan(btd_map)]
        plt.hist(btd_shifted_notnan, bins=100, alpha=0.5, label="btd_corrected_second_try")
        plt.title("raw, corrected and recorrected btd \n" + str(volc_name) + " " + str(filefmt[1:14]))
        plt.legend()
        # plt.savefig("Histogram_" + str(volc_name) + " " + str(filefmt[1:14]) + "_btds.png")
        # plt.show()


        print("Ash pixels detected after any corrections: " + str(ash_pixel_count_new))
        print("Ash percentage within polygon: " + str(100 * ash_fraction))
        print("Ash percentage within image: " + str(100 * ash_pixel_count_new / (512 * 512)))

    else:
        btd = b14 - b15
        print("Invalid entry. Uncorrected btd generated.")

    # Crop btd regions
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

    # Create exports based on region
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

        # btd_map = btd[msq[0]:msq[1], msq[2]:msq[3]]
        # btd_shifted_notnan = btd_map[~np.isnan(btd_map)]
        # plt.hist(btd_shifted_notnan, bins=100, alpha=0.5, label="btd_shifted")
        # plt.title("raw, corrected btd \n" + str(volc_name) + " " + str(filefmt[1:14]))
        # plt.legend()
        # plt.savefig("Histogram_" + str(volc_name) + " " + str(filefmt[1:14]) + "_btds.png")
        # plt.show()

    elif region == "standard":
        print("Partial region selected. r1r2c1c2 coordinates are: ")
        print(str(std_msq))
        btd_masked = np.ma.array(btd, mask=makemask(coords, scene)[0] == False)
        ash_map = np.ma.masked_greater_equal(btd_masked, 0)
        ash_map = -np.sign(ash_map)
        ash_map_export = ash_map[std_msq[0]:std_msq[1], std_msq[2]:std_msq[3]]

        plt.savefig("Histogram_" + str(volc_name) + " " + str(filefmt[1:14]) + "_btds.png")
        plt.show()

    elif region == "standard_modified_threshold":
        threshold = 0.0
        threshold_step = 0.2
        area = makemask(coords, scene)[3]
        print("Partial region selected. r1r2c1c2 coordinates are: ")
        print(str(std_msq))
        btd_masked = np.ma.array(btd, mask=makemask(coords, scene)[0] == False)
        ash_map = np.ma.masked_greater_equal(btd_masked, 0.0)
        ash_map_boolean = -np.sign(ash_map)
        ash_pixel_count = np.count_nonzero(ash_map_boolean == 1.0)
        print("Ash pixels detected on first iteration: " + str(ash_pixel_count))
        ash_fraction = ash_pixel_count/area
        ash_map_new_boolean = ash_map_boolean
        ash_pixel_count_new = ash_pixel_count
        k = 0
        if ash_fraction < 0.3:
            print("Ash fraction less than expected: Altering BTD threshold until ash fraction is enough.")
        if ash_fraction > 0.85:
            print("Ash fraction more than expected: Altering BTD threshold until ash fraction is enough.")
        if ash_fraction > 0.3 and ash_fraction < 0.85:
            print("Ash fraction good. Outputting ash map...")
        while ash_fraction < 0.3 or ash_fraction > 0.85:  # note this could end up in an infinite loop
            k += 1
            if ash_fraction < 0.3:
                # print("Too little ash. Increasing BTD Threshold.")
                btd -= threshold_step
                btd_masked = np.ma.array(btd, mask=makemask(coords, scene)[0] == False)
                ash_map_new = np.ma.masked_greater_equal(btd_masked, 0)
                ash_map_new_boolean = -np.sign(ash_map_new)
                ash_pixel_count_new = np.count_nonzero(ash_map_new_boolean == 1.0)
                ash_fraction = ash_pixel_count_new/area
            if ash_fraction > 0.85:
                # print("Too much ash. Decreasing BTD Threshold.")
                btd += threshold_step
                btd_masked = np.ma.array(btd, mask=makemask(coords, scene)[0] == False)
                ash_map_new = np.ma.masked_greater_equal(btd_masked, 0)
                ash_map_new_boolean = -np.sign(ash_map_new)
                ash_pixel_count_new = np.count_nonzero(ash_map_new_boolean == 1.0)
                ash_fraction = ash_pixel_count_new / area
            if k > 50:
                print("Ash percentage too sensitive. (Loop taking too long) ")
                btd_masked = np.ma.array(btd, mask=makemask(coords, scene)[0] == False)
                ash_map_new = np.ma.masked_greater_equal(btd_masked, 0)
                ash_map_new_boolean = -np.sign(ash_map_new)
                ash_pixel_count_new = np.count_nonzero(ash_map_new_boolean == 1.0)
                ash_fraction = ash_pixel_count_new / area
                break
        ash_map_export = ash_map_new_boolean[std_msq[0]:std_msq[1], std_msq[2]:std_msq[3]]
        btd_map = btd[std_msq[0]:std_msq[1], std_msq[2]:std_msq[3]]

        btd_shifted_notnan = btd_map[~np.isnan(btd_map)]
        plt.hist(btd_shifted_notnan, bins=100, alpha=0.5, label="btd_shifted")
        plt.title("raw, corrected and shifted btd \n" + str(volc_name) + " " + str(filefmt[1:14]))
        plt.legend()
        plt.savefig("Histogram_" + str(volc_name) + " " + str(filefmt[1:14]) + "_btds.png")
        plt.show()

        print("Ash pixels detected after any corrections: " + str(ash_pixel_count_new))
        print("Ash percentage within polygon: " + str(100*ash_fraction))
        print("Ash percentage within image: " + str(100*ash_pixel_count_new/(512*512)))
    else:
        btd_masked = np.ma.array(btd, mask=makemask(coords, scene)[0] == False)
        ash_map = np.ma.masked_greater_equal(btd_masked, 0)
        ash_map_export = -np.sign(ash_map)
    mask_image_full = makemask(coords, scene)[0]
    mask_image_standard = mask_image_full[std_msq[0]:std_msq[1], std_msq[2]:std_msq[3]]
    b14_map = b14_square
    b15_map = b15_square
    return btd_map, ash_map_export, filefmt, mask_image_standard, b14_map, b15_map


def generate_ash_and_all_data_map(vapath,datpath,index,region,type):  #not done yet
    coords = (get_vaac_data(vapath))[index][1]
    filefmt = (get_vaac_data(vapath))[index][0]
    print("Loading himawari8 data from: " + str((get_vaac_data(vapath))[index][0]))
    print("Polygon coordinates found: " + str(coords))
    xcoords = (list(zip(*coords)))[0]
    ycoords = (list(zip(*coords)))[1]
    print("Creating scene...")
    scene = make_scene(filefmt, datpath)
    scene.load(all_channels)
    print("Scene successfully loaded: ")
    b01 = scene['B01'].values[:, :]
    b02 = scene['B02'].values[:, :]
    b03 = scene['B03'].values[:, :]
    b04 = scene['B04'].values[:, :]
    b05 = scene['B05'].values[:, :]
    b06 = scene['B06'].values[:, :]
    b07 = scene['B07'].values[:, :]
    b08 = scene['B08'].values[:, :]
    b09 = scene['B09'].values[:, :]
    b10 = scene['B10'].values[:, :]
    b11 = scene['B11'].values[:, :]
    b12 = scene['B12'].values[:, :]
    b13 = scene['B13'].values[:, :]
    b14 = scene['B14'].values[:, :]
    b15 = scene['B15'].values[:, :]
    b16 = scene['B16'].values[:, :]
    # features to possibly include:
    # solar zenith angle
    # lat/lon relative to central lat/lon
    # whether a pixel is over sea or land
    std_msq = makemask(coords, scene)[2]

    if type == "no_wv_correction":
        btd = b14-b15
        print("Uncorrected btd generated.")
    elif type == "static_wv_correction":
        btd_uncorrected = b14 - b15
        btd_uncorrected = btd_uncorrected[std_msq[0]:std_msq[1], std_msq[2]:std_msq[3]]
        b14_square = scene['B14'].values[std_msq[0]:std_msq[1], std_msq[2]:std_msq[3]]
        idx, idy = np.where(b14_square == np.nanmax(b14_square))
        i, j = idx[0], idy[0]  # only take first solution
        btd_Tmax = btd_uncorrected[i, j]
        b14_max = b14_square[i, j]
        b = 6. - np.log(btd_Tmax)
        btd = b14 - b15 - np.exp(6. * (b14 / b14_max) - b)
    elif type == "dynamic_wv_correction":
        btd = b14 - b15 - np.exp(6. * (b14 / 320.) - (4.0 + np.cos(xcoords[1])))
        print("Dynamic corrected btd generated.")
    else:
        btd = b14-b15
        print("Invalid entry. Uncorrected btd generated.")
    msq = makemask(coords, scene)[1] #this is a plot region if you only want to look at the region of the polygon
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


def find_missing_data(vapath, datpath, print_good):  # Run this if you're getting empty images to check which data is missing
    data = get_vaac_data(vapath)
    for i in range(len(data)):
        fileformat = data[i][0]
        filelist = glob.glob(str(Filepath(datpath + "\\" + fileformat)))
        if filelist == []:
            print("No files found for date " + str(data[i][2]))
        else:
            if print_good:
                print(str(len(filelist)/16) + " filesets found for date " + str(data[i][2]))


def NormalizeData(data):
    return (data - np.nanmin(data)) / (np.nanmax(data) - np.nanmin(data))

html_data = get_vaac_data(htmlpath)
s = "E:\\TRAINING\\"

def generate_polygon_labelled_data(vapath,datpath,i,show_image,rotations):
    # read relevant data from VAAC warnings in vapath
    data = get_vaac_data(vapath)
    file_format = data[i][0]
    print(f"Fileformat is {file_format}")
    polygon_coords = data[i][1]
    volcano_code = data[i][2][10 + len(htmlpath):18 + len(htmlpath)]
    volcano_name = n_dict[volcano_code]

    # make satpy scene out of required himawari8 data
    scene = make_scene(file_format,datpath)

    # load all the data
    scene.load(all_channels)

    # resample our data to the same resolution (2km at subsurface pt)
    lscene = scene.resample(scene.coarsest_area(), resampler='native')

    # load in data about the polygon
    mask_data = makemask(polygon_coords,lscene)
    polygon_mask_full = mask_data[0]
    square = mask_data[2]  # r1 r2 c1 c2 coordinates of 512x512 pixel square around polygon
    polygon_mask_square = polygon_mask_full[square[0]:square[1], square[2]:square[3]]

    # load in all the other satellite data (visible and IR bands)
    b01 = lscene['B01'].values[square[0]:square[1], square[2]:square[3]]
    b02 = lscene['B02'].values[square[0]:square[1], square[2]:square[3]]
    b03 = lscene['B03'].values[square[0]:square[1], square[2]:square[3]]
    b04 = lscene['B04'].values[square[0]:square[1], square[2]:square[3]]
    b05 = lscene['B05'].values[square[0]:square[1], square[2]:square[3]]
    b06 = lscene['B06'].values[square[0]:square[1], square[2]:square[3]]
    b07 = lscene['B07'].values[square[0]:square[1], square[2]:square[3]]
    b08 = lscene['B08'].values[square[0]:square[1], square[2]:square[3]]
    b09 = lscene['B09'].values[square[0]:square[1], square[2]:square[3]]
    b10 = lscene['B10'].values[square[0]:square[1], square[2]:square[3]]
    b11 = lscene['B11'].values[square[0]:square[1], square[2]:square[3]]
    b12 = lscene['B12'].values[square[0]:square[1], square[2]:square[3]]
    b13 = lscene['B13'].values[square[0]:square[1], square[2]:square[3]]
    b14 = lscene['B14'].values[square[0]:square[1], square[2]:square[3]]
    b15 = lscene['B15'].values[square[0]:square[1], square[2]:square[3]]
    b16 = lscene['B16'].values[square[0]:square[1], square[2]:square[3]]

    if show_image:
        normal_b14_map = NormalizeData(b14)
        normal_b15_map = NormalizeData(b15)
        rgb_uint8 = (np.dstack((normal_b14_map, normal_b15_map, polygon_mask_square)) * 255.999).astype(
            np.uint8)
        img = Image.fromarray(rgb_uint8)
        img.save(("polygon_map_" + str(file_format[1:14]) + "_" + str(volcano_name) + ".png"))

    # we now wish to save the data as a 512x512x17 array

    output_array = np.dstack((b01, b02, b03, b04, b05, b06, b07, b08, b09, b10, b11,
                             b12, b13, b14, b15, b16, polygon_mask_square)).astype(np.float32)

    print("Shape of output_array: " + str(output_array.shape))
    output_filename = s + volcano_name + "-" + file_format[1:14] + ".npy"
    np.save(output_filename, output_array)
    print("File saved " + str(i))

    if rotations:
        output_filename_90 = s + volcano_name + "-" + file_format[1:14] + "-90.npy"
        output_filename_180 = s + volcano_name + "-" + file_format[1:14] + "-180.npy"
        output_filename_270 = s + volcano_name + "-" + file_format[1:14] + "-270.npy"
        np.save(output_filename_90,np.rot90(output_array, 1, axes=(0, 1)))
        np.save(output_filename_180, np.rot90(output_array, 2, axes=(0, 1)))
        np.save(output_filename_270, np.rot90(output_array, 3, axes=(0, 1)))

# done 2,822,20 3,823,20 4,824,20 5,825,20 6,826,20, 7,827,20 8,828,20 9,829,20 10,830,20 11,831,20 12,832,20 13,833,20
# 14,834,20 15,835,20 16,836,20 17,837,20 18,838,20 19,839,20 20,840,20 21,841,20 861,966,1
for i in range(0,1):
    generate_polygon_labelled_data(htmlpath, datapath, i, True, False)

# data = get_vaac_data(htmlpath)
#
# import subprocess
#
# b_dir = "E:\BROKEN_HTML"
#
# for i in range(0,1022):
#     #print(f"{data[i][0]} was this bad before? {data[i][4]}")
#     if data[i][4] == True:
#         print(f"copy \"{data[i][2]}\" \"{b_dir}{data[i][2][len(htmlpath):]}\" ")
#         subprocess.call(f"copy {data[i][2]} {b_dir}{data[i][2][len(htmlpath):]} " , shell = True)
#
#





#
# for i in range(1,233,2):
#     u = np.zeros((512,512))
#     if html_data[i][2][10 + len(htmlpath):18 + len(htmlpath)] == '28409600':
#         my_btd_and_ash_map = generate_btd_and_ash_map(htmlpath, datapath, i,
#                                                       "standard", "iterative_wv_correction")
#         file_flag = html_data[i][0][1:14]
#         volc_code = html_data[i][2][10 + len(htmlpath):18 + len(htmlpath)]
#         volc_name = n_dict[volc_code]
#         # plt.imsave(("btd_map_" + str(file_flag) + "_standard_modified_threshold.png"), my_btd_and_ash_map[0],
#                    # vmin=-5, vmax=5, cmap='RdBu')
#         # plt.imsave(("ash_map_" + str(file_flag) + "_" + str(volc_name) + "_standard_modified_threshold.png"), my_btd_and_ash_map[1],
#                   #  vmin=-5, vmax=5, cmap='RdBu')
#
#         normal_btd_map = my_btd_and_ash_map[0]/np.nanmax(my_btd_and_ash_map[0])
#         normal_b14_map = NormalizeData(my_btd_and_ash_map[4])
#         normal_b15_map = NormalizeData(my_btd_and_ash_map[5])
#
#         rgb_uint8 = (np.dstack((u, np.ma.array(my_btd_and_ash_map[1],mask=my_btd_and_ash_map[3]), u)) * 255.999).astype(np.uint8)
#         img = Image.fromarray(rgb_uint8)
#         img.save(("ash_map_" + str(file_flag) + "_" + str(volc_name) + ".png"))
#
#         # my_btd_and_ash_map[1][np.where(my_btd_and_ash_map[1] != 1.0)] = 0
#         # burned_map = my_btd_and_ash_map[0] - (2*my_btd_and_ash_map[3])
#         # plt.imsave(("mixed_map_" + str(file_flag) + "iterative_wv_correction.png"), burned_map,
#         #            vmin=-5, vmax=5, cmap='RdYlBu')
#
#         # rgb_uint8 = (np.dstack((normal_b14_map,normal_btd_map,normal_b15_map)) * 255.999).astype(np.uint8)
#         # img = Image.fromarray(rgb_uint8)
#         # img.save(("IR_map_" + str(file_flag) + "_" + str(volc_name) + ".png"))
#
#
#



