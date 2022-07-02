from matplotlib import pyplot as plt
import numpy as np
from math import isclose

def Plot_cartesian_points(points:list,ax=None)->plt:
    if ax==None:
        fig=plt.figure()
        ax=plt.axes(projection='3d')

    #   Plots the origin seperately
    points_=[]
    for point in points:
        dx=isclose(point.coords[0],0,abs_tol=1e-13)
        dy=isclose(point.coords[1],0,abs_tol=1e-13)
        dz=isclose(point.coords[2],0,abs_tol=1e-13)

        if dx==False or dy==False or dz==False:
            points_.append(point)
    points=points_

    x=[point.coords[0] for point in points]
    y=[point.coords[1] for point in points]
    z=[point.coords[2] for point in points]

    ax.scatter(x,y,z,color='r')
    ax.scatter(0,0,0,color='g')

    return plt

def Plot_polylines(polylines:list,ax=None)->plt:
    if ax==None:
        fig=plt.figure()
        ax=plt.axes(projection='3d')
    
    for line in polylines:
        x=[line.points_coord[0][0],line.points_coord[1][0]]
        y=[line.points_coord[0][1],line.points_coord[1][1]]
        z=[line.points_coord[0][2],line.points_coord[1][2]]
        ax.plot(x,y,z,color='k')

    return plt

def Plot_circles(circles:list,ax=None)->plt:
    POINTS=50

    if ax==None:
        fig=plt.figure()
        ax=plt.axes(projection='3d')
    
    for circle in circles:
        v1=circle.plane[0]
        v2=circle.plane[1]
        r=circle.radius
        centre=circle.centre

        #   Generates points around circle for plot
        coords=[]
        for i in range(POINTS):
            t=i/POINTS
            theta=t*2*np.pi

            coords.append(centre+r*(np.cos(theta)*v1+np.sin(theta)*v2))

        #   Plots circle
        for i,coord in enumerate(coords):
            if i==len(coords)-1:
                ax.plot(xs=[coord[0],coords[0][0]],
                        ys=[coord[1],coords[0][1]],
                        zs=[coord[2],coords[0][2]],
                        color='k')
                break

            x=[coord[0],coords[i+1][0]]
            y=[coord[1],coords[i+1][1]]
            z=[coord[2],coords[i+1][2]]
            ax.plot(x,y,z,color='k')

    return plt