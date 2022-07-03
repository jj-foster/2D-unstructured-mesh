"""
Bounding nodes generated within respective class
Domain nodes generated here
Mesh generation handled here.
"""
import numpy as np

from geometry import Step_read, Data_sort

class Mesh():
    def __init__(self,file:str,spacing:float)->None:
        self.bounding_lines,domain=self.read(file)

        self.line_nodes=self.Line_nodes(spacing)

        return None
        
    def read(self,file:str)->list:
        domain=None
        geom_raw=Step_read(file,csv=True)
        geom_dict=Data_sort(geom_raw)
        
        bounding_lines=[x for x in geom_dict.values() if x.bounding]
        
        return bounding_lines,domain

    def Line_nodes(self,spacing:float)->np.ndarray:
        line_nodes=[]
        for line in self.bounding_lines:
            line.gen_nodes(spacing)

        return line_nodes

if __name__=="__main__":
    mesh=Mesh(file='2D_arc.stp',spacing=0.2)