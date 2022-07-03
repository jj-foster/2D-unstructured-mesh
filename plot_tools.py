from matplotlib import pyplot as plt
import numpy as np

def Plot_cartesian_points(points:list,ax=None)->plt:
    if ax==None:
        fig=plt.figure()
        ax=plt.axes(projection='3d')

    #   Removes origin from plot
    points_=[]
    for point in points:
        if point.name!=None and np.array_equal(point.coords,[0,0,0])!=True:
            points_.append(point)
    points=points_

    x=[point.coords[0] for point in points]
    y=[point.coords[1] for point in points]
    #z=[point.coords[2] for point in points]

    max_dim=abs(max([max(x),max(y)]))

    ax.scatter(x,y,color='r',s=max_dim/10)
    #ax.scatter(0,0,color='g')

    return plt

def Plot_polylines(polylines:list,ax=None)->plt:
    if ax==None:
        fig=plt.figure()
        ax=plt.axes(projection='3d')
    
    for line in polylines:
        x=[line.points[0][0],line.points[1][0]]
        y=[line.points[0][1],line.points[1][1]]
        #z=[line.points_coord[0][2],line.points_coord[1][2]]
        ax.plot(x,y,color='k')

    return plt

def Plot_circles(circles:list,ax=None)->plt:
    POINTS=100

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
        for i in range(POINTS+1):
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
            #z=[coord[2],coords[i+1][2]]
            ax.plot(x,y,color='k')

    return plt

def Plot_bspline(bsplines:list,ax=None)->plt:

    if ax==None:
        fig=plt.figure()
        ax=plt.axes(projection='3d')
    
    for bspline in bsplines:
        range=np.linspace(
            bspline.knot_vector[0],
            bspline.knot_vector[-1],
            bspline.ctrl_pts.shape[0]*100
        )
        x,y,z=bspline.bspline(range).T
        
        ax.plot(x,y,'k')
        ax.plot(bspline.ctrl_pts[:,0],bspline.ctrl_pts[:,1],'--')

    return plt

def Plot_geom(geom_dict:dict,cartesian_points:bool=True,
                   polylines:bool=True,circles:bool=True,
                   bsplines:bool=True):
    
    points   = [x for x in geom_dict.values() if type(x).__name__=='Cartesian_point']
    lines    = [x for x in geom_dict.values() if type(x).__name__=='Polyline']
    circles_ = [x for x in geom_dict.values() if type(x).__name__=='Circle']
    bsplines_= [x for x in geom_dict.values() if type(x).__name__=='B_spline_curve_with_knots']

    fig=plt.figure()
    ax=plt.axes()

    if cartesian_points==True:
        points_plt=Plot_cartesian_points(points,ax)
    if polylines==True:
        line_plt=Plot_polylines(lines,ax)
    if circles==True:
        circle_plt=Plot_circles(circles_,ax)
    if bsplines==True:
        bspline_plt=Plot_bspline(bsplines_,ax)

    ax.set_xlabel('x')
    ax.set_ylabel('y')
    #ax.set_zlabel('z')
    ax.set_aspect('equal')

    plt.tight_layout()
    plt.show()

def Plot_nodes(nodes:list):
    x,y,z=nodes.T
    fig=plt.figure()
    ax=plt.axes()
    ax.plot(x,y)
    ax.set_aspect('equal')
    plt.show()

    return None