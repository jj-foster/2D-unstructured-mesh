import numpy as np

from mesh import Mesh, Front_side, Front
from plot_tools import Plot_nodes_2d,Plot_panels, Plot_sides

vect_out_plane=np.array([0,0,1])

"""
#   Case 1,2 test:

A=np.array([0,0,0])
B=np.array([1,0,0])
C=np.array([0.5,1.5,0])
D=np.array([0.5,3,0])

AB=B-A
CD=D-C

sides=[
    Front_side(A,B,orientation=False,vect_out_plane=vect_out_plane),
    Front_side(C,D,orientation=False,vect_out_plane=vect_out_plane)
]
"""
"""
#   Case 3,4 test:

A=np.array([0,0,0])
B=np.array([1,0,0])
C=np.array([0.3,1,0])

AB=B-A
BC=C-B
CA=A-C

sides=[
    Front_side(A,B,orientation=False,vect_out_plane=vect_out_plane),
    Front_side(B,C,orientation=False,vect_out_plane=vect_out_plane)
    #Front_side(C,A,orientation=False,vect_out_plane=vect_out_plane)
]
"""

# case 0 test:
A=np.array([1.2,0.3,0])
B=np.array([0,0,0])
C=np.array([1,0,0])
D=np.array([1.2,0.3,0])
E=np.array([0.5,0.6,0])
F=np.array([0.5,1.2,0])

sides=[
    Front_side(B,C,orientation=False,vect_out_plane=vect_out_plane),
    Front_side(A,B,orientation=False,vect_out_plane=vect_out_plane),
    Front_side(C,D,orientation=False,vect_out_plane=vect_out_plane),
    Front_side(E,F,orientation=False,vect_out_plane=vect_out_plane)
]

#Plot_sides(sides,projection='2d',line=True)

front=Front(sides)

mesh=Mesh(front=front,spacing=1,debug=True)
#Plot_panels(mesh.panels)
