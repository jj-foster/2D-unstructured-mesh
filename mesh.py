"""
Bounding nodes generated within respective class
Domain nodes generated here
Mesh generation handled here.
"""

from os import system
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
        assert type(nodes)==np.ndarray, "nodes must of type <class 'numpy.ndarray'>"
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
        geom_raw=Step_read(file,csv=False)
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

    def find_near_nodes(self,centre_node:np.array,nodes:np.array,r:float,in_direction=None)->dict:
        near_nodes={}
        for node in nodes:
            x,y,z=node[0],node[1],node[2]
            x_p,y_p,z_p=centre_node[0],centre_node[1],centre_node[2]

            if x_p-r<=x<=x_p+r and y_p-r<=y<=y_p+r and z_p-r<=z<=z_p+r:
                distance=np.linalg.norm(node-centre_node)

                if distance!=0:

                    if type(in_direction)==np.ndarray:  #   only nodes in same direction as given vector
                        vector=node-centre_node

                        if np.dot(vector,in_direction)<0:
                            near_nodes[distance]=node
                    else:
                        near_nodes[distance]=node

        return near_nodes

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

        edges=self.edges
        nodes=[node for edge in edges for node in edge.nodes]
        panels=[]
        
        i=0
        while i<5: 
            ax=plt.axes()
            Plot_edges(edges,projection='2d',line=True,ax=ax)
            for edge in edges:

                front_nodes=edge.nodes   #   nodes on current edge
                orientation=edge.orientation
                
                new_front_nodes=[]
                for j in range(len(front_nodes)-1):
                    ####    Identify optimal node placement     ####
                    A=front_nodes[j]
                    B=front_nodes[j+1]
                    AB=B-A
                    # Unit vectors in directrion between nodes & perpendicular
                    # i.e. for ideal isoseles triangle
                    x=AB/np.linalg.norm(AB)
                    y=np.cross(x,edge.v2)

                    if orientation==False:  #   Generate panels outside instead of inside:
                        y=-y

                    dx=np.linalg.norm(AB)
                    dy=np.sqrt(spacing**2-(spacing/2)**2)
                    C=A+x*dx/2+y*dy

                    ####    Check radius for other nodes    ####
                    r=0.5*dx

                    near_A=self.find_near_nodes(A,front_nodes,r,in_direction=x)
                    near_B=self.find_near_nodes(B,front_nodes,r,in_direction=x)
                    near_nodes=dict(list(near_A.items())+list(near_B.items()))

                    if near_nodes=={}: 
                        r=0.5*spacing
                        near_nodes=self.find_near_nodes(C,front_nodes,r)
                    
                    if near_nodes!={}:  
                        C=near_nodes[min(near_nodes.keys())]    #   Selects closets node

                    ####    Adds nodes to front and global node list    ####
                    AC_mod=np.linalg.norm(C-A)
                    BC_mod=np.linalg.norm(C-B)
                    if AC_mod<BC_mod or np.isclose(AC_mod,BC_mod,rtol=1e-5):
                        if (list(A) in np.array(new_front_nodes).tolist())==False:
                            new_front_nodes.append(A)
                            nodes.append(A)
                        if (list(C) in np.array(new_front_nodes).tolist())==False:
                            new_front_nodes.append(C)
                            nodes.append(C)
                    else:
                        if (list(C) in np.array(new_front_nodes).tolist())==False:
                            new_front_nodes.append(C)
                            nodes.append(C)
                        if (list(B) in np.array(new_front_nodes).tolist())==False:
                            new_front_nodes.append(B)
                            nodes.append(B) 

                    panels.append(Panel(A,C,B))
                #end for

                edge.nodes=np.array(new_front_nodes)
                #edge.nodes=Remove_duplicate_nodes(edge.nodes)
                edge.nodes=np.append(edge.nodes,[edge.nodes[0]],axis=0)    #   close edge loop

            #end for

            Plot_edges(edges,projection='2d',line=True,ax=ax)
            plt.show()
            i+=1
        #end while

        nodes=np.array(nodes)

        return nodes, panels

if __name__=="__main__":
    system('cls')
    #mesh=Mesh(file='NACA0012H.stp',spacing=30,edge_layers=1)
    mesh=Mesh(file='square_loop.stp',spacing=4,edge_layers=1)
    
    Plot_panels(mesh.panels)