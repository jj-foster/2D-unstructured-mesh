## TODO:
```
DONE 1. Fill trimmed_curve data
DONE 2. Change obj list to dict with ID as tag
DONE 3. Add parent/child relation to trimmed_curve & circle

DONE 4. Add line equations to geometry objects
DONE 5. Add B-splines

DONE 6. Move plotting to new file
DONE 7. Generate nodes on lines - within geom type class
DONE 8. generate nodes based on edge loops rather than geometry
9. edge nodes advancing front
    combine edge node lists

10. mesh smoothing
11. quad dominant mesh
12. fully quad mesh
```
## STEP Datastructure:
```
ADVANCED_FACE
    PLANE
    FACE_OUTER_BOUND+FACE_BOUND
        EDGE_LOOP
            ORIENTED EDGE
                EDGE_CURVE
                    VERTEX POINT
                    <geometry object>

geometry object:
    LINE
    POLYLINE
    CIRCLE
    BSPLINE
```
