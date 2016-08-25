from __future__ import division
import numpy as np
from numpy.linalg import inv
from numpy import transpose as t
from scipy.special import gamma
from collections import Counter
import pandas as pd
import mseq
import itertools
import scipy.linalg
import json
from collections import Counter

class GeneticAlgorithm(object):
    '''
    A class for an experimental design

    Parameters
    ----------
        ITI: list of two floats
            inter-trial interval min and max
        TR: float
            repetition time
        L: integer
            number of trials
        duration: float
            total duration (s)
        P: numpy.array with floats
            probability of each trialtype
        C: numpy array with floats
            contrast matrix (each row = one contrast)
        rho: float
            AR(1) correlation coefficient
        weights: numpy.array with 4 floats
            weights to each of the optimization criteria (order: Fe, Fd, Ff,Fc)
        Aoptimality: boolean, default True
            default usage of A-optimality criterion
            setting parameter to False results in D-optimality
        saturation: boolean, default True
            non-linearity in fMRI signal (see Kao et al.)
        resolution: float, default 0.1
            maximum resolution of design matrix
            has an impact of preciseness of convolved design with HRF
        G: integer, default 20
            number of designs that are transmitted to the next generation
        q: float (0<x<1), default 0.01
            percentage of mutations among all trials
        I: integer, default 4
            number of immigrants per Generation
        cycles: integer
            number of generations in optimisation
        preruncycles: integer
            number of generations to compute the maximum efficiency for Fd and Fe
        ConfoundOrder: integer
            up to which order do we control confounding
            (eg. 3: the probability that A follows A 3 trials ago = A follows B 3 trials ago)
        MaxRepeat: integer
            hard limit on the number of repeated stimuli
        HardProb: boolean, default = False
            setting parameter to True makes hard limit on probabilities
    '''

    def __init__(self,ITI,TR,L,P,C,rho,weights,Aoptimality=True,saturation=True,resolution=0.1,G=20,q=0.01,I=4,cycles=10000,preruncycles=10000,ConfoundOrder=3,MaxRepeat=6,write=None,HardProb=False):
        self.ITI = ITI
        self.mnITI = np.mean(ITI)
        self.TR = TR
        self.L = L
        self.P = P
        self.C = C
        self.stimtype = C.shape[1]
        self.rho = rho
        self.Aoptimality = Aoptimality
        self.saturation = saturation
        self.resolution = resolution
        self.weights = weights
        self.G = G
        self.q = q
        self.I = I
        self.cycles = cycles
        self.ConfoundOrder = ConfoundOrder
        self.rc = C.shape[0]
        self.preruncycles = preruncycles
        self.maxrepeat = MaxRepeat
        self.HardProb = HardProb
        if write:
            self.write = write

        self.CreateTsComp()
        self.CreateLmComp()

    '''
    #########################################################################
    Initial functions for parameters that are constant over different designs
    #########################################################################
    '''

    def CreateTsComp(self):
        # compute number of timepoints (self.tp)
        self.duration = self.L*self.mnITI #total duration (s)
        self.tp = int(np.ceil(self.duration/self.TR)) # number of scans

        return self

    def CreateLmComp(self):
        # compute components for linear model (drift, autocorrelation, projection of drift)

        # drift
        self.S = self.drift(np.arange(0,self.duration,self.TR)) #[tp x 1]
        self.S = np.matrix(self.S)

        # square of the whitening matrix
        base = [1+self.rho**2,-1*self.rho]+[0]*(self.tp-2)
        self.V2 = scipy.linalg.toeplitz(base)
        self.V2[0,0] = 1
        self.V2[self.tp-1,self.tp-1] = 1
        self.V2 = np.matrix(self.V2)
        self.V = scipy.linalg.sqrtm(self.V2)
        P = t(self.S)*np.linalg.pinv(self.S*t(self.S))*self.S

        self.white = t(self.V)*(np.eye(self.tp)-P)*self.V

        # orthogonal projection of whitened drift
        #VS = self.V*self.S
        #self.Pvs = reduce(np.dot,[VS,np.linalg.pinv(np.dot(t(VS),VS)),t(VS)])

        return self

    '''
    ###########################################
    Functions specific to the Genetic Algorithm
    ###########################################
    '''

    def GeneticAlgorithm(self):

        # Create first generation
        Generation = self.GeneticAlgorithmInitiate()

        # Natural selection
        NatSel = self.GeneticAlgorithmNaturalSelection(cycles=self.cycles,
                                Generation = Generation)

        # Select optimal design
        Generation = NatSel['Generation']
        Best = NatSel['Best']

        OptInd = np.min(np.arange(len(Generation['F']))[Generation['F']==np.max(Generation['F'])])
        self.opt = {
            'order':Generation['order'][OptInd],
            'onsets':Generation['onsets'][OptInd],
            'F':Generation['F'][OptInd],
            'FScores':Best
            }

        return self

    def GeneticAlgorithmNaturalSelection(self,cycles, Generation):

        Best = []
        for gen in range(cycles):
            self.counter = self.counter + 1
            print("Generation: "+str(gen+1))
            NextGen = self.GeneticAlgorithmGeneration(Generation)
            Generation = NextGen["NextGen"]
            Best.append(NextGen['FBest'])
            if self.write:
                with open(self.write,'w') as fp:
                    json.dump(Generation,fp)


        NatSel = {"Best":Best,
               "Generation":Generation}

        return NatSel

    def GeneticAlgorithmCreateEmptyGeneration(self):
        # Create empty generation
        Generation = {
            'order' : [],
            'onsets': [],
            'F' : [],
            'Fd': [],
            'Fe': [],
            'Ff': [],
            'Fc': [],
            'ID' : []
        }

        return Generation


    def GeneticAlgorithmInitiate(self):

        # Compute maximum efficiency
        self.ComputeMaximumEfficiency()
        self.counter = 1

        Generation = self.GeneticAlgorithmCreateEmptyGeneration()

        self.GeneticAlgorithmCreateOrder()

        # Create first generation
        weights = [0,0,1.] if self.HardProb==True else [1/3.,1/3.,1/3.]
        weights = [int(x) for x in np.array(weights)*self.G]
        Generation = self.GeneticAlgorithmAddOrder(Generation,weights)

        return Generation

    def GeneticAlgorithmGeneration(self,Generation):

        # Add children to generation
        Generation = self.GeneticAlgorithmCrossover(Generation)
        Generation = self.GeneticAlgorithmMutation(Generation)
        Generation = self.GeneticAlgorithmImmigration(Generation)
        Generation = self.GeneticAlgorithmConstraints(Generation)

        if len(Generation['F'])==0:
            Generation = self.GeneticAlgorithmAddOrder(Generation,[7,7,6])

        # To check overall improvement: save best design in Generation
        a = 2.1
        #Generation['Ft'] = [float(np.random.uniform(0,1,1)+1/(1+np.exp(-a*x))) for x in Generation['F']]
        Generation['Ft'] = [x for x in Generation['F']]
        best = np.min(np.argmax(Generation['Ft']))
        FBest = Generation['Ft'][best]
        FeBest = Generation['Fe'][best]
        FfBest = Generation['Ff'][best]
        FcBest = Generation['Fc'][best]
        FdBest = Generation['Fd'][best]

        # Select G best designs for Next Generation
        FCutOff = np.min(sorted(Generation['Ft'], reverse=True)[:self.G])
        OptIndLg = np.arange(len(Generation['Ft']))[Generation['Ft']>FCutOff]
        needed = self.G-len(OptIndLg)
        OptIndEq = np.arange(len(Generation['Ft']))[Generation['Ft']==FCutOff][:needed]
        OptInd = np.concatenate([OptIndLg,OptIndEq])

        NextGen = {}
        for DictEl in Generation.keys():
            NextGen[DictEl] = [Generation[DictEl][ind] for ind in OptInd]

        # create output
        out = {
            "NextGen":NextGen,
            "FBest":FBest,
            'FeBest':FeBest,
            'FfBest':FfBest,
            'FcBest':FcBest,
            'FdBest':FdBest
        }

        return out

    def GeneticAlgorithmConstraints(self,Generation):

        # cutoff on number of repeats
        IndMaxRep = []
        if self.maxrepeat:
            for ord in range(len(Generation['order'])):
                RepCheck = ''.join(str(e) for e in [0]*(self.maxrepeat+1)) in ''.join(str(e) for e in Generation['order'][ord])
                if RepCheck:
                    IndMaxRep.append(ord)

        IndHardProb = []
        if self.HardProb:
            for ord in range(len(Generation['order'])):
                ObsCnt = Counter(Generation['order'][ord]).values()
                ObsProb = [np.around(float(x)/float(np.sum(ObsCnt)),decimals=2) for x in ObsCnt]
                ProbCheck = np.array_equal(np.array(ObsProb),np.array(self.P))
                if not ProbCheck:
                    IndHardProb.append(ord)

        if self.maxrepeat or self.HardProb:
            IndRemove = IndMaxRep+IndHardProb
            for key in Generation.keys():
                Generation[key] = [x for ind, x in enumerate(Generation[key]) if not ind in IndRemove]

        return Generation

    def GeneticAlgorithmAddDestoGen(self,Generation,Design):
        Generation['order'].append(Design['order'])
        Generation['onsets'].append(Design['onsets'])
        Generation['F'].append(Design['F'])
        Generation['Fd'].append(Design['Fd'])
        Generation['Fe'].append(Design['Fe'])
        Generation['Fc'].append(Design['Fc'])
        Generation['Ff'].append(Design['Ff'])
        Generation['ID'].append(np.max(Generation['ID'])+1 if len(Generation['ID'])>0 else 1)

        return Generation

    def GeneticAlgorithmCrossover(self,Generation): ## REPLACE OR ADD?

        # Randomly select partners and loop over couples for babies
        noparents = int(len(Generation['order']))
        npairs = int(noparents/2.)
        CouplingRnd = np.random.choice(noparents,size=(npairs*2),replace=True)
        CouplingRnd = [[CouplingRnd[i],CouplingRnd[i+1]] for i in np.arange(0,npairs*2,2)]
        for couple in CouplingRnd:

            # randomly select a timepoint for cross-over
            changepoint = np.random.choice(self.L,1)[0]

            #create baby 1
            baby1_a = Generation['order'][couple[0]][:changepoint]
            baby1_b = Generation['order'][couple[1]][changepoint:]
            baby1_A = Generation['onsets'][couple[0]][:changepoint]
            baby1_B = Generation['onsets'][couple[1]][changepoint:]
            baby1 = {'order':np.concatenate([baby1_a,baby1_b]),'onsets':np.concatenate([baby1_A,baby1_B])}
            baby1 = self.CreateDesignMatrix(baby1)
            baby1 = self.ComputeEfficiency(baby1)

            # add baby 1 to Generation
            Generation = self.GeneticAlgorithmAddDestoGen(Generation,baby1)

            #create baby 2
            baby2_a = Generation['order'][couple[1]][:changepoint]
            baby2_b = Generation['order'][couple[0]][changepoint:]
            baby2_A = Generation['onsets'][couple[1]][:changepoint]
            baby2_B = Generation['onsets'][couple[0]][changepoint:]
            baby2 = {'order':np.concatenate([baby2_a,baby2_b]),'onsets':np.concatenate([baby2_A,baby2_B])}
            baby2 = self.CreateDesignMatrix(baby2)
            baby2 = self.ComputeEfficiency(baby2)

            # add baby 2 to Generation
            Generation = self.GeneticAlgorithmAddDestoGen(Generation,baby2)

        return Generation

    def GeneticAlgorithmMutation(self,Generation): ## REPLACE OR ADD?

        # loop over first G designs
        noparents = int(len(Generation['order'])/2.) #(assuming crossover was done before)
        for order,onsets in zip(Generation['order'][:noparents],Generation['onsets'][:noparents]):

            # randomly select the trials that will be mutated
            mutated = np.random.choice(self.L,int(round(self.L*self.q)),replace=False)

            # replace mutated trials by a randomly chosen stimulus
            mutatedorder = [np.random.choice(self.stimtype,1)[0] if ind in mutated else value for ind,value in enumerate(order)]
            mutatedbaby = {'order':mutatedorder}
            mutatedbaby['onsets'] = onsets
            mutatedbaby = self.CreateDesignMatrix(mutatedbaby)
            mutatedbaby = self.ComputeEfficiency(mutatedbaby)

            # add mutated designs to Generation
            Generation = self.GeneticAlgorithmAddDestoGen(Generation,mutatedbaby)

        return Generation

    def GeneticAlgorithmImmigration(self,Generation):

        # equally distribute new immigrants (blocked, msequence, ...)
        rp = [1/3.,1/3.,1/3.]
        r = [int(np.ceil(x*self.I)) for x in rp]
        r = r[:self.I]

        # add random orders according to types
        Generation = self.GeneticAlgorithmAddOrder(Generation,r)

        return Generation

    '''
    ####################################
    Functions specific to create designs
    ####################################
    '''

    def GeneticAlgorithmCreateOrder(self):
        Designs = {}
        nRandom = 10000
        Designs['Blocked'] = self.GenerateOrderBlocked()
        Designs['Mseq'] = self.GenerateOrderMsequence()
        Designs['Random'] = self.GenerateOrderRandom(nRandom)
        self.Designs = Designs

        return self

    def GeneticAlgorithmAddOrder(self,Generation,r):

        # r how many of each kind?
        nBlocked = r[0]
        nMseq = r[1]
        nRandom = r[2]

        iBlocked = np.random.choice(len(self.Designs['Blocked']['orders']),nBlocked,replace=False).tolist()
        oBlocked = [self.Designs['Blocked']['orders'][i] for i in iBlocked]
        tBlocked = [self.Designs['Blocked']['onsets'][i] for i in iBlocked]
        iMseq = np.random.choice(len(self.Designs['Mseq']['orders']),nMseq,replace=False).tolist()
        oMseq = [self.Designs['Mseq']['orders'][i] for i in iMseq]
        tMseq = [self.Designs['Mseq']['onsets'][i] for i in iMseq]
        iRandom = np.random.choice(len(self.Designs['Random']['orders']),nRandom,replace=False).tolist()
        oRandom = [self.Designs['Random']['orders'][i] for i in iRandom]
        tRandom = [self.Designs['Random']['onsets'][i] for i in iRandom]

        oTotal = []
        for orders in [oBlocked,oMseq,oRandom]:
            if isinstance(orders,list):
                oTotal = oTotal+orders
            else:
                oTotal.append(orders)

        tTotal = []
        for orders in [tBlocked,tMseq,tRandom]:
            if isinstance(orders,list):
                tTotal = tTotal+orders
            else:
                tTotal.append(orders)

        id = self.counter*100
        for order,onsets in zip(oTotal,tTotal):
            id = id+1
            NewDesign = {}
            NewDesign['order'] = order
            NewDesign['onsets'] = onsets
            NewDesign = self.CreateDesignMatrix(NewDesign)
            NewDesign = self.ComputeEfficiency(NewDesign)

            # add new designs to Generation
            Generation = self.GeneticAlgorithmAddDestoGen(Generation,NewDesign)

        return Generation

    def GenerateOrderRandom(self,number):
        orders = []
        onsets = []
        for ind in range(number):
            seed = np.random.randint(0,10**10)
            mult = np.random.multinomial(1,self.P,self.L)
            order = [x.tolist().index(1) for x in mult]
            orders.append(order)
            shift = self.mnITI/2.
            onset = [shift*2]*self.L
            onset = np.cumsum(onset)-shift
            jitter = np.random.uniform(-shift,shift,self.L)
            onset = onset+jitter
            onset = onset-np.min(onset)
            onsets.append(onset)

        return {"orders":orders,"onsets":onsets}

    def GenerateOrderMsequence(self):
        order = mseq.Msequence()
        order.GenMseq(mLen=self.L,stimtypeno=len(self.P))
        orders = order.orders

        onsets = []
        for ind in range(len(orders)):
            shift = self.mnITI/2.
            onset = [shift*2]*self.L
            onset = np.cumsum(onset)-shift
            jitter = np.random.uniform(-shift,shift,self.L)
            onset = onset+jitter
            onset = onset-np.min(onset)
            onsets.append(onset)

        return {"orders":orders,"onsets":onsets}

    def GenerateOrderBlocked(self):
        numBlocks = np.array([1,2,3,4,5,10,15,20,25,30,40])
        orders = []
        for blocks in numBlocks:
            BlockSize = int(np.ceil(self.L/(blocks*self.stimtype)))
            perms = list(itertools.permutations(range(self.stimtype)))
            for permut in perms:
                order = np.tile(np.repeat(list(permut),BlockSize),blocks).tolist()
                if len(order) > self.L:
                    order = order[:self.L]
                orders.append(order)

        onsets = []
        for ind in range(len(orders)):
            shift = np.mean(self.ITI)/2.
            onset = [shift*2]*self.L
            onset = np.cumsum(onset)-shift
            jitter = np.random.uniform(-shift,shift,self.L)
            onset = onset+jitter
            onset = onset-np.min(onset)
            onsets.append(onset)

        return {"orders":orders,"onsets":onsets}

    '''
    ###############################
    Functions to compute efficiency
    ###############################
    '''

    def CreateDesignMatrix(self,Design):
        '''
        Expand from order of stimuli to a fMRI timeseries
        Parameters
        ----------
            Design: dictionary
                Design['order']: dictionary with key 'order' generated by GenerateOrderXXX() functions or manual
                Design['onsets']: dictionary with key 'onsets'
        Returns
        -------
            Design: dictionary
                Design['X']: numpy array representing design matrix
                Design['Z']: numpy array representing convolved design matrix
        '''

        # upsample from trials to deciseconds

        tpX = int(self.duration/self.resolution) #total number of timepoints (upsampled)
        tpS = np.arange(0,self.duration,self.resolution)

        # expand random order to timeseries

        onsetX = [round(x/self.resolution)*self.resolution for x in Design['onsets']]
        index = [int(np.where(tpS==y)[0]) for y in onsetX]

        X_X = np.zeros([tpX,self.stimtype]) #upsampled Xmatrix
        XindStim = np.arange(0,tpX,self.mnITI/self.resolution).astype(int) # index of stimuluspoints in upsampled Xmatrix
        for stimulus in range(self.stimtype):
            # fill
            X_X[XindStim,int(stimulus)] = [1 if z==stimulus else 0 for z in Design["order"]]

        # convolve design matrix

        h0 = self.canonical(np.arange(0,self.duration,self.resolution))
        Z_X = np.zeros([tpX,self.stimtype])
        for stimulus in range(self.stimtype):
            Zinterim = np.convolve(X_X[:,stimulus],h0)[range(tpX)]
            ZinterimScaled = Zinterim/np.max(h0)
            if self.saturation==True:
                ZinterimScaled = [2 if x>2 else x for x in ZinterimScaled]
            Z_X[:,stimulus] = ZinterimScaled

        # downsample from deciseconds to scans

        XindScan = np.arange(0,tpX,self.TR/self.resolution).astype(int) # stimulus points
        X = np.zeros([self.tp,self.stimtype])
        Z = np.zeros([self.tp,self.stimtype])
        for stimulus in range(self.stimtype):
            X[:,stimulus] = X_X[XindScan,stimulus]
            Z[:,stimulus] = Z_X[XindScan,stimulus]

        # downsample and save in dictionary

        Design["X"] = X
        Design["Z"] = Z
        Design["ts"] = tpS

        return Design

    def ComputeEfficiency(self,Design):

        '''
        Compute efficiency as defined in Kao, 2009 from fMRI timeseries
        Parameters
        ----------
            Design: dictionary
                Design['order']: dictionary with key 'order' generated by GenerateOrderXXX() or manual
                Design['X']: numpy array representing design matrix
                Design['Z']: numpy array representing convolved design matrix
        Returns
        -------
            Design: dictionary
                Design['Fe']: estimation efficiency
                Design['Fd']: detection power
                Design['Ff']: efficiency against psychological confounds
                Design['Fc']: optimality of probability of trials
        '''
        Design['Fe'] = 0
        Design['Fd'] = 0
        Design['Ff'] = 0
        Design['Fc'] = 0

        if self.prerun=="Fe":
            weightsFnc = [1,0,0,0]
        elif self.prerun=="Fd":
            weightsFnc = [0,1,0,0]
        else:
            weightsFnc = self.weights


        if weightsFnc[0]>0:
            FeMax = 1 if self.prerun else self.FeMax
            Design = self.FeCalc(Design)
            Design['Fe']=Design['Fe']/FeMax
        if weightsFnc[1]>0:
            FdMax = 1 if self.prerun else self.FdMax
            Design = self.FdCalc(Design)
            Design['Fd']=Design['Fd']/FdMax
        if weightsFnc[2]>0:
            Design = self.FfCalc(Design)
            Design['Ff']=1-Design['Ff']/self.FfMax
        if weightsFnc[3]>0:
            Design = self.FcCalc(Design)
            Design['Fc']=1-Design['Fc']/self.FcMax

        Design['F'] = np.sum(weightsFnc * np.array([Design['Fe'],Design['Fd'],Design['Ff'],Design['Fc']]))

        return Design

    def ComputeMaximumEfficiency(self):
        nulorder = [np.argmin(self.P)]*self.L
        nulonsets = [0]*self.L
        NulDesign = {"order":nulorder,"onsets":nulonsets}
        NulDesign = self.CreateDesignMatrix(NulDesign)
        self.FfMax = self.FfCalc(NulDesign)['Ff']
        self.FcMax = self.FcCalc(NulDesign)['Fc']

        # prerun for FeMax #
        if self.weights[0]>0:
            self.prerun = 'Fe'
            self.counter = 1
            Generation = self.GeneticAlgorithmCreateEmptyGeneration()
            self.GeneticAlgorithmCreateOrder()
            r = [7,7,6]
            Generation = self.GeneticAlgorithmAddOrder(Generation,r)
            NatSel = self.GeneticAlgorithmNaturalSelection(cycles=self.preruncycles,
                                            Generation = Generation)
            self.FeMax = NatSel['Best'][-1]

        # prerun for FdMax #

        if self.weights[1]>0:
            self.prerun = 'Fd'
            self.counter = 1
            Generation = self.GeneticAlgorithmCreateEmptyGeneration()
            self.GeneticAlgorithmCreateOrder()
            r = [7,7,6]
            Generation = self.GeneticAlgorithmAddOrder(Generation,r)
            NatSel = self.GeneticAlgorithmNaturalSelection(cycles=self.preruncycles,
                                            Generation = Generation)
            self.FdMax = NatSel['Best'][-1]

        self.prerun = None

        return self

    def FeCalc(self,Design):
        W = Design['X']
        X = t(W)*self.white*W
        invM = scipy.linalg.pinv(X)
        CMC = np.matrix(self.C)*invM*np.matrix(t(self.C))
        if self.Aoptimality == True:
            Design["Fe"] = float(self.rc/np.matrix.trace(CMC))
        else:
            Design["Fe"] = float(np.linalg.det(CMC)**(-1/self.rc))

        return Design

    def FdCalc(self,Design):
        W = np.matrix(Design['Z'])
        X = t(W)*self.white*W
        invM = scipy.linalg.pinv(X)
        CMC = np.matrix(self.C)*invM*np.matrix(t(self.C))
        if self.Aoptimality == True:
            Design["Fd"] = float(self.rc/np.matrix.trace(CMC))
        else:
            Design["Fd"] = float(np.linalg.det(CMC)**(-1/self.rc))
        return Design

    def FcCalc(self,Design):
        Q = np.zeros([self.stimtype,self.stimtype,self.ConfoundOrder])
        for n in range(self.L):
            for r in range(self.ConfoundOrder):
                if n>(r-1):
                    Q[Design['order'][n],Design['order'][n-r],r] += 1
        Qexp = np.zeros([self.stimtype,self.stimtype,self.ConfoundOrder])
        for si in range(self.stimtype):
            for sj in range(self.stimtype):
                for r in range(self.ConfoundOrder):
                    Qexp[si,sj,r] = self.P[si]*self.P[sj]*(self.L-r+1)
        Qmatch = np.sum(abs(Q-Qexp))
        Design["Fc"] = Qmatch
        return Design

    # Ff frequencies
    def FfCalc(self,Design):
        trialcount = Counter(Design['order'])
        Pobs = [x[1] for x in trialcount.items()]
        Design["Ff"] = np.sum(abs(Pobs-self.L*self.P))
        return Design

    @staticmethod
    def drift(s):
        # second order Legendre polynomial
        # arguments: s = seconds after start
        ts = 1/2*(3*s**2-1)
        return ts

    @staticmethod
    def canonical(s,a1=6,a2=16,b1=1,b2=1,c=1/6,amplitude=1):
        #Canonical HRF as defined here: http://www.ncbi.nlm.nih.gov/pmc/articles/PMC3318970/
        # arguments: s seconds
        gamma1 = (s**(a1-1)*b1**a1*np.exp(-b1*s))/gamma(a1)
        gamma2 = (s**(a2-1)*b2**a2*np.exp(-b2*s))/gamma(a2)
        tsConvoluted = amplitude*(gamma1-c*gamma2)
        return tsConvoluted
