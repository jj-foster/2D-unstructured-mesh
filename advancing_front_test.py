import numpy as np
from os import system

from mesh import Mesh, Front_side, Front
from plot_tools import Plot_nodes_2d,Plot_panels, Plot_sides

vect_out_plane=np.array([0,0,1])

"""
#   Case 0 test:

#A=np.array([1.2,0.3,0])
A=np.array([-1,0.5,0])
B=np.array([0,0,0])
C=np.array([1,0,0])
D=np.array([0.5,0.3,0])
E=np.array([0.5,0.6,0])
F=np.array([0.5,1.2,0])
G=np.array([0.5,0.1,0])
H=np.array([1,1,0])

sides=[
    Front_side(B,C,orientation=False,vect_out_plane=vect_out_plane),
    Front_side(A,B,orientation=False,vect_out_plane=vect_out_plane),
    Front_side(C,D,orientation=False,vect_out_plane=vect_out_plane),
    Front_side(E,F,orientation=False,vect_out_plane=vect_out_plane),
    Front_side(G,H,orientation=False,vect_out_plane=vect_out_plane)
]
"""
"""
#   Case 1a,2 test:

A=np.array([0,0,0])
B=np.array([1,0,0])
C=np.array([0.5,2,0])
D=np.array([0.5,3,0])

sides=[
    Front_side(A,B,orientation=False,vect_out_plane=vect_out_plane),
    Front_side(C,D,orientation=False,vect_out_plane=vect_out_plane)
]
"""

# Case 1b test:
A=np.array([0,0,0])
B=np.array([1,0,0])
C=np.array([2,2,0])

sides=[
    Front_side(A,B,orientation=False,vect_out_plane=vect_out_plane),
    Front_side(C,A,orientation=False,vect_out_plane=vect_out_plane)
]

"""
#   Case 3,4 test:

A=np.array([0,0,0])
B=np.array([1,0,0])
C=np.array([0.3,1,0])

sides=[
    Front_side(A,B,orientation=False,vect_out_plane=vect_out_plane),
    Front_side(B,C,orientation=False,vect_out_plane=vect_out_plane),
    Front_side(C,A,orientation=False,vect_out_plane=vect_out_plane)
]
"""
system('cls')

#Plot_sides(sides)

front=Front(sides)

mesh=Mesh(front=front,spacing=1,debug=True)
#Plot_panels(panels)
