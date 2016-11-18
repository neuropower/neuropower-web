from designcore import design
import numpy as np

des = design.GeneticAlgorithm(
    # design specific
    ITImodel = "uniform",
    ITIunifmin = 2,
    ITIunifmax = 4,
    TR=2,
    n_trials=100,
    P=np.array([0.3,0.3,0.3]),
    C=np.array([[1,-1,0],[0,1,-1]]),
    stim_duration=1,
    weights=np.array([0,0.5,0.25,0.25]),
    tapsfile="/Users/Joke/Documents/Onderzoek/ProjectsOngoing/Neuropower/neuropower-web/neuropower/taps.p",
    rho=0.3,
    cycles=10,
    preruncycles=10,
    folder="/Users/Joke/designoutput/"
)

des.GeneticAlgorithmInitiate()
if des.weights[0]>0:
    des.prerun = 'Fe'
    des.GeneticAlgorithmNaturalSelection()
    des.FeMax = np.max(des.Best)
if des.weights[1]>0:
    des.prerun = 'Fd'
    des.GeneticAlgorithmNaturalSelection()
    des.FdMax = np.max(des.Best)
des.prerun=None
des.GeneticAlgorithmNaturalSelection()
des.prepare_download()
