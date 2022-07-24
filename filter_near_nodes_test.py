import numpy as np
from matplotlib import pyplot as plt

from mesh import Mesh,Front,Front_side
from plot_tools import Plot_nodes_2d,Plot_panels, Plot_sides

vect_out_plane=np.array([0,0,1])

#   geometry
p1=np.array([0,0.5,0])
p2=np.array([0,0,0])
p3=np.array([0.5,0,0])
p4=np.array([0.5,0.5,0])

#px1=np.array([1,1,0])
#px2=np.array([-2,2,0])

P1=np.array([0.25,-0.05,0])

spacing=0.5

#   mesh setup
sides=[
    Front_side(p1,p2,orientation=False,vect_out_plane=vect_out_plane),
    Front_side(p2,p3,orientation=False,vect_out_plane=vect_out_plane),
    Front_side(p3,p4,orientation=False,vect_out_plane=vect_out_plane)
    #Front_side(px1,p2,orientation=False,vect_out_plane=vect_out_plane),
    #Front_side(p3,px2,orientation=False,vect_out_plane=vect_out_plane)
]

#   test
front=Front(sides)

mesh=Mesh(front=front,spacing=spacing)


current_side=sides[1]
x=current_side.x
y=current_side.y
dx=current_side.length
dy=np.sqrt(spacing**2-(spacing/2)**2)

A=current_side.A
B=current_side.B
c_ideal=A+x*dx/2+y*dy

nodes=np.append(front.nodes,np.array([P1]),axis=0)
near_nodes=mesh.find_near_nodes(c_ideal,nodes,r=spacing,exclude=(A,B))

print(mesh.filter_near_nodes(current_side,near_nodes))

#   plot
fig,ax=plt.subplots()
Plot_sides(sides,line=True,ax=ax)
Plot_nodes_2d(nodes,ax=ax)
plt.show()
