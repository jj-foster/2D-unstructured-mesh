"""
Bounding nodes generated within respective class
Domain nodes generated here
Mesh generation handled here.
"""
import numpy as np

from geometry import Step_read, Data_sort
from plot_tools import Plot_nodes_3d,Plot_nodes_2d

class Mesh():
    def __init__(self,file:str,spacing:float)->None:
        self.bounding_lines,domain=self.read(file)

        self.line_nodes=self.Line_nodes(spacing)

        return None
        
    def read(self,file:str)->list:
        domain=None
        geom_raw=Step_read(file,csv=False)
        geom_dict=Data_sort(geom_raw)
        
        bounding_lines=[x for x in geom_dict.values() if x.bounding]
        
        return bounding_lines,domain

    def Line_nodes(self,spacing:float)->np.ndarray:
        line_nodes=np.array(self.bounding_lines[0].gen_nodes(spacing))
        for i,line in enumerate(self.bounding_lines):
            if i==0:
                continue
            line_nodes=np.concatenate((line_nodes,line.gen_nodes(spacing)),axis=0)

        return line_nodes

if __name__=="__main__":
    mesh=Mesh(file='spline_interpolation2.stp',spacing=1)
    Plot_nodes_2d(mesh.line_nodes)