import numpy as np
import design
from __future__ import division
# reload(design)
import time

import scipy.sparse as sps
import scipy.sparse.linalg as spsl
import matplotlib as mpl
import matplotlib.pyplot as plt


tapsfile = "/Users/Joke/Documents/Onderzoek/ProjectsOngoing/Neuropower/neuropower-web/neuropower/media/taps.p"


des = design.GeneticAlgorithm(
    # design specific
    ITI = [10,10,10],
    TR = 1,
    L = 242,
    P = [1/2,1/2],
    stim_duration = 20,
    C = np.array([[1,0],[0,1],[1,-1]]),
    restnum =0,
    restlength=0,
    weights = [0.1,0.4,0.25,0.25],
    ConfoundOrder = 3,
    MaxRepeat = 20,
    # general/defaulted
    rho = 0.3,
    Aoptimality = True,
    saturation = True,
    resolution = 0.125,
    G = 20,
    q = 0.01,
    I = 4,
    cycles = 1000,
    preruncycles = 0,
    HardProb = None,
    tapsfile = tapsfile,
    gui_sid=None
)


Design={"order":np.array([2,1,1,2,1,1,1,2,2,2,1,1,1,1,2,1,2,1,1,2,2,2,1,2,1,1,2,2,1,2,1,2,2,1,1,2,2,2,1,2,1,2,1,1,2,2,2,2,2,2,1,1,2,1,2,1,2,2,2,2,1,1,1,1,2,1,1,2,1,1,2,1,1,2,2,2,2,2,2,2,2,1,2,2,1,2,2,2,1,1,1,2,2,2,2,1,2,1,2,2,1,1,1,2,1,2,2,1,1,2,1,2,1,1,2,2,1,1,1,2,1,2,1,2,2,1,1,1,1,1,1,2,2,1,2,1,2,1,1,1,1,2,2,2,2,1,2,2,1,2,2,1,2,2,1,1,1,1,1,1,1,1,2,1,1,1,2,2,2,2,1,2,1,2,2,1,1,1,2,1,2,2,1,1,2,1,2,1,1,2,2,1,1,1,2,1,2,1,2,2,1,1,1,1,1,1,2,2,1,2,1,2,1,1,1,1,2,2,2,2,1,2,2,1,2,2,1,2,2,1,1,1,1,1,1,1,1,2,2,2,2,2])-1}
Design['ITIs']=[10]*242
Design = des.CreateDesignMatrix(Design)


XconvEV = Design['Xconv'][:,0]
X_EV = Design['Xnonconv'][:,0]

plt.plot(Design['Xconv'][:,0],color="red")
plt.plot(Design['Xnonconv'][:,0],color="grey")
plt.plot(XconvEV,color="blue")
plt.ylim([-1,2.5])
plt.xlim([0,700])
plt.show()




start_time = time.time()
a=scipy.linalg.solve(Design['X'],np.identity(Design['X'].shape[0],dtype=Design['X'].dtype))
atime = time.time()-start_time

start_time = time.time()
b=scipy.linalg.inv(Design['X'])
btime = time.time()-start_time

start_time = time.time()
c=scipy.linalg.pinv(Design['X'])
ctime = time.time()-start_time

start_time = time.time()
d1 = sps.coo_matrix(Design['X'])
d=spsl.inv(d1)
dtime = time.time()-start_time

start_time = time.time()
d1 = sps.coo_matrix(Design['X'])
d=spsl.inv(d1)
dtime = time.time()-start_time


print("--- solve: %s seconds ---" % (atime))
print("--- inv: %s seconds ---" % (btime))
print("--- pinv: %s seconds ---" % (ctime))
print("--- splu: %s seconds ---" % (dtime))
print("--- map: %s seconds ---" % (etime))

from numpy.linalg.lapack import lapack_lite
lapack_routine = lapack_lite.dgesv

def faster_inverse(A):
    b = np.identity(A.shape[2], dtype=A.dtype)
    n_eq = A.shape[1]
    n_rhs = A.shape[2]
    pivots = zeros(n_eq, np.intc)
    identity  = np.eye(n_eq)
    def lapack_inverse(a):
        b = np.copy(identity)
        pivots = zeros(n_eq, np.intc)
        results = lapack_lite.dgesv(n_eq, n_rhs, a, n_eq, pivots, b, n_eq, 0)
        if results['info'] > 0:
            raise LinAlgError('Singular matrix')
        return b





    return array([lapack_inverse(a) for a in A])




Generation = des.GeneticAlgorithmCreateEmptyGeneration()
des.GeneticAlgorithmCreateOrder()
weights = [0,0,1.]
weights = [int(x) for x in np.array(weights)*des.G]
Generation = des.GeneticAlgorithmAddOrder(Generation,weights)

# make babies and check constraints

Generation = des.GeneticAlgorithmGeneration(Generation)


len(Generation['order'])


for newbies in xrange(len(Children['order'])):
    newDesign = {'order':Generation['order'][newbies],'ITIs':Generation['ITIs'][newbies]}
    newDesign = self.CreateDesignMatrix(newDesign)
    newDesign = self.ComputeEfficiency(newDesign)
    Generation['']


        NextGeneration = Generation
        NextGeneration = self.GeneticAlgorithmAddDestoGen(NextGeneration,baby1)
        NextGeneration = self.GeneticAlgorithmAddDestoGen(NextGeneration,baby2)



d4 = dict(d1)
d4.update(d2)
d4.update(d3)


#
# Design = {"order":np.array([1,2,1,2,1,2,2,2,2,2,1,1,1,1,1,2,2,2,2,2])-1}
# Design['ITIs'] = [des.mnITI]*des.n_trials
# Design = des.CreateDesignMatrix(Design)
#
import matplotlib as mpl
import matplotlib.pyplot as plt

durres = Design['Xconv'][:,0]

plt.plot(Design['Xconv'][:,0])
plt.ylim([-1,2.5])
plt.xlim([0,700])
plt.show()
#
# plt.plot(Design['Xconv'])
# plt.show()
#
# plt.plot(des.basishrf)
# plt.show()
#
#
# axs[0].set_ylim([0,3])
# axs[0].plot(xn_p,null_p,color=twocol[3],lw=2,label="null distribution")
# axs[0].plot(xn_p,alt_p,color=twocol[5],lw=2,label="alternative distribution")
# axs[0].legend(loc="upper right",frameon=False)
# axs[0].set_title("Distribution of "+str(len(peaks))+" peak p-values \n $\pi_1$ = "+str(round(float(mixdata.pi1),2)))
# axs[0].set_xlabel("Peak p-values")
# axs[0].set_ylabel("Density")
# axs[1].hist(peaks.peak,lw=0,facecolor=twocol[0],normed=True,bins=np.arange(min(peaks.peak),30,0.3),label="observed distribution")
# axs[1].set_xlim([float(parsdata.ExcZ),np.max(peaks.peak)+1])
# axs[1].set_ylim([0,1.3])



Design={"order":np.array([2,1,1,2,1,1,1,2,2,2,1,1,1,1,2,1,2,1,1,2,2,2,1,2,1,1,2,2,1,2,1,2,2,1,1,2,2,2,1,2,1,2,1,1,2,2,2,2,2,2,1,1,2,1,2,1,2,2,2,2,1,1,1,1,2,1,1,2,1,1,2,1,1,2,2,2,2,2,2,2,2,1,2,2,1,2,2,2,1,1,1,2,2,2,2,1,2,1,2,2,1,1,1,2,1,2,2,1,1,2,1,2,1,1,2,2,1,1,1,2,1,2,1,2,2,1,1,1,1,1,1,2,2,1,2,1,2,1,1,1,1,2,2,2,2,1,2,2,1,2,2,1,2,2,1,1,1,1,1,1,1,1,2,1,1,1,2,2,2,2,1,2,1,2,2,1,1,1,2,1,2,2,1,1,2,1,2,1,1,2,2,1,1,1,2,1,2,1,2,2,1,1,1,1,1,1,2,2,1,2,1,2,1,1,1,1,2,2,2,2,1,2,2,1,2,2,1,2,2,1,1,1,1,1,1,1,1,2,2,2,2,2])-1}
Design['ITIs']=[2]*242


Design['deconvM']
array([[ 0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  1.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0
.,  0.,  0.,  0.,  0.,  0.,  0.,  0.],
       [ 1.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  1.,  0.,  0.,  0.,  0.,  0.,  0.,  0
.,  0.,  0.,  0.,  0.,  0.,  0.,  0.],
       [ 1.,  1.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  1.,  0.,  0.,  0.,  0.,  0.,  0
.,  0.,  0.,  0.,  0.,  0.,  0.,  0.],
       [ 0.,  1.,  1.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  1.,  0.,  0.,  1.,  0.,  0.,  0.,  0.,  0
.,  0.,  0.,  0.,  0.,  0.,  0.,  0.],
       [ 1.,  0.,  1.,  1.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  1.,  0.,  0.,  1.,  0.,  0.,  0.,  0
.,  0.,  0.,  0.,  0.,  0.,  0.,  0.],

       [ 1.,  1.,  0.,  1.,  1.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  1.,  0.,  0.,  1.,  0.,  0.,  0
.,  0.,  0.,  0.,  0.,  0.,  0.,  0.],
       [ 1.,  1.,  1.,  0.,  1.,  1.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  1.,  0.,  0.,  1.,  0.,  0
.,  0.,  0.,  0.,  0.,  0.,  0.,  0.],
       [ 0.,  1.,  1.,  1.,  0.,  1.,  1.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  1.,  0.,  0.,  0.,  1.,  0.,  0.,  1.,  0
.,  0.,  0.,  0.,  0.,  0.,  0.,  0.],
       [ 0.,  0.,  1.,  1.,  1.,  0.,  1.,  1.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  1.,  1.,  0.,  0.,  0.,  1.,  0.,  0.,  1
.,  0.,  0.,  0.,  0.,  0.,  0.,  0.],
       [ 0.,  0.,  0.,  1.,  1.,  1.,  0.,  1.,  1.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  1.,  1.,  1.,  0.,  0.,  0.,  1.,  0.,  0
.,  1.,  0.,  0.,  0.,  0.,  0.,  0.],
       [ 1.,  0.,  0.,  0.,  1.,  1.,  1.,  0.,  1.,  1.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  1.,  1.,  1.,  0.,  0.,  0.,  1.,  0
.,  0.,  1.,  0.,  0.,  0.,  0.,  0.],
       [ 1.,  1.,  0.,  0.,  0.,  1.,  1.,  1.,  0.,  1.,  1.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  1.,  1.,  1.,  0.,  0.,  0.,  1
.,  0.,  0.,  1.,  0.,  0.,  0.,  0.],
       [ 1.,  1.,  1.,  0.,  0.,  0.,  1.,  1.,  1.,  0.,  1.,  1.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  1.,  1.,  1.,  0.,  0.,  0
.,  1.,  0.,  0.,  1.,  0.,  0.,  0.],
       [ 1.,  1.,  1.,  1.,  0.,  0.,  0.,  1.,  1.,  1.,  0.,  1.,  1.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  1.,  1.,  1.,  0.,  0
.,  0.,  1.,  0.,  0.,  1.,  0.,  0.],
       [ 0.,  1.,  1.,  1.,  1.,  0.,  0.,  0.,  1.,  1.,  1.,  0.,  1.,  1.,  0.,  0.,  1.,  0.,  0.,  0.,  0.,  1.,  1.,  1.,  0
.,  0.,  0.,  1.,  0.,  0.,  1.,  0.],



stimList=[2,1,1,2,1,1,1,2,2,2,1,1,1,1,2,1,2,1,1,2,2,2,1,2,1,1,2,2,1,2,1,2,2,1,1,2,2,2,1,2,1,2,1,1,2,2,2,2,2,2,1,1,2,1,2,1,2,2,2,2,1,1,1,1,2,1,1,2,1,1,2,1,1,2,2,2,2,2,2,2,2,1,2,2,1,2,2,2,1,1,1,2,2,2,2,1,2,1,2,2,1,1,1,2,1,2,2,1,1,2,1,2,1,1,2,2,1,1,1,2,1,2,1,2,2,1,1,1,1,1,1,2,2,1,2,1,2,1,1,1,1,2,2,2,2,1,2,2,1,2,2,1,2,2,1,1,1,1,1,1,1,1,2,1,1,1,2,2,2,2,1,2,1,2,2,1,1,1,2,1,2,2,1,1,2,1,2,1,1,2,2,1,1,1,2,1,2,1,2,2,1,1,1,1,1,1,2,2,1,2,1,2,1,1,1,1,2,2,2,2,1,2,2,1,2,2,1,2,2,1,1,1,1,1,1,1,1,2,2,2,2,2]
