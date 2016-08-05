#!/usr/bin/python2.7
#
# Author: Joke Durnez
#
# Description: Generate m sequences
#
# Loosely translated from http://fmriserver.ucsd.edu/ttliu
#
# Version: 1
#
# Date: 2016-07-13
#
#===========================================================

from __future__ import division
import numpy as np
import math
import pickle
import os
import sys

class Msequence(object):
    '''
    A class for an order of experimental trials

    Parameters
    ----------
        stimtypeno: integer
                    number of different stimulus types
    '''

    def GenMseq(self,mLen,stimtypeno):
        '''
        Function specific to generate a maximum number of msequences for genetic algorithm.

        Parameters
        ----------
            mLen: integer
                desired length of sequence
            stimtypeno: integer or 'random'
                number of stimulus types
        '''

        self.mLen = mLen
        self.stimtypeno = stimtypeno

        # read in taps file and count
        tapsfile = "/Users/Joke/Documents/Onderzoek/ProjectsOngoing/DesignEfficiency/design_core/design/taps.p"
        self.taps = pickle.load(open(tapsfile))

        # initate baseVal
        baseVal = self.stimtypeno

        # initiate powerVal
        minpow = math.log(mLen+1,baseVal)
        pos = self.taps[baseVal].keys()
        orders = []

        if baseVal == 2:
            # restrict number of possibilities for time constraints,
            # could be lift if analyses are done on HPC
            # still results in 160 msequences...
            pos = pos[:10]

        for powerVal in pos:
            # which sequences are possible
            seqKeys = self.taps[baseVal][powerVal].keys()

            # generate msequence
            for keys in seqKeys:
                shift = 0
                ms = self.Mseq(baseVal,powerVal,shift,keys)
                if mLen > len(ms):
                    rep = np.ceil(mLen/len(ms))
                    ms = np.tile(ms,rep)
                if not mLen%len(ms) == 0:
                    ms = ms[:mLen]
                ms = [int(x) for x in ms]
                orders.append(ms)

        self.orders = orders
        return self

    def Mseq(self,baseVal,powerVal,shift=None,whichSeq=None,userTaps=None):
        '''
        Function to generate msequences

        Parameters
        ----------
            powerVal: integer or 'random'
                the power of the msequence
            baseVal: integer
                the base value of the msequence
                (equal to the number of stimuli)
            shift: integer or 'random'
                shift of the m-sequence
            whichSeq: integer
                index of the sequence desired in the taps file
            userTaps: list
                if user wants to specify own polynomial taps
        '''

        # compute total length
        bitNum = int(baseVal**powerVal-1)

        # initiate register and msequence
        register = np.ones(powerVal)
        ms = np.zeros(bitNum)

        # select possible taps
        print(self)
        tap = self.taps[baseVal][powerVal]

        # if sequence is not given or false : random
        if (not whichSeq) or (whichSeq > len(tap) or whichSeq < 1):
            if whichSeq:
                print("You've asked a non-existing tap ! Generating at random.")
            whichSeq = math.ceil(np.random.uniform(0,1,1)*len(tap))-1

        # generate weights

        if userTaps:
            weights = userTaps
        else:
            weights = np.zeros(powerVal)
            if baseVal == 2:
                tapindex = [x-1 for x in tap[int(whichSeq)]]
                weights[tapindex] = 1
            elif baseVal > 2:
                weights = tap[int(whichSeq)]
            else:
                print("You want at least 2 different stimulus types right? Now you asked for %s"%baseVal)

        # generate msequence
        for i in range(bitNum):
            if baseVal == 4 or baseVal == 8 or baseVal == 9:
                tmp = 0
                for ind in range(len(weights)):
                    tmp = self.qadd(tmp,self.qmult(int(weights[ind]),int(register[ind]),baseVal),baseVal)
                ms[i] = tmp
            else:
                ms[i] = (np.dot(weights,register)+baseVal) % baseVal
            reg_shft = [x for ind,x in enumerate(register) if ind in range(powerVal-1)]
            register=[ms[i]]+reg_shft

        #shift
        if shift == 'random':
            shift = math.ceil(np.random.uniform(0,1,1)*bitNum)-1

        elif shift:
            shift = shift%len(ms)
            ms = np.append(ms[shift:],ms[:shift])

        return ms

    @staticmethod
    def qadd(a,b,base):

        if (a >= base or b >= base):
            print('qadd(a,b), a and b must be < %s'%(base))

        if base == 4:
            amat = np.array([
                [0,1,2,3],
            	[1,0,3,2],
            	[2,3,0,1],
            	[3,2,1,0],
            ])
        elif base == 8:
            amat = np.array([
                [0,1,2,3,4,5,6,7],
                [1,0,3,2,5,4,7,6],
                [2,3,0,1,6,7,4,5],
                [3,2,1,0,7,6,5,4],
                [4,5,6,7,0,1,2,3],
                [5,4,7,6,1,0,3,2],
                [6,7,4,5,2,3,0,1],
                [7,6,5,4,3,2,1,0]
            ])
        elif base == 9:
            amat = np.array([
                [0,1,2,3,4,5,6,7,8],
                [1,2,0,4,5,3,7,8,6],
                [2,0,1,5,3,4,8,6,7],
                [3,4,5,6,7,8,0,1,2],
                [4,5,3,7,8,6,1,2,0],
                [5,3,4,8,6,7,2,0,1],
                [6,7,8,0,1,2,3,4,5],
                [7,8,6,1,2,0,4,5,3],
                [8,6,7,2,0,1,5,3,4]
            ])
        else:
            print('qadd base %s not supported yet'%base)

        y = amat[a,b]
        return y

    @staticmethod
    def qmult(a,b,base):

        if (a >= base or b >= base):
            print('qadd(a,b), a and b must be < %s'%(base))

        if base == 4:
            amult = np.array([
                [0,0,0,0],
                [0,1,2,3],
                [0,2,3,1],
                [0,3,1,2]
            ])
        elif base == 8:
            amult = np.array([
                [0,0,0,0,0,0,0,0],
                [0,1,2,3,4,5,6,7],
                [0,2,4,6,5,7,1,3],
                [0,3,6,5,1,2,7,4],
                [0,4,5,1,7,3,2,6],
                [0,5,7,2,3,6,4,1],
                [0,6,1,7,2,4,3,5],
                [0,7,3,4,6,1,5,2]
            ])
        elif base == 9:
            amult = np.array([
                [0,0,0,0,0,0,0,0,0],
                [0,1,2,3,4,5,6,7,8],
                [0,2,1,6,8,7,3,5,4],
                [0,3,6,4,7,1,8,2,5],
                [0,4,8,7,2,3,5,6,1],
                [0,5,7,1,3,8,2,4,6],
                [0,6,3,8,5,2,4,1,7],
                [0,7,5,2,6,4,1,8,3],
                [0,8,4,5,1,6,7,3,2]
        ])
        else:
            print('qmult base %s not supported yet'%base)

        y = amult[a,b]
        return y
