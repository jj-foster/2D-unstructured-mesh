"""
Bounding nodes generated within respective class
Domain nodes generated here
Mesh generation handled here.
"""
from click import FileError
import numpy as np
from os import system
from matplotlib import pyplot as plt

from geometry import Step_read, Data_sort
from plot_tools import Plot_nodes_3d,Plot_nodes_2d,Plot_geom,Plot_edges

class Step_exception(Exception):
    pass

class Panel():
    def __init__(self):
        pass

class Edge():
    def __init__(self,edge_loop,spacing:float,orientation:bool,axis):
        self.nodes=edge_loop.gen_nodes(spacing)
        self.orientation=orientation

        self.v1=axis.ref_vector
        self.v2=axis.axis

class Mesh():
    def __init__(self,file:str,spacing:float,edge_layers=1)->None:
        self.faces=self.Read(file)
        self.edges=self.Edges(spacing)

        self.nodes=self.Advancing_front(spacing,edge_layers)

        return None
        
    def Read(self,file:str)->list:
        geom_raw=Step_read(file,csv=True)
        geom_dict=Data_sort(geom_raw)

        #Plot_geom(geom_dict)
        
        faces=[x for x in geom_dict.values() if type(x).__name__=='Advanced_face']
        if faces==[]:
            raise Step_exception("No face defined in input file. Input model must contain a 2D face.")

        return faces

    def Edges(self,spacing:float)->np.ndarray:
        edges=[]
        for face in self.faces:
            axis=face.plane.axis
            for bound in face.bounds:
                orientation=bound.orientation
                edge_loop=bound.edge_loop
                
                edges.append(Edge(edge_loop,spacing,orientation,axis))

        return edges

    def Advancing_front(self,spacing:float,layers:int):
        r=spacing*0.75

        for edge in self.edges:
            nodes=edge.nodes
            nodes_=nodes
            orientation=edge.orientation

            i=0
            while i<len(nodes)-1:
                A=nodes[i]
                B=nodes[i+1]
                AB=B-A
                x=AB/np.linalg.norm(AB)
                y=np.cross(x,edge.v2)
                if orientation==False:   #   generate panels outside instead of inside
                    y=-y

                dx=spacing
                dy=np.sqrt(dx**2-(dx/2)**2)
                C=A+x*dx/2+y*dy

                nodes_=np.append(nodes_,[C],axis=0)

                i+=1
            
            edge.nodes=nodes_

        return nodes_

if __name__=="__main__":
    mesh=Mesh(file='NACA0012H.stp',spacing=30,edge_layers=1)
    #mesh=Mesh(file='square_donut.stp',spacing=4,edge_layers=1)
    
    Plot_edges(mesh.edges,projection='2d',label=True)