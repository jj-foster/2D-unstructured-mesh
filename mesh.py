from os import system
import numpy as np
from matplotlib.animation import ArtistAnimation
import numba as nb

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

        self.vector=B-A
        self.length=np.linalg.norm(self.vector)
        # Unit vectors in directrion between nodes & perpendicular
        # i.e. for ideal isoseles triangle
        self.x=self.vector/self.length
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

        return np.array(nodes)

class Mesh():
    def __init__(self,spacing:float,front:Front,debug:bool=False)->None:
        self.front=front

        self.panels=self.advancing_front(spacing,debug)

        return None

    @staticmethod
    @nb.jit(nopython=True)
    def find_near_nodes(centre_node:np.ndarray,nodes:np.ndarray,r:float)->list:
        """
        Finds nodes in radius around centre node.

        Arguments:
            centre_node: {np.ndarray} -- Central node to search around.
            nodes: {np.ndarray} -- Array of nodes to search in.
            r: {float} -- Radius of search area.

        Returns:
            near_nodes: {np.ndarray} -- List of nodes within search area.
        """
        near_nodes=[]
        for node in nodes:
            distance=np.linalg.norm(node-centre_node)
            if distance<=r:
                near_nodes.append((node,distance))
        
        return near_nodes

    def find_connected_sides(self,node:np.array,sides:list)->list:
        """
        Finds sides in the front attached to a node.

        Arguments:
            node: {np.array} -- Node to find connected sides.
            sides: {list} -- List of sides to search from.
        
        Returns:
            near_sides: {list} -- List of sides connected to node.
        """
        near_sides=[]
        for side in sides:
            A=side.A
            B=side.B

            if list(A)==list(node) or list(B)==list(node):
                near_sides.append(side)
        
        return near_sides

    def filter_near_nodes(self,current_side:Front_side,near_nodes:list):
        """
        Finds most constraining left and right sides connected to the current side and works out if nodes are within these bounds,

        Attributes:
            current_side: {Front_side} -- Current side in the front to consider.
            near_nodes: {list} -- List of nodes to be put through the filter.

        Returns:
            near_nodes_filetered: {list} -- List of nodes within the bounds.
            L_constraint: {Front_side,float} -- Left constraining side and angle (side,angle).
            R_constraint: {Front_side,float} -- Right constraining side and angle (side,angle).
        """
        def check_side_direction(side:Front_side,node:np.ndarray)->tuple:
            """
            Calculates which side of a line a point is.

            Attributes:
                side: {Front_side} -- Dividing line to check which side the point is on.
                node: {np.ndarray} -- Point to work out which side of the line it is on.

            Returns:
                d_node: {float} -- Min. distance between node and line.
                d_side_in: {float} -- Used to compare sign with d_node. If both have the same sign, both are on the same side.
            """
            assert type(side)==Front_side
            assert type(node)==np.ndarray

            norm_side=side.y
            x_side_A,y_side_A,z_side_A=side.A.T
            x_side_B,y_side_B,z_side_B=side.B.T
            d_side_in=(x_side_A+1*norm_side[0]-x_side_A)*(y_side_B-y_side_A)-(y_side_A+1*norm_side[1]-y_side_A)*(x_side_B-x_side_A)

            x_node,y_node,z_node=node.T
            d_node=(x_node-x_side_A)*(y_side_B-y_side_A)-(y_node-y_side_A)*(x_side_B-x_side_A)

            return d_node,d_side_in
    
        adjacent_sides=[
            self.find_connected_sides(current_side.A,self.front.sides),
            self.find_connected_sides(current_side.B,self.front.sides)
        ]
        adjacent_sides=[_ for xs in adjacent_sides for _ in xs if _!=current_side]
        
        #   Remove adjacent sides with nodes below current side from consideration.
        adjacent_sides_in={}
        for adj_side in adjacent_sides:
            if list(adj_side.A)==list(current_side.A):
                connect="A"
                node=adj_side.A
            elif list(adj_side.A)==list(current_side.B):
                connect="B"
                node=adj_side.B
            elif list(adj_side.B)==list(current_side.A):
                connect="A"
                node=adj_side.A
            elif list(adj_side.B)==list(current_side.B):
                connect="B"
                node=adj_side.B

            d_node,d_current_in=check_side_direction(current_side,node)
            
            if d_node*d_current_in>0:   #   if above current side
                adjacent_sides_in[adj_side]=connect
        
        #   Calculates constraining sides & angels
        L_angle=0
        R_angle=0
        L_constraint=(None,0)
        R_constraint=(None,0)
        for adj_side,connect in adjacent_sides_in.items():
            angle=np.rad2deg(np.arccos(np.dot(adj_side.vector,current_side.vector)/(adj_side.length*current_side.length)))
            
            if connect=="A":
                if angle>L_angle:
                    L_angle=angle
                    L_constraint=(adj_side,angle)
            else:
                if angle>R_angle:
                    R_angle=angle
                    R_constraint=(adj_side,angle)
        
        #   Filter near nodes by constraints
        near_nodes_filtered=[]
        for node,dist in near_nodes:

            node2A=current_side.A-node
            B2node=node-current_side.B

            node2A_mod=np.linalg.norm(node2A)
            B2node_mod=np.linalg.norm(B2node)
            """warning happening because filter is called before cases identified. Not an issue, just slows it
            down a touch. Add something to stop it printing the warning"""
            angle_A=np.rad2deg(np.arccos(np.dot(node2A,current_side.vector)/(node2A_mod*current_side.length)))
            angle_B=np.rad2deg(np.arccos(np.dot(B2node,current_side.vector)/(B2node_mod*current_side.length)))
            
            if angle_A>=L_angle and angle_B>=R_angle:   #   if within angle constraints
                d_node,d_current_in=check_side_direction(current_side,node)

                if d_node*d_current_in>0:   #   if above current side
                    near_nodes_filtered.append((node,dist))

        return near_nodes_filtered,(L_constraint,R_constraint)

    def advancing_front(self,spacing:float,debug:bool):
        """
        Advancing front mesh generation algorithm. Currently does not use guide nodes.

        Arguments:
            spacing: {float} -- Target spacing between nodes.
            debug: {bool} -- Enable debug mode.

        Returns:
            panels: {list} -- List of generated tri panels.

        """
        panels=[]
        i=0
        while True:
            if self.front.sides==[]:
                break

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
            front_nodes=self.front.nodes
            near_nodes=self.find_near_nodes(
                centre_node=C_ideal,
                nodes=front_nodes,
                r=r,
            )
            near_nodes_=[]
            for node in near_nodes:
                if list(node)!=list(A) and list(node)!=list(B):
                    near_nodes_.append(node)
            
            near_nodes_filtered,(L_constraint,R_constraint)=self.filter_near_nodes(side,near_nodes_)

            #   Checks to determine type of close node:
            #       1a. No close nodes, generate point in ideal position.
            #       1b. No close nodes but ideal crosses constraint.
            #       2. Connect to a node with no adjascent sides.
            #       3. Connect to 1 adjascent side.
            #       4. Connect to 2 adjascent sides (close a triangle).
            if near_nodes_filtered==[]:
                node=C_ideal
                
                node2A=A-node
                B2node=node-B

                node2A_mod=np.linalg.norm(node2A)
                B2node_mod=np.linalg.norm(B2node)

                angle_A=np.rad2deg(np.arccos(np.dot(node2A,side.vector)/(node2A_mod*side.length)))
                angle_B=np.rad2deg(np.arccos(np.dot(B2node,side.vector)/(B2node_mod*side.length)))
                
                if angle_A>=L_constraint[1] and angle_B>=R_constraint[1]:   #   if within angle constraints
                    #   Case 1a:
                    C=C_ideal

                    new_sides=[
                        Front_side(C,B,orientation=side.orientation,vect_out_plane=side.vect_out_plane),
                        Front_side(A,C,orientation=side.orientation,vect_out_plane=side.vect_out_plane)
                    ]

                    #   update front and panels
                    self.front.update(add=new_sides,remove=[side])
                    panels.append(Panel(side.vect_out_plane,A,B,C))

                else:
                    #   Case 1b:
                    h=np.sqrt((dx/2)**2+(dy)**2)
                    
                    if angle_A<L_constraint[1]:
                        #crosses left constraint
                        theta=180-L_constraint[1]
                        dx_=h*np.cos(np.deg2rad(theta))
                        dy_=h*np.sin(np.deg2rad(theta))
                        C=A+dx_*x+dy_*y

                        remove=[L_constraint[0],side]
                        split=Front_side(L_constraint[0].A,
                            C,
                            orientation=L_constraint[0].orientation,
                            vect_out_plane=L_constraint[0].vect_out_plane
                        )

                        new_sides=[
                            Front_side(C,B,orientation=side.orientation,vect_out_plane=side.vect_out_plane),
                            split
                        ]
                    
                    elif angle_B<R_constraint[1]:
                        #crosses right constraint
                        theta=180-R_constraint[1]
                        dx_=dx-h*np.cos(np.deg2rad(theta))
                        dy_=h*np.sin(np.deg2rad(theta))
                        C=A+dx_*x+dy_*y

                        remove=[R_constraint[0],side]
                        split=Front_side(C,
                            R_constraint[0].B,
                            orientation=R_constraint[0].orientation,
                            vect_out_plane=R_constraint[0].vect_out_plane
                        )

                        new_sides=[
                            Front_side(A,C,orientation=side.orientation,vect_out_plane=side.vect_out_plane),
                            split
                        ]
                    
                    else:
                        print('wot')

                    #   update front and panels
                    self.front.update(add=new_sides,remove=remove)
                    panels.append(Panel(side.vect_out_plane,A,B,C))

            else:
                ####   Check if near nodes cross adjacent sides.    ####
                
                min_dist=1e99
                for node,dist in near_nodes_filtered:
                    if dist<min_dist:
                        min_dist=dist
                        nearest_node=node

                """
                ####    Checks if nearest node has sides connecting to current side    ####
                shared_nodes={}
                if L_constraint!=None:
                    shared_nodes[L_constraint]=B
                if R_constraint!=None:
                    shared_nodes[R_constraint]=A
                """
                #end for
                
                shared_nodes={}
                near_sides=self.find_connected_sides(nearest_node,self.front.sides)
                for near_side in near_sides:
                    if list(A) in (list(near_side.A),list(near_side.B)):
                        shared_nodes[near_side]=B
                    elif list(B) in (list(near_side.A),list(near_side.B)):
                        shared_nodes[near_side]=A
                
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
                if i>328:
                    if (i/1).is_integer()==True:
                        Plot_sides(self.front.sides)

            i+=1
        #end while

        return panels

        
def read(file:str)->list:
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

def init_front(faces:list,spacing:float)->list:
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


if __name__=="__main__":
    system('cls')

    faces=read('square_loop.stp')
    spacing=1

    front=init_front(faces,spacing=spacing)
    mesh=Mesh(front=front,spacing=spacing,debug=False)
    print('mesh done')
    
    Plot_panels(mesh.panels)