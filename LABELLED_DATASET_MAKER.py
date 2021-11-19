###This program will loop through your vaa html folder
#For each, it will identify the set of .DAT files to read, and then read them
#It will then, for each set of .DAT files, create an array of numbers for each pixel in the image
#These numbers will be 0 for not ash, 1 for ash, and 2 for outside the disk of the earth
#It will do this by first calculating a brightness temperature difference for each pixel
#This overestimates the amount of ash in the image, so we use the vaac polygons to mask out
#Areas which we know do not contain ash
#The program should output pairs of image data, along with the array value associated with each pixel


#Note!!!!! Running this program dumps a lot of data into your hidden /temp folder like a lot of data

from VAA_HTML import download_command
from VAA_HTML import coords_file_pairs
from pathlib import Path as Filepath
from satpy import Scene
from pyresample import create_area_def
from DATA_FUNCTIONS import BTDs
import geopandas as gp
import numpy as np
import glob
from matplotlib import pyplot as plt
import matplotlib.path
from pyproj import Proj
from MASK_MAKER import makemask
from MASK_MAKER import makemask2

datapath = "D:\Test_download_folder"
htmlpath = "D:\Test_html_folder"

### Some test cases here
#download_command("D:\Test_html_folder") #this just prints the downloads you need to do one by one
#print(coords_file_pairs("D:\Test_html_folder")) #format [["*fileformat*",[(x,y),(x,y),...]] , ]

def make_scene(fileformat,datfilepath): #fileformat is "*YYYYMMDD_HHMM*"
    filelist = glob.glob(str(Filepath(datfilepath + "\\" + fileformat)))
    scn = Scene(filelist, reader='ahi_hsd')
    return scn

i = 0 #index of file you want to load for testing

coords = (coords_file_pairs(htmlpath))[i][1]
print("This is where we get the coords from: " + str(coords_file_pairs(htmlpath)))
print("Coordinates to be used:" + str(coords))
xcoords = (list(zip(*coords)))[0]
ycoords = (list(zip(*coords)))[1]
xcoordsrnd = np.round(xcoords,2)
ycoordsrnd = np.round(ycoords,2)

# scene1 = make_scene((coords_file_pairs(htmlpath))[1][0],datapath)
# scene1.load(['B14','B15','true_color'])
# area_def = create_area_def('eqc', "+proj=eqc", units="degrees",
#                            area_extent=[min(ycoordsrnd), min(xcoordsrnd), max(ycoordsrnd), max(xcoordsrnd)], resolution=0.02)
#
# scene1 = scene1.resample(area_def)
# T11 = scene1['B14'].values[:,:]
# T12 = scene1['B15'].values[:,:]
# BTD = T11-T12
# print("Size of data: " + str(np.size(BTD)))
# plt.imshow(BTD, vmin=-5, vmax=5, cmap='RdBu')
# plt.title("Raw BTD in region near polygon without mask")
# plt.show()
#
#
# b = 4.5 # maybe subtract a function of latitude (experiment needed)
# wv = np.exp(6. * (T11 / 320.) - b)
# BTDc = BTD-wv
# plt.imshow(BTDc, vmin=-5, vmax=5, cmap='RdBu')
# plt.title("BTD with water vapour correction near polygon without mask")
# plt.show()

#scene1.show('true_color')
#print("dir" + str(dir(scene1["B14"].attrs["area"])))

#ok now time to show the polygon in this thing

print("Coords: " + str(coords))
scene2 = make_scene((coords_file_pairs(htmlpath))[i][0], datapath)
scene2.load(['B14','B15'])
T11 = scene2['B14'].values[:,:]
T12 = scene2['B15'].values[:,:]
BTD = T11-T12-np.exp(6. * (T11 / 320.) - 4.5)
BTD_masked = np.ma.array(BTD, mask=makemask(coords,scene2)[0] == False)
print("Size of disk image: " + str(np.size(BTD)))
msq = makemask(coords,scene2)[1] #plotsquare
BTD_masked_new_area = BTD_masked[msq[0]:msq[1],msq[2]:msq[3]]
BTD_new_area = BTD[msq[0]:msq[1],msq[2]:msq[3]]
# plt.imshow(BTD_masked,vmin=-5, vmax=5, cmap='RdBu')
# plt.title("BTD with applied VAAC mask: ")
# plt.show()
plt.imshow(BTD_masked_new_area,vmin=-5, vmax=5, cmap='RdBu')
plt.title("BTD with applied VAAC mask in the right area: ")
plt.show()
plt.imshow(BTD,vmin=-5, vmax=5, cmap='RdBu')
plt.title("BTD")
plt.imsave("full_disk_image_BTD.png",BTD,vmin=-5, vmax=5, cmap='RdBu')
plt.show()
plt.imshow(BTD_new_area,vmin=-5, vmax=5, cmap='RdBu')
plt.title("BTD Smaller Area")
plt.show()

ash_map = np.ma.masked_greater_equal(BTD_masked, 0)
ash_map = np.sign(ash_map)
print(ash_map)
print(ash_map[5][5])

plt.imshow(ash_map,vmin=-5, vmax=5, cmap='RdBu')
plt.title("Ash pixels")
plt.imsave("ash_pixels.png",ash_map)
plt.show()










