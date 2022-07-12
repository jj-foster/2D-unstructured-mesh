"""
Bounding nodes generated within respective class
Domain nodes generated here
Mesh generation handled here.
"""

import numpy as np
from matplotlib import pyplot as plt

from geometry import Step_read, Data_sort, Remove_duplicate_nodes
from plot_tools import Plot_nodes_3d,Plot_nodes_2d,Plot_geom,Plot_edges,Plot_panels

class StepException(Exception):
    pass

class Panel():
    def __init__(self,A,B,C,D=None):
        self.A=A
        self.B=B
        self.C=C
        self.D=D

        if D==None:
            self.points=np.array([A,B,C,A])
        else:
            self.points=np.array([A,B,C,D,A])

class Edge():
    def __init__(self,nodes,orientation:bool,axis):
        self.nodes=nodes
        self.orientation=orientation

        self.v1=axis.ref_vector
        self.v2=axis.axis

class Mesh():
    def __init__(self,file:str,spacing:float,edge_layers=1)->None:
        self.faces=self.Read(file)
        self.edges=self.Init_edges(spacing)

        self.nodes,self.panels=self.advancing_front(spacing,edge_layers)

        return None
        
    def Read(self,file:str)->list:
        geom_raw=Step_read(file,csv=True)
        geom_dict=Data_sort(geom_raw)

        #Plot_geom(geom_dict)
        
        faces=[x for x in geom_dict.values() if type(x).__name__=='Advanced_face']
        if faces==[]:
            raise StepException("No face defined in input file. Input model must contain a 2D face.")

        return faces

    def Init_edges(self,spacing:float)->list:
        edges=[]
        for face in self.faces:
            axis=face.plane.axis
            for bound in face.bounds:
                orientation=bound.orientation
                edge_loop=bound.edge_loop
                nodes=edge_loop.gen_nodes(spacing)

                edges.append(Edge(nodes,orientation,axis))

        return edges

    def advancing_front(self,spacing:float,layers:int):
        """
        Edge object defining edge nodes
            - update next iteration with each tri panel generation
            - with each loop new edge object is used

        DONE - node variable containing nodes from all edges
        loop through edges:
            DONE - identify optimal node placement
            DONE - check radius for other nodes
            DONE - create tri panel object
            FIX - 2nd edge wave
            FIX - first edge 0th element crossover
            add new edges to next edge object

        at end delete duplicate nodes and panels

        need to figure out creating new edges - some sort of loop check?
        """
        r=spacing*0.5

        edges=self.edges
        nodes=[node for edge in edges for node in edge.nodes]
        panels=[]
        
        i=0
        while i<1: 
            for edge in edges:
                edge_nodes=edge.nodes   #   nodes on current edge
                orientation=edge.orientation
                
                new_edge_nodes=[]
                for j in range(len(edge_nodes)-1):
                    ####    Identify optimal node placement     ####
                    A=edge_nodes[j]
                    B=edge_nodes[j+1]
                    AB=B-A
                    # Unit vectors in directrion between nodes & perpendicular
                    # i.e. for ideal isoseles triangle
                    x=AB/np.linalg.norm(AB)
                    y=np.cross(x,edge.v2)

                    if orientation==False:  #   Generate panels outside instead of inside:
                        y=-y

                    dx=spacing
                    dy=np.sqrt(dx**2-(dx/2)**2)
                    C=A+x*dx/2+y*dy

                    ####    Check radius for other nodes    ####
                    near_nodes={}
                    for node in nodes:
                        x=node[0]
                        y=node[1]
                        z=node[2]
                        x_p=C[0]
                        y_p=C[1]
                        z_p=C[2]

                        if x_p-r<=x<=x_p+r and y_p-r<=y<=y_p+r and z_p-r<=z<=z_p+r:
                            distance=np.linalg.norm(node-C)
                            near_nodes[distance]=node

                    if near_nodes!={}:  
                        C=near_nodes[min(near_nodes.keys())]    #   Selects closets node

                        #
                        AC_mod=np.linalg.norm(C-A)
                        BC_mod=np.linalg.norm(C-B)
                        if AC_mod>=BC_mod:
                            new_edge_nodes.append(A)
                            nodes.append(A)
                        else:
                            new_edge_nodes.append(B)
                            nodes.append(B) 
                    else:
                        new_edge_nodes.append(A)
                        nodes.append(A) 

                    new_edge_nodes.append(C)
                    nodes.append(C)

                    panels.append(Panel(A,C,B))
                #end for

                edge.nodes=np.array(new_edge_nodes)
                edge.nodes=Remove_duplicate_nodes(edge.nodes)
                edge.nodes=np.append(edge.nodes,[edge.nodes[0]],axis=0)    #   close edge loop

            #end for

            Plot_edges(edges,projection='2d',line=True)

            i+=1
        #end while

        nodes=np.array(nodes)

        return nodes, panels

if __name__=="__main__":
    #mesh=Mesh(file='NACA0012H.stp',spacing=30,edge_layers=1)
    mesh=Mesh(file='square_loop.stp',spacing=3,edge_layers=1)
    
    #Plot_nodes_2d(mesh.nodes,labels=True)
    #Plot_panels(mesh.panels)