import numpy as np
import matplotlib.path
import matplotlib.pyplot as plt
import satpy

def makemask(coords,scn):
    #coords = [(lat,lon),(lat,lon),...]
    #scn = Scene(filelist, reader = 'ahi_hsd')
    #first we project the lat lon coordinates to pixel coordinates
    lats = (list(zip(*coords)))[0] #unzips list of coordinate tuples into lats and lons
    lons = (list(zip(*coords)))[1]
    coordproj = scn["B14"].attrs["area"].get_xy_from_lonlat(lons,lats) #returns pixel coordinates given angular coordinates
    x, y = coordproj[0],coordproj[1]
    pixel_coords = list(zip(x, y)) #puts them back into the right format for the matplotlib Path function
    print("Pixel coordinates: " + str(pixel_coords))
    polygon = matplotlib.path.Path(pixel_coords) #produces the polygon object
    xs = np.arange(1, 5501, 1)
    ys = np.arange(1, 5501, 1) #create a blank array of the same size as the himawari images
    a, b = np.meshgrid(xs, ys)
    positions = np.vstack([a.ravel(), b.ravel()]).T
    mask = polygon.contains_points(positions) #creates mask by checking each point in positions for if it's in the polygon
    mask2d = mask.reshape(5500,5500)
    masksquare = [min(y),max(y),min(x),max(x)] #pixel square around which is the mask
    return mask2d,masksquare #Array of true/false depending on if the pixel is in the polygon or not

def makemask2(coords,scn):
    #coords = [(lat,lon),(lat,lon),...]
    #scn = Scene(filelist, reader = 'ahi_hsd')
    #first we project the lat lon coordinates to pixel coordinates
    #polylats = (list(zip(*coords)))[0] #unzips list of coordinate tuples into lats and lons
    #polylons = (list(zip(*coords)))[1]
    lons, lats = scn["B14"].attrs["area"].get_lonlats() #returns pixel coordinates given angular coordinates
    print("lonlats are: " + str(lons) + str(lats))
    x, y = lons.flatten(), lats.flatten()
    points = np.vstack((x, y)).T
    print("points to check if they are in the polygon: " + str(points))
    p = matplotlib.path.Path(coords)
    grid = p.contains_points(points)  # Returns whether closed polygon contains point as array (example: [False False False ... False False False])
    print("1d? grid of truefalses: " + str(grid))
    mask2d = grid.reshape(lats.shape) # Creates a mask of the shape of our image (BTD_wv) with each index describing if the point is inside the closed polygon or not
    plt.imshow(mask2d)
    plt.title("latlonmask")
    plt.show()
    return mask2d #Array of true/false depending on if the pixel is in the polygon or not


