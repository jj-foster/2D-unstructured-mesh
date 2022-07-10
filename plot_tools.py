from matplotlib import lines, pyplot as plt
import numpy as np

def Plot_cartesian_points(points:list,ax=None)->plt:
    if ax==None:
        fig=plt.figure()
        ax=plt.axes(projection='3d')

    """
    #   Removes origin from plot
    points_=[]
    for point in points:
        if point.name==None and np.array_equal(point.coords,[0,0,0])==True:
            continue
        else:
            points_.append(point)
    points=points_
    """
    
    x=[point.coords[0] for point in points]
    y=[point.coords[1] for point in points]
    z=[point.coords[2] for point in points]

    max_dim=abs(max([max(x),max(y)]))

    ax.scatter(x,y,color='r',s=10)
    #ax.scatter(0,0,color='g')

    return plt

def Plot_polylines(polylines:list,ax=None)->plt:
    if ax==None:
        fig=plt.figure()
        ax=plt.axes(projection='3d')
    
    for line in polylines:
        x,y,z=line.gen_nodes(spacing=np.linalg.norm(line.points[1]-line.points[0])).T
        ax.plot(x,y,color='k')

    return plt

def Plot_circles(circles:list,ax=None)->plt:
    POINTS=100

    if ax==None:
        fig=plt.figure()
        ax=plt.axes(projection='3d')
    
    for circle in circles:
        x,y,z=circle.gen_nodes(N=POINTS).T
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

def Plot_lines(lines:list,ax=None)->plt:
    if ax==None:
        fig=plt.figure()
        ax=plt.axes(projection='3d')
    


    return plt

def Plot_geom(geom_dict:dict,cartesian_points:bool=True,
                   polylines:bool=True,circles:bool=True,
                   bsplines:bool=True,lines=True):
    
    points      = [x for x in geom_dict.values() if type(x).__name__=='Cartesian_point']
    lines_      = [x for x in geom_dict.values() if type(x).__name__=='Line']
    polylines_  = [x for x in geom_dict.values() if type(x).__name__=='Polyline']
    circles_    = [x for x in geom_dict.values() if type(x).__name__=='Circle']
    bsplines_   = [x for x in geom_dict.values() if type(x).__name__=='B_spline_curve_with_knots']

    fig=plt.figure()
    ax=plt.axes()

    if cartesian_points==True:
        points_plt=Plot_cartesian_points(points,ax)
    if polylines==True:
        polyline_plt=Plot_polylines(polylines_,ax)
    if circles==True:
        circle_plt=Plot_circles(circles_,ax)
    if bsplines==True:
        bspline_plt=Plot_bspline(bsplines_,ax)
    if lines==True:
        lines_plt=Plot_lines(lines_,ax)

    ax.set_xlabel('x')
    ax.set_ylabel('y')
    #ax.set_zlabel('z')
    ax.set_aspect('equal')

    #plt.tight_layout()
    plt.show()

def Plot_nodes_3d(nodes:list):
    x,y,z=nodes.T

    #   basically if in one plane
    if np.ptp(x)!=0:
        x_aspect=np.ptp(x)
    else:
        x_aspect=0.0000001
    if np.ptp(y)!=0:
        y_aspect=np.ptp(y)
    else:
        y_aspect=0.0000001
    if np.ptp(z)!=0:
        z_aspect=np.ptp(z)
    else:
        z_aspect=0.0000001

    fig=plt.figure()
    ax=plt.axes(projection='3d')

    ax.scatter(x,y,z,s=5)
    ax.set_box_aspect((x_aspect,y_aspect,z_aspect))
    plt.tight_layout()
    plt.show()

    return None

def Plot_nodes_2d(nodes:np.ndarray):
    x,y,z=nodes.T

    fig=plt.figure()
    ax=plt.axes()

    ax.scatter(x,y,s=5)

    ax.set_aspect('equal')
    plt.tight_layout()
    plt.show()

    return None