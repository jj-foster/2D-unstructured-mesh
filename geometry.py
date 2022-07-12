from multiprocessing.sharedctypes import Value
import pandas as pd
import numpy as np
import re
from scipy.interpolate import BSpline, splev
from matplotlib import pyplot as plt

from plot_tools import Plot_geom, Plot_nodes_2d

"""
ADVANCED_FACE
    PLANE
    FACE_OUTER_BOUND+FACE_BOUND
        EDGE_LOOP
            ORIENTED EDGE
                EDGE_CURVE
                    VERTEX POINT
                    <geometry object>

geometry object:
    LINE
    POLYLINE
    CIRCLE
    BSPLINE
"""

DATA_HIERARCHY=[
    'CARTESIAN_POINT',
    'VERTEX_POINT',
    'DIRECTION',
    'VECTOR',
    'LINE',
    'AXIS2_PLACEMENT_3D',
    'PLANE',
    'TRIMMED_CURVE',
    'POLYLINE',
    'CIRCLE',
    'B_SPLINE_CURVE_WITH_KNOTS',
    'EDGE_CURVE',
    'ORIENTED_EDGE',
    'EDGE_LOOP',
    'FACE_BOUND',
    'ADVANCED_FACE'
]

class Cartesian_point():
    def __init__(self,raw_data:pd.Series):
        properties=raw_data['properties']
        coords=properties[properties.find("(")+1:properties.find(")")].split(',')
        
        self.id         =   int(raw_data['id'][1:])
        self.name       =   properties.split(',')[0][1:-1]
        self.coords     =   np.array([float(x) for x in coords])
        self.child      =   True

        if self.name=="":
            self.name=None

        return None

class Vertex_point():
    def __init__(self,raw_data):
        properties=raw_data['properties'].split(',')

        self.id         =   int(raw_data['id'][1:])
        self.name       =   properties[0][1:-1]
        self.coords     =   None

        self.coords_id  =   int(properties[1][1:])

        if self.name=="":
            self.name=None

    def fill_data(self,geom_dict):
        self.coords =   geom_dict[self.coords_id].coords

        return None

class Direction():
    def __init__(self,raw_data:pd.Series):
        properties=raw_data['properties']
        vector =   properties[properties.find("(")+1:properties.find(")")].split(',')

        self.id         =   int(raw_data['id'][1:])
        self.name       =   properties.split(',')[0][1:-1]
        self.vector     =   np.array([float(x) for x in vector])

        if self.name=="":
            self.name=None

class Vector():
    def __init__(self,raw_data):
        properties=raw_data['properties'].split(',')

        self.id             =   int(raw_data['id'][1:])
        self.name           =   properties[0][1:-1]
        self.length         =   float(properties[2])
        self.vector         =   None
        
        self.direction_id   =   int(properties[1][1:])

        if self.name=="":
            self.name=None

    def fill_data(self,geom_dict):
        self.vector =   geom_dict[self.direction_id].vector

        return None

class Line():
    def __init__(self,raw_data):
        properties=raw_data['properties'].split(',')

        self.id         =   int(raw_data['id'][1:])
        self.name       =   properties[0][1:-1]
        self.vector     =   None
        self.length     =   None
        self.point      =   None

        self.point_id   =   int(properties[1][1:])
        self.vector_id  =   int(properties[2][1:])

        if self.name=="":
            self.name=None

    def fill_data(self,geom_dict):
        vector_obj  =   geom_dict[self.vector_id]

        self.vector =   vector_obj.vector
        self.length =   vector_obj.length
        self.point  =   geom_dict[self.point_id].coords

        return None

class Axis2_placement_3d():
    """Basically a local coordinate system definition"""
    def __init__(self,raw_data:pd.Series):
        properties=raw_data['properties'].split(',')

        self.id         =   int(raw_data['id'][1:])
        self.name       =   properties[0][1:-1]
        self.origin     =   None
        self.axis       =   None
        self.ref_vector =   None

        self.origin_id      =   int(properties[1][1:])
        self.axis_id        =   int(properties[2][1:])
        self.ref_vector_id  =   int(properties[3][1:])

    def fill_data(self,geom_dict):
        self.origin     =   geom_dict[self.origin_id].coords
        self.axis       =   geom_dict[self.axis_id].vector
        self.ref_vector =   geom_dict[self.ref_vector_id].vector

        return None

class Plane():
    def __init__(self,raw_data):
        properties=raw_data['properties'].split(',')

        self.id         =   int(raw_data['id'][1:])
        self.name       =   properties[0][1:-1]
        self.axis       =   None
        
        self.axis_id    =   int(properties[1][1:])

        if self.name=="":
            self.name=None

    def fill_data(self,geom_dict):
        self.axis =   geom_dict[self.axis_id]

        return None

class Trimmed_curve():
    """
    Overwites a circle. Trims curve between trim1 and trim2
    """
    def __init__(self,raw_data:pd.Series):
        properties=raw_data['properties'].split(',')

        self.id         =   int(raw_data['id'][1:])
        self.name       =   properties[0][1:-1]
        self.basis      =   None
        self.trim1      =   None
        self.trim2      =   None
        self.child      =   True

        self.basis_id   =   int(properties[1][1:])
        self.trim1_id   =   int(properties[2][2:])
        self.trim2_id   =   int(properties[4][2:])

        if self.name=="":
            self.name=None

    def fill_data(self,geom_dict):
        self.basis  =   geom_dict[self.basis_id] #   circle object
        self.trim1  =   geom_dict[self.trim1_id].coords
        self.trim2  =   geom_dict[self.trim2_id].coords

        geom_dict[self.basis_id].trim=self

        return None

class Polyline():
    """3D line connecting 2 cartesian points."""
    def __init__(self,raw_data:pd.Series=None,points:np.ndarray=None):
        if raw_data!=None:
            properties=raw_data['properties']
            points=properties[properties.find("(")+1:properties.find(")")].split(',')

            self.id         =   int(raw_data['id'][1:])
            self.name       =   properties.split(',')[0][1:-1]
            self.points     =   None    #   in form [[x0,y0,z0],[x1,y1,z1]]

            self.points_id  =   [int(x[1:]) for x in points]

            if self.name=="":
                self.name=None
            
        else:
            self.points=points  #   in form [[x0,y0,z0],[x1,y1,z1]]

    def fill_data(self,geom_dict):
        self.points =   [geom_dict[self.points_id[0]].coords,
                        geom_dict[self.points_id[1]].coords]
        
        return None

    def gen_nodes(self,spacing):
        vector=self.points[1]-self.points[0]
        length=np.linalg.norm(vector)
        N=int(round(length/spacing,0))+1

        nodes=np.zeros([N,3])
        for i,node in enumerate(nodes):
            t=i/(N-1)
            nodes[i]=self.points[0]+t*vector
        nodes[-1]=self.points[1]    #   corrects for floating point error

        return nodes

class Circle():
    def __init__(self,raw_data:pd.Series):
        properties=raw_data['properties'].split(',')

        self.id         =   int(raw_data['id'][1:])
        self.name       =   properties[0][1:-1]
        self.radius     =   float(properties[2])
        self.plane      =   None
        self.centre     =   None
        self.trim       =   None
        
        self.plane_id    =   int(properties[1][1:])

        if self.name=="":
            self.name=None

    def fill_data(self,geom_dict):
        axes_obj=geom_dict[self.plane_id]

        self.centre =   axes_obj.origin
        self.plane  =   [axes_obj.ref_vector,np.cross(axes_obj.axis,axes_obj.ref_vector)]

        return None

    def gen_nodes(self,spacing=None,N=None):
        v1=self.plane[0]
        v2=self.plane[1]

        if self.trim:
            start=self.trim.trim1
            end=self.trim.trim2
        else: 
            start=end=self.centre+v1*self.radius

        CR=self.radius*v1
        CS=start-self.centre
        CE=end-self.centre

        #   angle between v1 and centre to trim1 vector
        phi=np.arccos(np.dot(CR,CS)/(np.linalg.norm(CR)*np.linalg.norm(CS)))
        #   ensures full clockwise angle (starting at x' axis)
        if np.dot(v1,CS)<0:
            phi=2*np.pi-phi

        #   rotate v1,v2 to align with first trim coordinate
        v1_=v1*np.cos(phi)+v2*np.sin(phi)
        v2_=-v1*np.sin(phi)+v2*np.cos(phi)

        #   angle to draw between start and end points
        theta_=np.arccos(np.dot(CE,CS)/(np.linalg.norm(CS)*np.linalg.norm(CE)))
        if np.dot(v2_,CE)<=0:
            theta_=2*np.pi-theta_

        length=self.radius*(theta_)
        #   fix for tube_keel.stp - check which circles are missing
        if np.isnan(length):
            length=0

        #   generate theta range between start/end coords.
        if N==None and spacing!=None:
            N=int(round(length/spacing,0))
        elif N!=None and spacing==None:
            pass
        else:
            raise ValueError("No spacing or node number specified.")
        thetas=np.linspace(0,theta_,N)

        nodes=np.zeros([N,3])
        for i,theta in enumerate(thetas):
            nodes[i]=self.centre+self.radius*(np.cos(theta)*v1_+np.sin(theta)*v2_)
        
        #   corrects for floating point error with start/end nodes
        if theta_==2*np.pi:
            nodes[-1]=nodes[0]

        return nodes

class B_spline_curve_with_knots():
    """
    THEORY:
    Degree k       - The degree of polynomial as order n-1. Defined at knots over 1+n locations.
    Control points - Bounding polyline coordinates.
    Knots          - A vector defining continuity of curve with control points.
                     Vector is composed of knot function values represented in a list.
                     Knot values can be repeated to force curve to coincide with control point.
                     If curve is clamped to start/end control points, the start/end knot values are repeated k+1 times.

    'Interpolated' (curve goes through control point) and 'control vertex' are treated the same. CAD exports to common
    B-Spline format for STEP files. Control points for 'interpolated' will be modified automatically.
    """
    def __init__(self,raw_data):
        properties=[i.strip() for i in re.split(r',(?![^\(]*[\)])', raw_data['properties'])]
        str_to_bool=lambda x:True if (x=="T") else False

        self.id             =   int(raw_data['id'][1:])
        self.name           =   properties[0]
        self.degree         =   int(properties[1])
        self.ctrl_pts       =   None
        self.closed         =   str_to_bool(properties[4][1:-1])    #   bool
        self.self_intersect =   str_to_bool(properties[5][1:-1])    #   bool
        self.bspline        =   None

        knot_multipicities  =   [int(x) for x in properties[6][1:-1].split(',')]
        self.knot_values         =   [float(x) for x in properties[7][1:-1].split(',')]
        knot_vector         =   []
        
        #   multiply out knot values into knot vector according to multipicity values
        for i,_ in enumerate(self.knot_values):
            knot_vector.append([self.knot_values[i]]*knot_multipicities[i])
        self.knot_vector=[x for xs in knot_vector for x in xs]

        self.ctrl_pts_ids       =   [int(x[1:]) for x in properties[2][1:-1].split(',')]
                
        if self.name=="":
            self.name=None

    def fill_data(self,geom_dict):
        #   get coordinate values for control points
        self.ctrl_pts   =   np.array([geom_dict[x].coords for x in self.ctrl_pts_ids])

        #   create associated scipy B-spline object
        self.bspline    =   BSpline(self.knot_vector,self.ctrl_pts,self.degree)

        return None

    def gen_nodes(self,spacing:float):
        N_initial=int(self.ctrl_pts.shape[0]*30)

        spline_range_initial=np.linspace(
            self.knot_vector[0],
            self.knot_vector[-1],
            N_initial
        )
        points=self.bspline(spline_range_initial)

        #   calculate arclength of spline
        length=0
        length_list=[0]
        for i in range(len(points)-1):
            dL=np.linalg.norm(points[i]-points[i+1])
            length+=dL
            length_list.append(length)

        N=int(round(length/spacing,0))
        spacing_=length/N
        
        #   Searches for cumulative lengths between which each equadistant point lies referencing
        #   length list. The equidistant point is linearly interpolated between the points either
        #   side of it. 
        equidistant_points=np.zeros([N,3])
        dL=0
        for i in range(N):
            #   Binary search for index where cumulative length would lie.
            j_L=np.searchsorted(length_list,dL,side='left')
            j_R=j_L+1

            #   Gets points and cumulative lengths either side of the equadistant point.
            p_L=points[j_L]
            p_R=points[j_R]
            L_L=length_list[j_L]
            L_R=length_list[j_R]
            
            #   Linear interpolation
            ratio=(dL-L_L)/(L_R-L_L)

            p_LR=p_R-p_L
            p_j=p_L+ratio*p_LR

            equidistant_points[i]=p_j

            dL+=spacing_

        nodes=equidistant_points

        return nodes

class Edge_curve():
    def __init__(self,raw_data):
        properties=raw_data['properties'].split(',')

        self.id                 =   int(raw_data['id'][1:])
        self.name               =   properties[0][1:-1]
        self.start_coords       =   None
        self.end_coords         =   None
        self.edge_geom          =   None

        self.start_vertex_id    =   int(properties[1][1:])
        self.end_vertex_id      =   int(properties[2][1:])
        self.edge_geom_id       =   int(properties[3][1:])

        if self.name=="":
            self.name=None

    def fill_data(self,geom_dict):
        self.start_coords   =   geom_dict[self.start_vertex_id].coords
        self.end_coords     =   geom_dict[self.end_vertex_id].coords
        self.edge_geom      =   geom_dict[self.edge_geom_id]

        return None

class Oriented_edge():
    def __init__(self,raw_data):
        properties=raw_data['properties'].split(',')
        str_to_bool=lambda x:True if (x=="T") else False

        self.id             =   int(raw_data['id'][1:])
        self.name           =   properties[0][1:-1]
        self.orientation    =   str_to_bool(properties[4][1:-1])
        self.edge_curve     =   None

        self.edge_curve_id  =   int(properties[3][1:])

        if self.name=="":
            self.name=None

    def fill_data(self,geom_dict):
        self.edge_curve =   geom_dict[self.edge_curve_id]

        return None

class Edge_loop():
    def __init__(self,raw_data:pd.Series):
        properties=raw_data['properties']
        edges=properties[properties.find("(")+1:properties.find(")")].split(',')

        self.id         =   int(raw_data['id'][1:])
        self.name       =   properties[0][1:-1]
        self.edges      =   None

        self.edge_ids  =   [int(x[1:]) for x in edges]

        if self.name=="":
            self.name=None

    def fill_data(self,geom_dict):
        self.edges =   [geom_dict[i] for i in self.edge_ids]
        
        return None

    def gen_nodes(self,spacing:float)->np.ndarray:
        
        def find_next_edge(current_edge,edges):
            end=current_edge.edge_curve.end_coords

            for edge in edges:
                start=edge.edge_curve.start_coords
                if list(start)==list(end):
                    return edge

        #   Reorder edges so that they are head to tail.
        """
        list of edges
        start with first edge
        find edge with start coords that match previous edge end coords
        add edge to new list of edges
        """
        reordered=[self.edges[0]]       #   list grows
        unordered=self.edges
        unordered.remove(unordered[0])  #   list shrinks

        for i in range(len(self.edges)):
            current_edge=reordered[i]
            next_edge=find_next_edge(current_edge,unordered)

            reordered.append(next_edge)
            unordered.remove(next_edge)

        #   Generate nodes for each edge
        nodes=[]
        for edge in reordered:
            curve=edge.edge_curve
            start=curve.start_coords
            end=curve.end_coords
            geom=curve.edge_geom

            #print(start,end)
            
            if type(geom)==Line:
                polyline=Polyline(points=[start,end])
                nodes.append(polyline.gen_nodes(spacing))
            else:
                nodes.append(geom.gen_nodes(spacing))

        nodes=np.array([node for edge in nodes for node in edge])

        #   removoe duplicate nodes
        nodes_=[]
        for node in nodes:
            if (list(node) in nodes_)==False:
                nodes_.append(list(node))

        #   add back in duplicate start/end node
        nodes_.append(nodes_[0])
        nodes_=np.array(nodes_)

        return nodes_

class Face_bound():
    def __init__(self,raw_data,outer):
        properties=raw_data['properties'].split(',')
        str_to_bool=lambda x:True if (x=="T") else False

        self.id             =   int(raw_data['id'][1:])
        self.name           =   properties[0][1:-1]
        self.bound          =   None
        self.orientation    =   str_to_bool(properties[1][1:-1])
        self.outer          =   outer

        self.edge_loop_id       =   int(properties[1][1:])

        if self.name=="":
            self.name=None

    def fill_data(self,geom_dict):
        self.edge_loop  =   geom_dict[self.edge_loop_id]

        return None

class Advanced_face():
    def __init__(self,raw_data):
        properties=[i.strip() for i in re.split(r',(?![^\(]*[\)])', raw_data['properties'])]

        self.id         =   int(raw_data['id'][1:])
        self.name       =   properties[0][1:-1]
        self.bounds     =   None
        self.plane      =   None
        
        self.bound_ids   =   [int(x[1:]) for x in properties[1][1:-1].split(',')]
        self.plane_id   =   int(properties[2][1:])

        if self.name=="":
            self.name=None

    def fill_data(self,geom_dict):
        self.bounds =   [geom_dict[i] for i in self.bound_ids]
        self.plane  =   geom_dict[self.plane_id]

        return None

def Step_read(file:str,csv=False)->pd.Series:
    """
    Reads .STEP (or .stp) file.

    Parameters
    ----------
    file : str, to read.
    csv : bool, optional. To export step data as csv.

    """
    with open(file,'r') as f:
        lines=f.readlines()

    data_str=[]
    #   Gets only geometry data from step file
    read=False
    for line in lines:
        if read==True:
            data_str.append(line)

        if line=="DATA;\n":
            read=True
    
    data_str=[x.strip() for x in data_str]  #   removes /n from strings

    data_str="".join(data_str)  #   merges everything into one long string (strp files sometimes segment lines)
    data_str=data_str.split(';')    #   then splits by each data instance
    if data_str[-1]=="":    #   removes trailing file format bits
        data_str.pop(-1)
    data_str=data_str[:-2]

    data=pd.DataFrame(columns=['id','tag','properties'])
    #   Puts the data into a dataframe
    for str in data_str:
        str_=str.split('=')
        id=str_[0]
        tag=str_[1].split('(')[0]
        if tag=="":
            tag=None
        properties=str_[1][str_[1].find('(')+1:str_[1].find(');')]
        
        data=pd.concat([data,pd.DataFrame.from_records([{'id':id,'tag':tag,'properties':properties}])],ignore_index=True)

    data.dropna(axis=0,inplace=True)    #   removes blank entries
    #data=data[data['tag'].isin(DATA_HIERARCHY)]  #   removes entries that contain waffle data

    if csv==True:
        data.to_csv('data.csv')

    return data

def Data_sort(geom_data:pd.Series)->dict:
    """
    Sorts step raw data and creates appropriate geometry objects.
    Parameters
    ----------
    geom_data : pandas.Series, Geometry instance data in format {'id','tag','properties'}
    """
    #   Goes through geometry raw data & initialises geometry objects.
    geom_dict={}    #   format 
    for index,row in geom_data.iterrows():
        if row['tag']=='CARTESIAN_POINT':
            x=Cartesian_point(row)
        elif row['tag']=='VERTEX_POINT':
            x=Vertex_point(row)
        elif row['tag']=='DIRECTION':
            x=Direction(row)
        elif row['tag']=='VECTOR':
            x=Vector(row)
        elif row['tag']=='LINE':
            x=Line(row)
        elif row['tag']=='AXIS2_PLACEMENT_3D':
            x=Axis2_placement_3d(row)
        elif row['tag']=='PLANE':
            x=Plane(row)
        elif row['tag']=='CIRCLE':
            x=Circle(row)
        elif row['tag']=='TRIMMED_CURVE':
            x=Trimmed_curve(row)
        elif row['tag']=='POLYLINE':
            x=Polyline(raw_data=row)
        elif row['tag']=='B_SPLINE_CURVE_WITH_KNOTS':
            x=B_spline_curve_with_knots(row)
        elif row['tag']=='EDGE_CURVE':
            x=Edge_curve(row)
        elif row['tag']=='ORIENTED_EDGE':
            x=Oriented_edge(row)
        elif row['tag']=='EDGE_LOOP':
            x=Edge_loop(row)
        elif row['tag']=='FACE_BOUND':
            x=Face_bound(row,outer=False)
        elif row['tag']=='FACE_OUTER_BOUND':
            x=Face_bound(row,outer=True)
        elif row['tag']=='ADVANCED_FACE':
            x=Advanced_face(row)
        else:
            continue

        geom_dict[x.id]=x
    
    #   Now all geom_dictetry objects are defined, each object is completed by following ID links 
    #   and filing in data.
    for data_type in DATA_HIERARCHY:
        for obj in geom_dict.values():
            if type(obj).__name__==data_type.lower().capitalize():
                try:
                    obj.fill_data(geom_dict)
                except AttributeError:
                    pass

    return geom_dict

if __name__=="__main__":
    geom_raw=Step_read('square_donut2.stp',csv=True)
    geom_dict=Data_sort(geom_raw)

    Plot_geom(geom_dict,cartesian_points=True,polylines=True,circles=True)