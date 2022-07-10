"""
Bounding nodes generated within respective class
Domain nodes generated here
Mesh generation handled here.
"""
import numpy as np

from geometry import Step_read, Data_sort
from plot_tools import Plot_nodes_3d,Plot_nodes_2d,Plot_geom

class Mesh():
    def __init__(self,file:str,spacing:float)->None:
        self.edges,domain=self.Read(file)

        self.edge_nodes=self.Edge_nodes(spacing)

        return None
        
    def Read(self,file:str)->list:
        domain=None
        geom_raw=Step_read(file,csv=True)
        geom_dict=Data_sort(geom_raw)

        Plot_geom(geom_dict)
        
        edges=[x for x in geom_dict.values() if hasattr(x,'plt_ignore')==False]
        
        return edges,domain

    def Edge_nodes(self,spacing:float)->np.ndarray:
        edge_nodes=np.array(self.edges[0].gen_nodes(spacing))
        for i,line in enumerate(self.edges):
            if i==0:
                continue
            edge_nodes=np.concatenate((edge_nodes,line.gen_nodes(spacing)),axis=0)
        
        # remove overlapping nodes
        edge_nodes_=[]
        for node in edge_nodes:
            if (list(node) in edge_nodes_)==False:
                edge_nodes_.append(list(node))

        edge_nodes_=np.array(edge_nodes_)

        return edge_nodes_

if __name__=="__main__":
    mesh=Mesh(file='square_donut2.stp',spacing=1)
    Plot_nodes_2d(mesh.edge_nodes)