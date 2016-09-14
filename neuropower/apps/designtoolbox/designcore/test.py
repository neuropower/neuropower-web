import numpy as np
import design
from __future__ import division
# reload(design)
import time

tapsfile = "/Users/Joke/Documents/Onderzoek/ProjectsOngoing/Neuropower/neuropower-web/neuropower/media/taps.p"


des = design.GeneticAlgorithm(
    # design specific
    ITI = [0.5,4],
    TR = 0.68,
    L = 242,
    P = [1/2,1/2],
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
    write = False,
    HardProb = None,
    tapsfile = tapsfile,
    gui_sid=2233
)


Design={"order":np.array([2,1,1,2,1,1,1,2,2,2,1,1,1,1,2,1,2,1,1,2,2,2,1,2,1,1,2,2,1,2,1,2,2,1,1,2,2,2,1,2,1,2,1,1,2,2,2,2,2,2,1,1,2,1,2,1,2,2,2,2,1,1,1,1,2,1,1,2,1,1,2,1,1,2,2,2,2,2,2,2,2,1,2,2,1,2,2,2,1,1,1,2,2,2,2,1,2,1,2,2,1,1,1,2,1,2,2,1,1,2,1,2,1,1,2,2,1,1,1,2,1,2,1,2,2,1,1,1,1,1,1,2,2,1,2,1,2,1,1,1,1,2,2,2,2,1,2,2,1,2,2,1,2,2,1,1,1,1,1,1,1,1,2,1,1,1,2,2,2,2,1,2,1,2,2,1,1,1,2,1,2,2,1,1,2,1,2,1,1,2,2,1,1,1,2,1,2,1,2,2,1,1,1,1,1,1,2,2,1,2,1,2,1,1,1,1,2,2,2,2,1,2,2,1,2,2,1,2,2,1,1,1,1,1,1,1,1,2,2,2,2,2])-1}
Design['ITIs']=[2]*242
Design = des.CreateDesignMatrix(Design)


start_time = time.time()
des.GeneticAlgorithm()
print("--- %s seconds ---" % (time.time()-start_time))





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
# import matplotlib as mpl
# import matplotlib.pyplot as plt
#
# plt.plot(a)
# plt.show()
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
