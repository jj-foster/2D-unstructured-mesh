import pandas as pd
from matplotlib import pyplot as plt
import numpy as np

from plot_tools import Plot_cartesian_points, Plot_circles, Plot_polylines

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
        self.origin=geom_dict[self.origin_id].coords
        self.axis=geom_dict[self.axis_id].vector
        self.ref_vector=geom_dict[self.ref_vector_id].vector

        return None

class Polyline():
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
        self.points_coord=[geom_dict[self.points_id[0]].coords,
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

        self.centre=axes_obj.origin
        self.plane=[np.cross(axes_obj.axis,axes_obj.ref_vector),axes_obj.ref_vector]

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
        self.basis=geom_dict[self.basis_id] #   circle object
        self.trim1=geom_dict[self.trim1_id].coords
        self.trim2=geom_dict[self.trim2_id].coords

        geom_dict[self.basis_id].trimmed=True

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
            continue
    
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
    geom_raw=Step_read('spline_interpolation_loop.stp',csv=True)
    geom_dict=Data_sort(geom_raw)
    
    points  =[x for x in geom_dict.values() if type(x)==Cartesian_point]
    lines   =[x for x in geom_dict.values() if type(x)==Polyline]
    circles =[x for x in geom_dict.values() if type(x)==Circle]
    
    fig=plt.figure()
    ax=plt.axes(projection='3d')

    points_plt=Plot_cartesian_points(points,ax)
    line_plt=Plot_polylines(lines,ax)
    circle_plt=Plot_circles(circles,ax)

    plt.tight_layout()
    plt.show()
    