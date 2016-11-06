from __future__ import division
import numpy as np
from numpy.linalg import inv
import scipy
from scipy import linalg
from numpy import transpose as t
from scipy.special import gamma
from collections import Counter
import pandas as pd
import mseq
import itertools
import scipy.linalg
import json
from collections import Counter
import os
import sys
import numpy as np
import zipfile
import StringIO
import shutil

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
        restnum
        restlength
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

    def __init__(self,TR,P,C,rho,weights,tapsfile,stim_duration,n_trials=None,duration=None,restnum=0,restlength=0,Aoptimality=True,saturation=False,resolution=0.1,G=20,q=0.01,I=4,cycles=10000,preruncycles=10000,ConfoundOrder=3,MaxRepeat=100,write_score=False,write_design=False,HardProb=False,gui_sid=False,convergence=None,ITImodel="uniform",ITIfixed=None,ITIunifmin=None,ITIunifmax=None,ITItruncmin=None,ITItruncmax=None,ITItruncmean=None,folder=None):
        self.ITImodel = ITImodel
        self.ITIfixed = ITIfixed
        self.ITIunifmin = ITIunifmin
        self.ITIunifmax = ITIunifmax
        self.ITItruncmin = ITItruncmin
        self.ITItruncmax = ITItruncmax
        self.ITItruncmean = ITItruncmean
        self.TR = TR
        self.n_trials = n_trials
        self.duration = duration
        self.n_cons = C.shape[0]
        self.n_stimuli = C.shape[1]
        self.stim_duration = stim_duration
        self.P = P
        self.C = C
        self.rho = rho
        self.restnum = restnum
        self.restlength = restlength
        self.Aoptimality = Aoptimality
        self.saturation = saturation
        self.resolution = resolution
        self.weights = weights
        self.G = G
        self.q = q
        self.I = I
        self.cycles = cycles
        self.ConfoundOrder = ConfoundOrder
        self.preruncycles = preruncycles
        self.maxrepeat = MaxRepeat
        self.HardProb = HardProb
        self.tapsfile = tapsfile
        self.counter = 0
        self.prerun = None
        self.FeMax = 1
        self.FdMax = 1
        self.FfMax = 1
        self.FcMax = 1
        self.CX = None
        self.laghrf = None
        self.basishrf = None
        self.n_tp = None
        self.n_scans = None
        self.r_tp = None
        self.r_scans = None
        self.write_score = write_score
        self.write_design = write_design
        self.convergence=convergence
        self.seed = 1234
        self.folder = folder

        self.CreateTsComp()
        self.CreateLmComp()

        self.printcmd()

    '''
    #########################################################################
    Initial functions for parameters that are constant over different designs
    #########################################################################
    '''

    def canonical(self,resolution):
        # translated from spm_hrf
        p=[6,16,1,1,6,0,32]
        dt = resolution/16.
        s = np.array(xrange(int(p[6]/dt+1)))
        #HRF sampled at 0.1 s
        hrf = self.spm_Gpdf(s,p[0]/p[2],dt/p[2]) - self.spm_Gpdf(s,p[1]/p[3],dt/p[3])/p[4]
        hrf = hrf[[int(x) for x in np.array(xrange(int(p[6]/resolution+1)))*16.]]
        self.hrf = hrf/np.sum(hrf)
        #self.hrf = self.hrf/np.max(self.hrf)
        # HRF sampled at resolution
        self.basishrf = self.hrf[[int(x) for x in np.arange(0,len(self.hrf)-1,self.resolution*10)]]
        # duration of the HRF
        self.durhrf = 32.0
        # length of the HRF parameters in resolution scale
        self.laghrf = int(np.ceil(self.durhrf/self.resolution))

        return self

    def CreateTsComp(self):
        # ITI mean
        if self.ITImodel == "uniform":
            self.mnITI = float(self.ITIunifmin+self.ITIunifmax)/2
        elif self.ITImodel == "fixed":
            self.mnITI = self.ITIfixed
        elif self.ITImodel == "truncated exponential":
            self.mnITI = self.ITItruncmean
            opt = scipy.optimize.minimize(self.diftexp,[1.5],args=(self.ITItruncmin,self.ITItruncmax,self.ITItruncmean,))
            self.lam = opt.x

        # compute number of timepoints (self.tp)
        resdur = 0
        if self.restnum>0:
            resdur = (np.floor(self.n_trials/self.restnum)*self.restlength) #total duration (s)
        if self.duration:
            trialdur = float(self.duration-resdur)
            SOA = float(self.stim_duration + self.mnITI)
            self.n_trials = int(np.floor(trialdur/SOA))
        if self.n_trials:
            ITIdur = self.n_trials*self.mnITI
            STIMdur = self.n_trials*self.stim_duration
            self.duration = ITIdur+STIMdur
        self.duration_norest = self.duration
        self.duration = self.duration+resdur
        self.n_scans = int(np.ceil(self.duration/self.TR)) # number of scans
        self.n_tp = int(np.ceil(self.duration/self.resolution)) #number of timepoints (in resolution)
        self.r_scans = np.arange(0,self.duration,self.TR)
        self.r_tp = np.arange(0,self.duration,self.resolution)

        return self

    def CreateLmComp(self):
        # compute components for linear model (drift, autocorrelation, projection of drift)

        # hrf
        self.canonical(0.1)

        # contrasts
        # expand contrasts to resolution of HRF (?)
        self.CX = np.kron(self.C,np.eye(self.laghrf))

        # drift
        self.S = self.drift(np.arange(0,self.n_scans)) #[tp x 1]
        self.S = np.matrix(self.S)

        # square of the whitening matrix
        base = [1+self.rho**2,-1*self.rho]+[0]*(self.n_scans-2)
        self.V2 = scipy.linalg.toeplitz(base)
        self.V2[0,0] = 1
        self.V2 = np.matrix(self.V2)
        self.V2[self.n_scans-1,self.n_scans-1] = 1

        self.white = self.V2 - self.V2*t(self.S)*np.linalg.pinv(self.S*self.V2*t(self.S))*self.S*self.V2

        return self

    '''
    ######################################################
    Functions related to initiating of design optimisation
    ######################################################
    '''

    def GeneticAlgorithmInitiate(self):
        self.GeneticAlgorithmCreateOrder()

        nulorder = [np.argmin(self.P)]*self.n_trials
        nulitis = [self.mnITI]*self.n_trials

        NulDesign = {"order":nulorder,"ITIs":nulitis}
        NulDesign = self.CreateDesignMatrix(NulDesign)
        self.FfMax = self.FfCalc(NulDesign)['Ff']
        self.FcMax = self.FcCalc(NulDesign)['Fc']

        return self

    def GeneticAlgorithmCreateOrder(self):
        Designs = {}
        nRandom = 10000
        Designs['Blocked'] = self.GenerateOrderBlocked()
        if not (self.n_stimuli == 6 or self.n_stimuli == 10):
            Designs['Mseq'] = self.GenerateOrderMsequence()
        Designs['Random'] = self.GenerateOrderRandom(nRandom)
        self.Designs = Designs

        return self

    def GenerateOrderRandom(self,number):
        orders = []
        ITIs = []
        for ind in xrange(number):
            self.seed=self.seed+1
            np.random.seed(self.seed)
            mult = np.random.multinomial(1,self.P,self.n_trials)
            order = [x.tolist().index(1) for x in mult]
            orders.append(order)

            ITI = self.smpl_ITI()
            ITIs.append(ITI)

        return {"orders":orders,"ITIs":ITIs}

    def GenerateOrderMsequence(self):
        order = mseq.Msequence()
        order.GenMseq(mLen=self.n_trials,stimtypeno=len(self.P),tapsfile=self.tapsfile)
        orders = order.orders

        ITIs = []
        for ind in xrange(len(orders)):
            ITI = self.smpl_ITI()
            ITIs.append(ITI)

        return {"orders":orders,"ITIs":ITIs}

    def GenerateOrderBlocked(self):
        numBlocks = np.arange(3,self.maxrepeat)
        orders = []
        for blocks in numBlocks:
            BlockSize = int(np.ceil(self.n_trials/(blocks*self.n_stimuli)))
            perms = list(itertools.permutations(xrange(self.n_stimuli)))
            if len(perms)>100:
                self.seed=self.seed+1
                np.random.seed(self.seed)
                rind = np.random.randint(0,len(perms),100)
                perms = [np.array(perms[k]) for k in rind]
            for permut in perms:
                order = np.tile(np.repeat(list(permut),BlockSize),blocks).tolist()
                if len(order) > self.n_trials:
                    order = order[:self.n_trials]
                orders.append(order)

        ITIs = []
        for ind in xrange(len(orders)):
            ITI = self.smpl_ITI()
            ITIs.append(ITI)

        return {"orders":orders,"ITIs":ITIs}

    '''
    ###########################################
    Functions specific to the Genetic Algorithm
    ###########################################
    '''

    def GeneticAlgorithmNaturalSelection(self):
        if self.prerun=="Fe" or self.prerun=="Fd":
            cycles=self.preruncycles
        else:
            cycles=self.cycles
        # sid is a parameter for monitoring

        Generation = self.GeneticAlgorithmCreateEmptyGeneration()

        # number of designs to be added
        if not (self.n_stimuli == 6 or self.n_stimuli == 10):
            rp = [1/4.,2/4.,1/4.]
        else:
            rp = [2/4.,0,2/4.]
        r = [int(np.ceil(x*self.G)) for x in rp]
        r[2] = r[2]-int(np.sum(r)-self.G)
        Generation = self.GeneticAlgorithmAddOrder(Generation,r)

        self.counter = 0

        if self.write_score:
            Out = {"FBest": [], 'FeBest': [], 'FfBest': [],
                   'FcBest': [], 'FdBest': [], 'Gen': []}

        Best = []
        conv=False
        for gen in xrange(cycles):

            # start loop
            self.counter = self.counter + 1
            print("Generation: "+str(gen+1))
            NextGen = self.GeneticAlgorithmGeneration(Generation)
            Generation = NextGen["NextGen"]

            # write away best
            Best.append(NextGen['FBest'])

            # check for convergence
            if self.convergence:
                last = len(Best)-1
                earlier = int(last-self.convergence)
                if self.counter>self.convergence:
                    conv = (Best[last]-Best[earlier])<10**(-6)
                    if conv:
                        break

            # write scores
            if self.write_score:
                for key in ['FBest','FeBest','FfBest','FcBest','FdBest']:
                    Out[key].append(NextGen[key])
                Out['Gen'].append(gen)
                with open(self.write_score,'w') as fp:
                    json.dump(Out,fp)

            # write design
            if self.write_design:
                keys = ["Stimulus_"+str(i) for i in range(self.n_stimuli)]
                Seq = {}
                for s in keys:
                    Seq.update({s:[]})
                for stim in range(self.n_stimuli):
                    Seq["Stimulus_"+str(stim)]=NextGen["Design"]["Xconv"][:,stim].tolist()
                Seq.update({"tps":NextGen["Design"]["ts"].tolist()})
                with open(self.write_design,'w') as out2file:
                    json.dump(Seq,out2file)

        self.Best = Best
        self.conv = conv
        self.Generation = Generation

        return self

    def GeneticAlgorithmCreateEmptyGeneration(self):
        # Create empty generation
        Generation = {
            'order' : [],
            'onsets': [],
            'ITIs': [],
            'F' : [],
            'FdNorm': [],
            'FeNorm': [],
            'FfNorm': [],
            'FcNorm': [],
            'ID' : []
        }

        return Generation

    def GeneticAlgorithmGeneration(self,Generation):

        # make babies and check constraints
        Children = self.GeneticAlgorithmCrossover(Generation)
        Children = self.GeneticAlgorithmMutation(Children)
        Children = self.GeneticAlgorithmConstraints(Children)

        # depending on how many babies: get immigrants
        Immigrants = self.GeneticAlgorithmImmigration(Children)
        Immigrants = self.GeneticAlgorithmConstraints(Immigrants)

        # add newbies to Population
        Generation = self.AddNewbiesEfficiencies(Generation,Children)
        Generation = self.AddNewbiesEfficiencies(Generation,Immigrants)

        # To check overall improvement: save best design in Generation
        #a = 2.1
        #Generation['Ft'] = [float(np.random.uniform(0,1,1)+1/(1+np.exp(-a*x))) for x in Generation['F']]
        Generation['Ft'] = [x for x in Generation['F']]
        best = np.min(np.argmax(Generation['Ft']))
        FBest = Generation['Ft'][best]
        FeBest = Generation['FeNorm'][best]
        FfBest = Generation['FfNorm'][best]
        FcBest = Generation['FcNorm'][best]
        FdBest = Generation['FdNorm'][best]

        # Make design with best from Generation
        Design = {
            "order":Generation['order'][best],
            "ITIs":Generation['ITIs'][best],
            'onsets':Generation['onsets'][best]}
        Design = self.CreateDesignMatrix(Design)

        # Select G best designs for Next Generation
        FCutOff = np.min(sorted(Generation['Ft'], reverse=True)[:self.G])
        OptIndLg = np.arange(len(Generation['Ft']))[Generation['Ft']>FCutOff]
        needed = self.G-len(OptIndLg) #little trick for when multiple designs have the same fit
        OptIndEq = np.arange(len(Generation['Ft']))[Generation['Ft']==FCutOff][:needed]
        OptInd = np.concatenate([OptIndLg,OptIndEq])

        # Copy best G designs from Generation to NextGen
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
            'FdBest':FdBest,
            'Design':Design
        }

        return out

    def GeneticAlgorithmConstraints(self,Generation):

        # cutoff on number of repeats
        IndMaxRep = []
        if self.maxrepeat:
            for ord in xrange(len(Generation['order'])):
                RepCheck = ''.join(str(e) for e in [0]*(self.maxrepeat)) in ''.join(str(e) for e in Generation['order'][ord])
                if RepCheck:
                    IndMaxRep.append(ord)

        IndHardProb = []
        if self.HardProb:
            for ord in xrange(len(Generation['order'])):
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
        fill = list(set(Design.keys()) & set(Generation.keys()))
        for keys in fill:
            Generation[keys].append(Design[keys])
        Generation['ID'].append(np.max(Generation['ID'])+1 if len(Generation['ID'])>0 else 1)

        return Generation

    def GeneticAlgorithmCrossover(self,Generation):

        # replace
        NextGeneration = self.GeneticAlgorithmCreateEmptyGeneration()

        # Randomly select partners and loop over couples for babies
        noparents = int(len(Generation['order']))
        npairs = int(noparents/2.)
        self.seed=self.seed+1
        np.random.seed(self.seed)
        CouplingRnd = np.random.choice(noparents,size=(npairs*2),replace=True)
        CouplingRnd = [[CouplingRnd[i],CouplingRnd[i+1]] for i in np.arange(0,npairs*2,2)]
        for couple in CouplingRnd:

            # randomly select a timepoint for cross-over
            changepoint = np.random.choice(self.n_trials,1)[0]

            #create baby 1
            baby1_a = Generation['order'][couple[0]][:changepoint]
            baby1_b = Generation['order'][couple[1]][changepoint:]
            baby1_O = Generation['ITIs'][couple[0]]
            baby1 = {'order':np.concatenate([baby1_a,baby1_b]),'ITIs':baby1_O}

            #create baby 2
            baby2_a = Generation['order'][couple[1]][:changepoint]
            baby2_b = Generation['order'][couple[0]][changepoint:]
            baby2_O = Generation['ITIs'][couple[1]]
            baby2 = {'order':np.concatenate([baby2_a,baby2_b]),'ITIs':baby2_O}

            # add babies to Generation
            NextGeneration = self.GeneticAlgorithmAddDestoGen(NextGeneration,baby1)
            NextGeneration = self.GeneticAlgorithmAddDestoGen(NextGeneration,baby2)

        return NextGeneration

    def GeneticAlgorithmMutation(self,Generation):

        NextGeneration = self.GeneticAlgorithmCreateEmptyGeneration()

        # loop over first G designs
        for order,ITIs in zip(Generation['order'],Generation['ITIs']):

            # randomly select the trials that will be mutated
            self.seed=self.seed+1
            np.random.seed(self.seed)
            mutated = np.random.choice(self.n_trials,int(round(self.n_trials*self.q)),replace=False)

            # replace mutated trials by a randomly chosen stimulus
            self.seed=self.seed+1
            np.random.seed(self.seed)
            mutatedorder = [np.random.choice(self.n_stimuli,1)[0] if ind in mutated else value for ind,value in enumerate(order)]
            mutatedbaby = {'order':mutatedorder}
            mutatedbaby['ITIs'] = ITIs

            # add mutated designs to Generation
            NextGeneration = self.GeneticAlgorithmAddDestoGen(NextGeneration,mutatedbaby)

        return NextGeneration

    def GeneticAlgorithmImmigration(self,Generation):

        NextGeneration = self.GeneticAlgorithmCreateEmptyGeneration()

        missing = self.G - len(Generation['order'])
        if missing>0:
            add = missing+self.I
        else:
            add = self.I
        # equally distribute new immigrants (blocked, msequence, ...)
        if not (self.n_stimuli == 6 or self.n_stimuli == 10):
            rp = [1/4.,2/4.,1/4.]
        else:
            rp = [2/4.,0,2/4.]
        r = [int(np.ceil(x*add)) for x in rp]
        r[2] = r[2]-int(np.sum(r)-add)

        # add random orders according to types
        NextGeneration = self.GeneticAlgorithmAddOrder(NextGeneration,r)

        return NextGeneration

    '''
    ####################################
    Functions specific to create designs
    ####################################
    '''

    def GeneticAlgorithmAddOrder(self,Generation,r):

        # r how many of each kind?
        nBlocked = r[0]
        nMseq = r[1]
        nRandom = r[2]

        oBlocked=[]
        tBlocked =[]
        oMseq = []
        tMseq = []
        oRandom = []
        tRandom = []

        if nBlocked>0:
            self.seed=self.seed+1
            np.random.seed(self.seed)
            iBlocked = np.random.choice(len(self.Designs['Blocked']['orders']),nBlocked,replace=True).tolist()
            oBlocked = [self.Designs['Blocked']['orders'][i] for i in iBlocked]
            tBlocked = [self.Designs['Blocked']['ITIs'][i] for i in iBlocked]
        if nMseq>0:
            self.seed=self.seed+1
            np.random.seed(self.seed)
            iMseq = np.random.choice(len(self.Designs['Mseq']['orders']),nMseq,replace=True).tolist()
            oMseq = [self.Designs['Mseq']['orders'][i] for i in iMseq]
            tMseq = [self.Designs['Mseq']['ITIs'][i] for i in iMseq]
        if nRandom>0:
            self.seed=self.seed+1
            np.random.seed(self.seed)
            iRandom = np.random.choice(len(self.Designs['Random']['orders']),nRandom,replace=True).tolist()
            oRandom = [self.Designs['Random']['orders'][i] for i in iRandom]
            tRandom = [self.Designs['Random']['ITIs'][i] for i in iRandom]

        oTotal = []
        ors = [oBlocked,oMseq,oRandom]
        for orders in ors:
            if isinstance(orders,list):
                oTotal = oTotal+orders
            else:
                oTotal.append(orders)

        tTotal = []
        trs = [tBlocked,tMseq,tRandom] if not (self.n_stimuli == 6 or self.n_stimuli == 10) else [tBlocked,tRandom]
        for itis in trs:
            if isinstance(orders,list):
                tTotal = tTotal+itis
            else:
                tTotal.append(itis)

        id = self.counter*100
        for order,ITIs in zip(oTotal,tTotal):
            id = id+1
            NewDesign = {}
            NewDesign['order'] = order
            NewDesign['ITIs'] = ITIs

            # add new designs to Generation
            Generation = self.GeneticAlgorithmAddDestoGen(Generation,NewDesign)

        return Generation

    '''
    ###############################
    Functions to compute efficiency
    ###############################
    '''

    def AddNewbiesEfficiencies(self,Population,Offspring):
        for newbies in xrange(len(Offspring['order'])):
            newDesign = {'order':Offspring['order'][newbies],'ITIs':Offspring['ITIs'][newbies]}
            newDesign = self.CreateDesignMatrix(newDesign)
            newDesign = self.ComputeEfficiency(newDesign)
            Population = self.GeneticAlgorithmAddDestoGen(Population,newDesign)

        return Population

    def CreateDesignMatrix(self,Design):
        '''
        Expand from order of stimuli to a fMRI timeseries
        Parameters
        ----------
            Design: dictionary
                Design['order']: dictionary with key 'order' generated by GenerateOrderXXX() functions or manual
                Design['ITIs']: dictionary with key 'ITIs'
        Returns
        -------
            Design: dictionary
                Design['X']: numpy array representing design matrix
                Design['Z']: numpy array representing convolved design matrix
        '''

        # ITIs to onsets
        if self.restnum>0:
            orderli = list(Design['order'])
            ITIli = list(Design['ITIs'])
            for x in np.arange(0,self.n_trials,self.restnum)[1:][::-1]:
                orderli.insert(x,"R")
                ITIli.insert(x,self.restlength)
            ITIli = np.array(ITIli)+self.stim_duration
            onsets = np.cumsum(ITIli)-ITIli[0]
            Design['onsets'] = [y for x,y in zip(orderli,onsets) if not x == "R"]
        else:
            ITIli = np.array(Design['ITIs'])+self.stim_duration
            Design['onsets'] = np.cumsum(ITIli)-ITIli[0]

        # round onsets to resolution
        onsetX = [round(x/self.resolution)*self.resolution for x in Design['onsets']]
        Design['onsets'] = onsetX

        # find indices in resolution scale of stimuli
        XindStim = [int(np.where(self.r_tp==y)[0]) for y in onsetX]

        # create design matrix in resolution scale (=deltasM in Kao toolbox)
        X_X = np.zeros([self.n_tp,self.n_stimuli])
        stim_duration_tp = int(self.stim_duration/self.resolution)
        for stimulus in xrange(self.n_stimuli):
            for dur in xrange(stim_duration_tp):
                X_X[np.array(XindStim)+dur,int(stimulus)] = [1 if z==stimulus else 0 for z in Design["order"]]

        # deconvolved matrix in resolution units
        deconvM = np.zeros([self.n_tp,int(self.laghrf*self.n_stimuli)])
        for stim in xrange(self.n_stimuli):
            for j in xrange(int(self.laghrf)):
                deconvM[j:,self.laghrf*stim+j] = X_X[:(self.n_tp-j),stim]

        # downsample to TR
        idx = [int(x) for x in np.arange(0,self.n_tp,self.TR/self.resolution)]
        Design['deconvM'] = deconvM[idx,:]
        Xwhite = np.dot(np.dot(t(Design['deconvM']),self.white),Design['deconvM'])

        # convolve design matrix
        X_Z = np.zeros([self.n_tp,self.n_stimuli])

        for stim in xrange(self.n_stimuli):
             X_Z[:,stim] = np.dot(deconvM[:,(stim*self.laghrf):((stim+1)*self.laghrf)],self.basishrf)

        if self.saturation==True:
            X_Z[X_Z>2] = 2
            X_Z[X_Z<-0.1778] = -0.1778

        # downsample to TR
        idx = [int(x) for x in np.arange(0,self.n_tp,self.TR/self.resolution)]
        X_Z = X_Z[idx,:]
        X_X = X_X[idx,:]
        Zwhite = t(X_Z)*self.white*X_Z

        Design["X"] = Xwhite
        Design["Z"] = Zwhite
        Design["Xconv"] = X_Z
        Design['Xnonconv'] = X_X
        Design["ts"] = self.r_scans

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
                Design['Ff']: optimality of probability of trials
                Design['Fc']: efficiency against psychological confounds
        '''
        Design['FeNorm'] = 0
        Design['FdNorm'] = 0
        Design['FfNorm'] = 0
        Design['FcNorm'] = 0

        if self.prerun=="Fe":
            weightsFnc = [1,0,0,0]
        elif self.prerun=="Fd":
            weightsFnc = [0,1,0,0]
        else:
            weightsFnc = self.weights

        if weightsFnc[0]>0:
            Design = self.FeCalc(Design)
            if self.prerun=="Fe":
                Design['FeNorm']=Design['Fe']
            else:
                Design['FeNorm']=Design['Fe']/self.FeMax
        if weightsFnc[1]>0:
            Design = self.FdCalc(Design)
            if self.prerun=="Fd":
                Design['FdNorm']=Design['Fd']
            else:
                Design['FdNorm']=Design['Fd']/self.FeMax
            Design['FdNorm']=Design['Fd']/self.FdMax
        if weightsFnc[2]>0:
            Design = self.FfCalc(Design)
            Design['FfNorm']=1-Design['Ff']/self.FfMax
        if weightsFnc[3]>0:
            Design = self.FcCalc(Design)
            Design['FcNorm']=1-Design['Fc']/self.FcMax

        Design['F'] = np.sum(weightsFnc * np.array([Design['FeNorm'],Design['FdNorm'],Design['FfNorm'],Design['FcNorm']]))

        return Design

    def FeCalc(self,Design):
        try:
            invM = scipy.linalg.inv(Design['X'])
        except scipy.linalg.LinAlgError:
            invM  = scipy.linalg.pinv(Design['X'])
        invM = np.array(invM)
        st1 = np.dot(self.CX,invM)
        CMC = np.dot(st1,t(self.CX))
        if self.Aoptimality == True:
            Design["Fe"] = float(self.CX.shape[0]/np.matrix.trace(CMC))
        else:
            Design["Fe"] = float(np.linalg.det(CMC)**(-1/self.n_cons))
        return Design

    def FdCalc(self,Design):
        try:
            invM = scipy.linalg.inv(Design['Z'])
        except scipy.linalg.LinAlgError:
            invM = scipy.linalg.pinv(Design['Z'])
        invM = np.array(invM)
        CMC = np.matrix(self.C)*invM*np.matrix(t(self.C))
        if self.Aoptimality == True:
            Design["Fd"] = float(self.C.shape[0]/np.matrix.trace(CMC))
        else:
            Design["Fd"] = float(np.linalg.det(CMC)**(-1/self.n_cons))
        return Design

    def FcCalc(self,Design):
        Q = np.zeros([self.n_stimuli,self.n_stimuli,self.ConfoundOrder])
        for n in xrange(self.n_trials):
            for r in np.arange(1,self.ConfoundOrder+1):
                if n>(r-1):
                    Q[Design['order'][n],Design['order'][n-r],r-1] += 1
        Qexp = np.zeros([self.n_stimuli,self.n_stimuli,self.ConfoundOrder])
        for si in xrange(self.n_stimuli):
            for sj in xrange(self.n_stimuli):
                for r in np.arange(1,self.ConfoundOrder+1):
                    Qexp[si,sj,r-1] = self.P[si]*self.P[sj]*(self.n_trials-r+1)
        Qmatch = np.sum(abs(Q-Qexp))
        Design["Fc"] = Qmatch
        return Design

    def FfCalc(self,Design):
        trialcount = Counter(Design['order'])
        Pobs = [trialcount[x] for x in xrange(self.n_stimuli)]
        Design["Ff"] = np.sum(abs(np.array(Pobs)-np.array(self.n_trials*np.array(self.P))))
        return Design

    def smpl_ITI(self):
        if self.ITImodel == "fixed":
            smp = [self.ITIfixed]*self.n_trials
        elif self.ITImodel == "uniform":
            maxsmpdur = self.duration_norest-self.ITIunifmin-self.n_trials*self.stim_duration
            success = 0
            while success == 0:
                self.seed=self.seed+1
                np.random.seed(self.seed)
                smp = np.random.uniform(self.ITIunifmin,self.ITIunifmax,self.n_trials)
                if np.sum(smp[1:])<maxsmpdur:
                    success = 1
        elif self.ITImodel == "truncated exponential":
            maxsmpdur = self.duration_norest-self.ITItruncmin-self.n_trials*self.stim_duration
            success = 0
            while success == 0:
                smp = self.rtexp(self.n_trials,self.lam,self.ITItruncmin,self.ITItruncmax)
                if np.sum(smp[1:])<maxsmpdur:
                    success = 1
        return smp

    def itexp(self,x,lam,trunc):
        i = -np.log(1-x*(1-np.exp(-trunc*lam)))/lam
        return i

    def rtexp(self,n,lam,min,max):
        trunc = max-min
        self.seed=self.seed+1
        np.random.seed(self.seed)
        r = self.itexp(np.random.uniform(0,1,n),lam,trunc) + min
        return r

    def etexp(self,lam,min,max,mean):
        trunc = max-min
        exp = 1/lam-trunc*(np.exp(lam*trunc)-1)**(-1)+min
        return exp

    def diftexp(self,lam,min,max,mean):
        exp = self.etexp(lam,min,max,mean)
        return((exp-mean)**2)

    def printcmd(self):
        self.cmd = "ITImodel = '{0}', \n" \
        "ITIfixed = {1}, \n" \
        "ITIunifmin = {2}, \n" \
        "ITIunifmax = {3}, \n" \
        "ITItruncmin = {4}, \n" \
        "ITItruncmax = {5}, \n" \
        "ITItruncmean = {6}, \n" \
        "TR = {7}, \n" \
        "n_trials = {8}, \n" \
        "duration = {9}, \n" \
        "n_cons = {10}, \n" \
        "n_stimuli = {11}, \n" \
        "stim_duration = {12}, \n" \
        "P = {13}, \n" \
        "C = {14}, \n" \
        "rho = {15}, \n" \
        "restnum = {16}, \n" \
        "restlength = {17}, \n"\
        "Aoptimality = {18}, \n" \
        "saturation = {19}, \n" \
        "resolution = {20}, \n" \
        "weights = {21}, \n" \
        "G = {22}, \n" \
        "q = {23}, \n" \
        "I = {24}, \n" \
        "cycles = {25}, \n" \
        "ConfoundOrder = {26}, \n" \
        "preruncycles = {27}, \n" \
        "maxrepeat = {28}, \n" \
        "HardProb = {29}, \n" \
        "tapsfile = {30}, \n" \
        "prerun = {31}, \n" \
        "convergence = {32}, \n" \
        "seed = {33} \n".format(
            self.ITImodel,
            self.ITIfixed,
            self.ITIunifmin,
            self.ITIunifmax,
            self.ITItruncmin,
            self.ITItruncmax,
            self.ITItruncmean,
            self.TR,
            self.n_trials,
            self.duration,
            self.n_cons,
            self.n_stimuli,
            self.stim_duration,
            self.P,
            self.C,
            self.rho,
            self.restnum,
            self.restlength,
            self.Aoptimality,
            self.saturation,
            self.resolution,
            self.weights,
            self.G,
            self.q,
            self.I,
            self.cycles,
            self.ConfoundOrder,
            self.preruncycles,
            self.maxrepeat,
            self.HardProb,
            self.tapsfile,
            self.prerun,
            self.convergence,
            self.seed
        )

        return self

    @staticmethod
    def drift(s,deg=3):
        S = np.ones([deg,len(s)])
        s = np.array(s)
        tmpt = np.array(2.*s/float(len(s)-1)-1)
        S[1] = tmpt
        for k in np.arange(2,deg):
            S[k] = ((2.*k-1.)/k)*tmpt*S[k-1] - ((k-1)/float(k))*S[k-2]
        return S

    @staticmethod
    def spm_Gpdf(s,h,l):
        s = np.array(s)
        res = (h-1)*np.log(s) + h*np.log(l) - l*s - np.log(gamma(h))
        return np.exp(res)

    def prepare_download(self):
        OptInd = np.min(np.arange(len(self.Generation['F']))[
                        self.Generation['F'] == np.max(self.Generation['F'])])

        orders = self.Generation['order'][OptInd]
        onsets = self.Generation['onsets'][OptInd]
        itis = self.Generation['ITIs'][OptInd]

        # if path already exist: remove
        if os.path.exists(self.folder):
            shutil.rmtree(self.folder)
        os.mkdir(self.folder)

        # write onset files
        stimuli = len(np.unique(orders))
        filenames = [os.path.join(
            self.folder, "stimulus_" + str(stim) + ".txt") for stim in range(self.n_stimuli)]
        for stim in range(self.n_stimuli):
            onsubsets = [str(x) for x in np.array(
                onsets)[np.array(orders) == stim]]
            f = open(filenames[stim], 'w+')
            for line in onsubsets:
                f.write(line)
                f.write("\n")
            f.close()
        itifile = os.path.join(self.folder,"itis.txt")
        f = open(itifile, 'w+')
        for line in itis:
            f.write(str(line))
            f.write("\n")
        f.close()


        # combine in zipfile
        zip_subdir = "OptimalDesign"
        zip_filename = "%s.zip" % zip_subdir
        file = StringIO.StringIO()
        zf = zipfile.ZipFile(file, "w")
        for fpath in filenames+[itifile]:
            fdir, fname = os.path.split(fpath)
            zip_path = os.path.join(zip_subdir, fname)
            zf.write(fpath, zip_path)
        zf.close()

        return({"file":file, "zipfile":zip_filename})
