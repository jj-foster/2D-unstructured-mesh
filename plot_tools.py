from matplotlib import pyplot as plt
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

    ax.set_xlabel('x')
    ax.set_ylabel('y')
    #ax.set_zlabel('z')
    ax.set_aspect('equal')

    #plt.tight_layout()
    plt.ax()

def Plot_nodes_3d(nodes:np.ndarray,labels=False,ax=None,line=False):
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

    if ax==None:
        fig=plt.figure()
        ax_=plt.axes(projection='3d')
    else:
        ax_=ax

    if line==False:
        ax_.scatter(x,y,z,s=5)
    else:
        ax_.plot(x,y,'o-')

    if labels==True:
        for i,node in enumerate(nodes):
            ax_.text(node[0],node[1],node[2],s=i)

    ax_.set_box_aspect((x_aspect,y_aspect,z_aspect))
    plt.tight_layout()

    if ax==None:
        plt.show()
        pass
    else:
        return plt

def Plot_nodes_2d(nodes:np.ndarray,labels=False,ax=None,line=False):
    x,y,z=nodes.T

    if ax==None:
        fig=plt.figure()
        ax_=plt.axes()
    else:
        ax_=ax

    if line==False:
        ax_.scatter(x,y,s=5)
    else:
        ax_.plot(x,y,'o-')

    if labels==True:
        for i,node in enumerate(nodes):
            ax_.text(node[0],node[1],s=i)

    ax_.set_aspect('equal')
    plt.tight_layout()

    if ax==None:
        plt.show()
        pass
    else:
        return plt

def Plot_edges(edges,projection,labels=True,line=False,ax=None):
    if ax==None:
        fig=plt.figure()
        ax_=plt.axes()
    else:
        ax_=ax

    if projection=='2d':  
        ax_.set_aspect('equal')
    elif projection=='3d':
        ax_=plt.axes(projection='3d')

    for edge in edges:
        nodes=edge.nodes

        if projection=='2d':  
            fig=Plot_nodes_2d(nodes,labels=labels,ax=ax_,line=line)
        elif projection=='3d':
            fig=Plot_nodes_3d(nodes,labels=labels,ax=ax_,line=line)

    if ax==None:
        plt.show()
        pass
    else:
        return fig

def Plot_panels(panels,ax=None):
    if ax==None:
        fig=plt.figure()
        ax_=plt.axes()
    else:
        ax_=ax

    for panel in panels:
        x,y,z=panel.points.T

        if panel.D==None:
            ax_.plot(x,y,'o-')
    
    ax_.set_aspect('equal')
    
    if ax==None:
        plt.show()
        pass
    else:
        return plt