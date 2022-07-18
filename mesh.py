"""
Bounding nodes generated within respective class
Domain nodes generated here
Mesh generation handled here.
"""

from os import system
import numpy as np
from matplotlib import pyplot as plt

from geometry import Step_read, Data_sort, Remove_duplicate_nodes
from plot_tools import Plot_nodes_3d,Plot_nodes_2d,Plot_geom,Plot_sides,Plot_panels

class StepException(Exception):
    pass

class Panel():
    """
    Mesh panel object. Currently consists only of corner points.

    Parameters:
    ----------
    A,B,C,D : np.ndarray; Corner coordinates
    """
    def __init__(self,A,B,C,D=None):
        self.A=A
        self.B=B
        self.C=C
        self.D=D

        if D==None:
            self.points=np.array([A,B,C,A])
        else:
            self.points=np.array([A,B,C,D,A])

class Front_side():
    """
    Tri panel side within the advancing front. Is defined by 2 coordinates and orientation (for generating
    new points in the right direction.

    Parameters:
    -----------
    A, B : np.ndarray; Beginning and end coordinates.
    orientation: bool; Determines which direction new nodes are generated.
    axis: geometry.Axis2_placement_3d; Axis object defining plane on which side lies. Used for calculating local definition along side.
    """
    def __init__(self,A:np.ndarray,B:np.ndarray,orientation:bool,axis):
        self.A=A
        self.B=B
        self.orientation=orientation

        v1=axis.ref_vector
        v2=axis.axis

        self.AB=B-A
        self.length=np.linalg.norm(self.AB)
        # Unit vectors in directrion between nodes & perpendicular
        # i.e. for ideal isoseles triangle
        self.x=self.AB/self.length
        self.y=np.cross(self.x,v2)

        if orientation==False:  #   Generate panels outside instead of inside:
            self.y=-self.y

        return None

class Front():
    def __init__(self,sides:list):
        """Dynamic front object composed of individual tri panel sides."""
        self.sides=sides

        return None
    
    def __call__(self,index:int)->Front_side:
        return self.sides[index]

    def update(self,remove:list[Front_side],add:list[Front_side])->None:
        """
        Updates front by removing and adding tri panel sides.

        Parameters:
        ----------
        remove_sides, add_sides: list[Front_side]; Side objects to add and remove to the front.

        Returns:
        --------
        None - Front is updated inplace. 
        """
        self.sides=[side for side in self.sides if side not in remove]    #   Remove inactive sides
        self.sides.extend(add)    #   Add new active sides

        return None

class Mesh():
    def __init__(self,file:str,spacing:float)->None:
        faces=self.Read(file)
        self.front=self.Init_front(faces,spacing)

        self.nodes,self.panels=self.advancing_front(spacing)

        return None
        
    def Read(self,file:str)->list:
        """
        Reads STEP file and gets geometry faces (or surface) on which to generate mesh.

        Parameters:
        ----------
        file: str; Input step file.

        Returns:
        --------
        faces: list[gometry.Advanced_face]; List of face objects to generate mesh on.
        """
        geom_raw=Step_read(file,csv=False)
        geom_dict=Data_sort(geom_raw)

        #Plot_geom(geom_dict)
        
        faces=[x for x in geom_dict.values() if type(x).__name__=='Advanced_face']
        if faces==[]:
            raise StepException("No face defined in input file. Input model must contain a 2D face.")

        return faces

    def Init_front(self,faces:list,spacing:float)->list:
        """
        Initialises advancing front with surface boundaries.

        Parameters:
        -----------
        faces: list[geometry.Advanced_faces]; Face (or surface) objects on which to generate mesh.
        spacing: float; Node spacing for mesh generation. Smaller -> more refined mesh.

        Returns:
        -------
        front: Front; Front object containing sides on boundaries of geometry.
        """
        sides=[]
        for face in faces:
            axis=face.plane.axis
            for bound in face.bounds:
                orientation=bound.orientation
                edge_loop=bound.edge_loop
                nodes=edge_loop.gen_nodes(spacing)

                for i in range(len(nodes)-1):
                    sides.append(Front_side(nodes[i],nodes[i+1],orientation,axis))

        front=Front(sides)

        return front

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

    def advancing_front(self,spacing:float):

        Plot_sides(self.front.sides,projection='2d',labels=False,line=True)
        nodes=[]
        for side in self.front.sides:
            nodes.extend([side.A,side.B])

        panels=[]
        
        i=0
        while i<5:
            side=self.front(0)

            x=side.x
            y=side.y
            dx=side.length
            dy=np.sqrt(spacing**2-(spacing/2)**2)

            A=side.A
            B=side.B
            C_ideal=A+x*dx/2+y*dy

            """
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
            """

            i+=1

        #end while

        nodes=np.array(nodes)

        return nodes, panels

if __name__=="__main__":
    system('cls')
    #mesh=Mesh(file='NACA0012H.stp',spacing=30,edge_layers=1)
    mesh=Mesh(file='circle.stp',spacing=4)
    
    #Plot_panels(mesh.panels)