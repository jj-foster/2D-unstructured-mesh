"""
Bounding nodes generated within respective class
Domain nodes generated here
Mesh generation handled here.
"""

from multiprocessing.sharedctypes import Value
from os import system
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.animation import ArtistAnimation

from geometry import Step_read, Data_sort, Remove_duplicate_nodes
from plot_tools import Plot_nodes_3d,Plot_nodes_2d,Plot_geom,Plot_sides,Plot_panels

import cProfile,pstats,io
profiler=cProfile.Profile()

class StepException(Exception):
    pass

class Panel():
    """
    Mesh panel object. Currently consists only of corner points.

    Parameters:
    ----------
    A,B,C,D : np.ndarray; Corner coordinates
    """
    def __init__(self,normal:np.array,A:np.array,B:np.array,C:np.array,D:np.array=None):
        self.norma=normal

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
    def __init__(self,A:np.ndarray,B:np.ndarray,orientation:bool,vect_out_plane:np.array):
        self.A=A
        self.B=B
        self.orientation=orientation
        self.vect_out_plane=vect_out_plane

        self.AB=B-A
        self.length=np.linalg.norm(self.AB)
        # Unit vectors in directrion between nodes & perpendicular
        # i.e. for ideal isoseles triangle
        self.x=self.AB/self.length
        self.y=np.cross(self.x,self.vect_out_plane)

        if orientation==False:  #   Generate panels outside instead of inside:
            self.y=-self.y

        return None

class Front():
    def __init__(self,sides:list):
        """Dynamic front object composed of individual tri panel sides."""
        self.sides=sides

        self.nodes=self.get_nodes()

        return None
    
    def __call__(self,index:int)->Front_side:
        return self.sides[index]

    def update(self,add:list,remove:list)->None:
        """
        Updates front by removing and adding tri panel sides.

        Parameters:
        ----------
        add, remove: list[Front_side]; Side objects to add and remove to the front.

        Returns:
        --------
        None - Front is updated inplace. 
        """
        try:
            self.sides=[side for side in self.sides if side not in remove]    #   Remove inactive sides
        except TypeError as e:
            print(e)
            print(self.sides,remove)
            exit()

        self.sides.extend(add)    #   Add new active sides

        self.nodes=self.get_nodes() #   refresh node list

        return None

    def get_nodes(self):
        nodes=[]
        for side in self.sides:
            A=side.A
            B=side.B

            nodes.extend([A,B])

        return nodes

class Mesh():
    def __init__(self,spacing:float,file:str=None,front:Front=None,debug:bool=False)->None:
        if file==None and front==None:
            raise TypeError("Mesh is missing 1 required positional argument: 'file' or 'front'")

        if type(front)!=Front:
            faces=self.Read(file)
            self.front=self.Init_front(faces,spacing)
        else:
            self.front=front

        self.panels=self.advancing_front(spacing,debug)

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
            vect_out_plane=face.plane.axis.axis
            for bound in face.bounds:
                orientation=bound.orientation
                edge_loop=bound.edge_loop
                nodes=edge_loop.gen_nodes(spacing)

                for i in range(len(nodes)-1):
                    sides.append(Front_side(nodes[i],nodes[i+1],orientation,vect_out_plane))

        front=Front(sides)

        return front

    def find_near_nodes(self,centre_node:np.array,nodes:np.array,r:float,in_direction=None,exclude=None)->dict:
        near_nodes={}
        for node in nodes:
            #x,y,z=node[0],node[1],node[2]
            #x_p,y_p,z_p=centre_node[0],centre_node[1],centre_node[2]

            if type(exclude)!=None:
                exclude_=(list(x) for x in exclude)
                if list(node) in exclude_:
                    continue
            
            distance=np.linalg.norm(node-centre_node)
            if distance<=r:
                """ DOESN'T WORK
                if type(in_direction)==np.ndarray:  #   only nodes in same direction as given vector
                    vector=node-centre_node
                    #print(np.rad2deg(np.dot(vector,in_direction)))
                    if np.dot(vector,in_direction)>0:
                        near_nodes[distance]=node
                else:
                """
                near_nodes[distance]=node

        return near_nodes

    def find_near_sides(self,node:np.array,sides:list)->list:
        near_sides=[]
        for side in sides:
            A=side.A
            B=side.B

            if list(A)==list(node) or list(B)==list(node):
                near_sides.append(side)
        
        return near_sides

    def advancing_front(self,spacing:float,debug:bool):
        #lines=[]    #   for animation
        #fig,ax=plt.subplots()

        panels=[]
        i=0
        while i<100:
            if self.front.sides==[]:
                break
            
            #fig,ax=plt.subplots()
            #Plot_sides(self.front.sides,projection='2d',labels=False,line=True,ax=ax)

            #lines.append(Plot_sides(self.front.sides,projection='2d',labels=False,line=True,ax=ax))
            
            side=self.front(0)

            #   Find ideal node position.
            x=side.x
            y=side.y
            dx=side.length
            dy=np.sqrt(spacing**2-(spacing/2)**2)

            A=side.A
            B=side.B
            C_ideal=A+x*dx/2+y*dy

            r=1*spacing   #   needs a proper method
            near_nodes=self.find_near_nodes(
                centre_node=C_ideal,
                nodes=self.front.nodes,
                r=r,
                in_direction=y,
                exclude=(A,B)
            )
            
            #   Checks to determine type of close node:
            #       1. No close nodes, generate point in ideal position.
            #       2. Connect to a node with no adjascent sides.
            #       3. Connect to 1 adjascent side.
            #       4. Connect to 2 adjascent sides (close a triangle).
            if near_nodes=={}:
                #   Case 1:
                C=C_ideal

                new_sides=[
                    Front_side(C,B,orientation=side.orientation,vect_out_plane=side.vect_out_plane),
                    Front_side(A,C,orientation=side.orientation,vect_out_plane=side.vect_out_plane)
                ]

                #   update front and panels
                self.front.update(add=new_sides,remove=[side])
                panels.append(Panel(side.vect_out_plane,A,B,C))

            else:
                ####   Check if near nodes cross adjacent sides.    ####

                adjacent_sides=[
                    self.find_near_sides(side.A,self.front.sides),
                    self.find_near_sides(side.B,self.front.sides)
                ]
                adjacent_sides=[_ for xs in adjacent_sides for _ in xs if _!=side]

                side_L=adjacent_sides[0]
                side_R=adjacent_sides[1]

                norm_L=side_L.y
                norm_R=side_R.y
                norm_C=y
                
                near_nodes_filtered={}
                for dist,node in near_nodes.items():
                    x_node,y_node,z_node=node.T

                    x_CA,y_CA,z_CA=side.A.T
                    x_LA,y_LA,z_LA=side_L.A.T
                    x_RA,y_RA,z_RA=side_R.A.T

                    x_CB,y_CB,z_CB=side.B.T
                    x_LB,y_LB,z_LB=side_L.B.T
                    x_RB,y_RB,z_RB=side_R.B.T
                    
                    # Finds min distance to side line. <=0 if inside
                    d_L_node=(x_node-x_LA)*(y_LB-y_LA)-(y_node-y_LA)*(x_LB-x_LA)
                    d_C_node=(x_node-x_CA)*(y_CB-y_CA)-(y_node-y_CA)*(x_CB-x_CA)
                    d_R_node=(x_node-x_RA)*(y_RB-y_RA)-(y_node-y_RA)*(x_RB-x_RA)

                    """Add check to work out which way is in vs out"""
                    d_L_in=(x_LA+1*norm_L[0]-x_LA)*(y_LB-y_LA)-(y_LA+1*norm_L[1]-y_LA)*(x_LB-x_LA)
                    d_C_in=(x_CA+1*norm_C[0]-x_CA)*(y_CB-y_CA)-(y_CA+1*norm_C[1]-y_CA)*(x_CB-x_CA)
                    d_R_in=(x_RA+1*norm_R[0]-x_RA)*(y_RB-y_RA)-(y_RA+1*norm_R[1]-y_RA)*(x_RB-x_RA)
        
                    if d_L_node>0 or d_R_node>0 or d_C_node>0:
                        print(d_L_node)
                        print(d_L_in)
                        continue
                    else:
                        near_nodes_filtered[dist]=node
                #print(near_nodes_filtered)
                try:
                    nearest_node=near_nodes_filtered[min(near_nodes_filtered.keys())]
                except ValueError:
                    print(i)
                    fig,ax=plt.subplots()
                    Plot_sides((side_L,side,side_R),projection='2d',line=True,ax=ax)
                    Plot_nodes_2d(np.array(list(near_nodes.values())),line=False,ax=ax)
                    plt.show()

                ####    Checks if nearest node has sides connecting to current side    ####
                shared_nodes={}
                if list(side_L.A)==list(nearest_node) or list(side_L.B)==list(nearest_node):
                    shared_nodes[side_L]=B
                if list(side_R.A)==list(nearest_node) or list(side_R.B)==list(nearest_node):
                    shared_nodes[side_R]=A

                #end for

                """
                near_sides=self.find_near_sides(nearest_node,self.front.sides)
                for near_side in near_sides:
                    if list(A) in (list(near_side.A),list(near_side.B)):
                        shared_nodes[near_side]=B
                    elif list(B) in (list(near_side.A),list(near_side.B)):
                        shared_nodes[near_side]=A
                """
                ####    Checks cases 2,3,4    ####

                C=nearest_node
                if len(shared_nodes.items())==0:
                    ##   Case 2:
                    new_sides=[
                        Front_side(C,B,orientation=side.orientation,vect_out_plane=side.vect_out_plane),
                        Front_side(A,C,orientation=side.orientation,vect_out_plane=side.vect_out_plane)
                    ]

                    #   update front and panels
                    self.front.update(add=new_sides,remove=[side])
                    panels.append(Panel(side.vect_out_plane,A,B,C))

                elif len(shared_nodes.items())==1:
                    ##   Case 3:
                    side_node=list(shared_nodes.values())[0]
                    if list(side_node)==list(A):
                        new_sides=[
                            Front_side(
                                side_node,C,orientation=side.orientation,vect_out_plane=side.vect_out_plane
                            )
                        ]
                    elif list(side_node)==list(B):
                        new_sides=[
                            Front_side(
                                C,side_node,orientation=side.orientation,vect_out_plane=side.vect_out_plane
                            )
                        ]

                    self.front.update(add=new_sides,remove=[side,list(shared_nodes.keys())[0]])
                    panels.append(Panel(side.vect_out_plane,A,B,C))

                elif len(shared_nodes.items())==2:
                    ##   Case 4:
                    side1,side2=list(shared_nodes.keys())

                    self.front.update(add=(),remove=[side,side1,side2])
                    panels.append(Panel(side.vect_out_plane,A,B,C))
            
            if debug==True:
                if i>64:
                    if (i/1).is_integer()==True:
                        Plot_sides(self.front.sides,projection='2d',labels=False,line=True)
                plt.show()

            i+=1
        #end while

        
        #ani=ArtistAnimation(fig,lines,interval=100,blit=True,repeat_delay=1000)
        #ani.save('square_donut.mp4')
        #plt.show()
        
        return panels

if __name__=="__main__":
    system('cls')
    #mesh=Mesh(file='NACA0012H.stp',spacing=30,edge_layers=1)
    mesh=Mesh(file='square_loop.stp',spacing=5,debug=True)
    print('mesh done')
    
    Plot_panels(mesh.panels)