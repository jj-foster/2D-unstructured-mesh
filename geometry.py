import pandas as pd
from matplotlib import pyplot as plt
import numpy as np
import re
from scipy.interpolate import BSpline

from plot_tools import Plot_geom

DATA_HIERARCHY=[
    'CARTESIAN_POINT',
    'DIRECTION',
    'AXIS2_PLACEMENT_3D',
    'CIRCLE',
    'TRIMMED_CURVE',
    'POLYLINE',
    'B_SPLINE_CURVE_WITH_KNOTS',
]

class Cartesian_point():
    def __init__(self,raw_data:pd.Series):
        properties=raw_data['properties']
        coords=properties[properties.find("(")+1:properties.find(")")].split(',')
        
        self.id     =   int(raw_data['id'][1:])
        self.name   =   properties.split(',')[0][1:-1]
        self.coords =   np.array([float(x) for x in coords])

        if self.name=="":
            self.name=None

        return None

class Direction():
    def __init__(self,raw_data:pd.Series):
        properties=raw_data['properties']
        vector =   properties[properties.find("(")+1:properties.find(")")].split(',')

        self.id     =   int(raw_data['id'][1:])
        self.name   =   properties.split(',')[0][1:-1]
        self.vector =   np.array([float(x) for x in vector])

        if self.name=="":
            self.name=None

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

class Polyline():
    """3D line connecting 2 cartesian points."""
    def __init__(self,raw_data:pd.Series):
        properties=raw_data['properties']
        points=properties[properties.find("(")+1:properties.find(")")].split(',')

        self.id             =   int(raw_data['id'][1:])
        self.name           =   properties.split(',')[0][1:-1]
        self.points_coord   =   None    #   in form [[x0,y0,z0],[x1,y1,z1]]

        self.points_id      =   [int(x[1:]) for x in points]

        if self.name=="":
            self.name=None

    def fill_data(self,geom_dict):
        self.points_coord   =   [geom_dict[self.points_id[0]].coords,
                                 geom_dict[self.points_id[1]].coords]
        
        return None

class Circle():
    def __init__(self,raw_data:pd.Series):
        properties=raw_data['properties'].split(',')

        self.id         =   int(raw_data['id'][1:])
        self.name       =   properties[0][1:-1]
        self.radius     =   float(properties[2])
        self.plane      =   None
        self.centre     =   None
        self.trimmed    =   False
        
        self.plane_id    =   int(properties[1][1:])

        if self.name=="":
            self.name=None

    def fill_data(self,geom_dict):
        axes_obj=geom_dict[self.plane_id]

        self.centre =   axes_obj.origin
        self.plane  =   [np.cross(axes_obj.axis,axes_obj.ref_vector),axes_obj.ref_vector]

        return None

class Trimmed_curve():
    """
    Overwites a circle. Trims from trim1 to trim2.
    """
    def __init__(self,raw_data:pd.Series):
        properties=raw_data['properties'].split(',')

        self.id         =   int(raw_data['id'][1:])
        self.name       =   properties[0][1:-1]
        self.basis      =   None
        self.trim1      =   None
        self.trim2      =   None

        self.basis_id   =   int(properties[1][1:])
        self.trim1_id   =   int(properties[2][2:])
        self.trim2_id   =   int(properties[4][2:])

        if self.name=="":
            self.name=None

    def fill_data(self,geom_dict):
        self.basis  =   geom_dict[self.basis_id] #   circle object
        self.trim1  =   geom_dict[self.trim1_id].coords
        self.trim2  =   geom_dict[self.trim2_id].coords

        geom_dict[self.basis_id].trimmed=True

        return None

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
        knot_values         =   [float(x) for x in properties[7][1:-1].split(',')]
        knot_vector         =   []
        
        #   multiply out knot values into knot vector according to multipicity values
        for i,_ in enumerate(knot_values):
            knot_vector.append([knot_values[i]]*knot_multipicities[i])
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
        
        data=data.append({'id':id,'tag':tag,'properties':properties},ignore_index=True)

    data.dropna(axis=0,inplace=True)    #   removes blank entries
    data=data[data['tag'].isin(DATA_HIERARCHY)]  #   removes entries that contain waffle data

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
            geom_dict[x.id]=x
        elif row['tag']=='DIRECTION':
            x=Direction(row)
            geom_dict[x.id]=x
        elif row['tag']=='AXIS2_PLACEMENT_3D':
            x=Axis2_placement_3d(row)
            geom_dict[x.id]=x
        elif row['tag']=='CIRCLE':
            x=Circle(row)
            geom_dict[x.id]=x
        elif row['tag']=='TRIMMED_CURVE':
            x=Trimmed_curve(row)
            geom_dict[x.id]=x
        elif row['tag']=='POLYLINE':
            x=Polyline(row)
            geom_dict[x.id]=x
        elif row['tag']=='B_SPLINE_CURVE_WITH_KNOTS':
            x=B_spline_curve_with_knots(row)
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
    geom_raw=Step_read('NACA0012H.step',csv=True)
    geom_dict=Data_sort(geom_raw)

    Plot_geom(geom_dict,cartesian_points=False,polylines=True,circles=True)