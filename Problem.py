import matplotlib.path
import numpy as np
from matplotlib import pyplot as plt
from pathlib import Path as Filepath
from pyproj import Proj
import timeit
print("start")
timeit.timeit()
vertices = [(1,1),(2,3),(3,4),(4,2),(3,2.5),(2.5,2),(2.3,0.4)]
polygon = matplotlib.path.Path(vertices) #This returns a type error
xs = np.arange(0.0,5.001,0.001)
ys = np.arange(0.0,5.001,0.001)
x , y = np.meshgrid(xs,ys)
positions = np.vstack([x.ravel(), y.ravel()]).T
mask = polygon.contains_points(positions)
mask2d = np.resize(mask,(5001,5001))
print("stop")
plt.imshow(mask2d,"Accent_r")
plt.show()
print(timeit.timeit())

