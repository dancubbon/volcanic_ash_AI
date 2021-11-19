###This will contain functions which act on the Himawari data itself
# BTD gives 1 and 0 map -- want to ignore all 1s (ASH) outside of the polygons
#
import matplotlib.path
import numpy as np
import satpy

def BTDs(B14, B15, polygon, datascene, r1, r2, c1, c2):
    """
    Calculates brightness temperatures corrected by the Yu et al.
    semi-empirical water vapour correction. Then masks pixels outside the
    Tokyo VAAC polygon.
    """
    #B14 = arrays containing brightness temperature for channel 14
    #B15 = arrays containing brightness temperature for channel 15
    #polygon = list of vertices for the VAAC polygon
    #
    # r1 = top row containing pixel values
    # c1 = first column containing pixel values
    # r2 = bottom row of pixel values
    # c2 = last column of pixel values
    #lcn = all of the data from Himawari-8 for a particular time, we can access each channel from this

    # We now use the satellite data and VAAC polygon to determine ash location.
    # Plot brightness temperature difference to detect ash (-ve = ash, +ve = water/ice)
    T11 = B14
    T12 = B15
    BTD = T11 - T12

    # Notice how the whole plume isn't detected by this difference. This is due to
    # the interference of water vapour. To address this we can apply the Yu et al.
    # semi-emprical water vapour correction.
    # Note: increasing b reduces the water vapour correction)
    b = 4.5
    wv = np.exp(6. * (T11 / 320.) - b)
    BTD_wv = BTD - wv

    # We here mask the data outside the VAAC polygon

    # Get lons and lats for each point in our area? Not sure if these are correct
    # or if I need to convert them? They seem to work...?
    lons, lats = datascene['B14'].attrs['area'].get_lonlats()
    lons, lats = lons[r1:r2, c1:c2], lats[r1:r2, c1:c2]

    # Create the array of BTDs for just ash
    x, y = lons.flatten(), lats.flatten()
    points = np.vstack((x, y)).T  # Creates stack of (repeating) lon and lat pairs
    p = matplotlib.path.Path(polygon)  # Connects polygon coords to make closed polygon
    grid = p.contains_points(points)  # Returns whether closed polygon contains point as array (example: [False False False ... False False False])
    Mask = grid.reshape(lats.shape)  # Creates a mask of the shape of our image (BTD_wv) with each index describing if the point is inside the closed polygon or not
    BTD_wv_ma = np.ma.array(BTD_wv,
                            mask=Mask == False)  # BTDs inside polygon only. mask=Mask==False sets all the points of BTD_wv which have a False value in Mask to be masked

    # Masks BTDs greater than or equal to zero
    BTD_wv_ma = np.ma.masked_greater_equal(BTD_wv_ma, 0)

    return BTD_wv, BTD_wv_ma
