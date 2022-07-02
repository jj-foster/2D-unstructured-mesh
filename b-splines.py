from matplotlib import pyplot as plt
from scipy.interpolate import BSpline
import numpy as np

def scipy_bspline(points,n,degree,closed=False):
    points=np.asarray(points)
    count=points.shape[0]

    if closed:
        knots=np.arange(-degree,count+degree+1)
        factor,fraction=divmod(count+degree+1,count)
        points=np.roll(np.concatenate((points,)*factor+(points[:fraction],)),-1,axis=0)
        degree=np.clip(degree,1,degree)

    else:
        degree=np.clip(degree,1,count-1)
        knots=np.clip(np.arange(count+degree+1)-degree,0,count-degree)

    max_param=count-(degree*(1-closed))
    spline=BSpline(knots,points,degree)

    return spline(np.linspace(0,max_param,n))

points = np.array([[0,0],
                   [5,2.5],
                   [8,10],
                   [-8,10],
                   [-5,2.5],
                   [0,0]
                   ])

#knots=np.array([1,1,1,1,1,2,3,3,3,3,3])
knots=np.array([0,0,0,0,0,1,2,2,2,2,2])

degree=4

#spline=scipy_bspline(points,1000,4,closed=False)
spline=BSpline(knots,points,degree)
fig=plt.figure()
ax=plt.axes()

x,y=spline(np.linspace(0,points.shape[0]-degree,100)).T
ax.plot(x,y,'k-')
ax.plot(points[:,0],points[:,1],'o-',label='Control Points')

ax.set_aspect('equal')
plt.show()