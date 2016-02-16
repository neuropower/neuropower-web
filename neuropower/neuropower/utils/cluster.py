import nibabel as nib
import numpy as np
import pandas as pd

"""
Extract local maxima from a spm, return a pandas table with variables:
- x coordinate
- y coordinate
- z coordinate
- peak height
"""

def cluster(spm,exc):
	# make a new array with an extra row/column/plane around the original array
	spm_newdim = tuple(map(lambda x: x+2,spm.shape))
	spm_ext = np.zeros((spm_newdim))
	spm_ext.fill(-100)
	spm_ext[1:(spm.shape[0]+1),1:(spm.shape[1]+1),1:(spm.shape[2]+1)] = spm
	# initate table
	labels=['x','y','z','peak']
	peaks = pd.DataFrame(columns=labels)
	# check for each voxel whether it's a peak, if it is, add to table
	for m in range(1,spm.shape[0]+1):
		for n in range(1,spm.shape[1]+1):
			for o in range(1,spm.shape[2]+1):
				if spm_ext[m,n,o]>exc:
					surroundings=[spm_ext[m-1,n-1,o-1],
					spm_ext[m-1,n-1,o],
					spm_ext[m-1,n-1,o+1],
					spm_ext[m-1,n,o-1],
					spm_ext[m-1,n,o],
					spm_ext[m-1,n,o+1],
					spm_ext[m-1,n+1,o-1],
					spm_ext[m-1,n+1,o],
					spm_ext[m-1,n+1,o+1],
					spm_ext[m,n-1,o-1],
					spm_ext[m,n-1,o],
					spm_ext[m,n-1,o+1],
					spm_ext[m,n,o-1],
					spm_ext[m,n,o+1],
					spm_ext[m,n+1,o-1],
					spm_ext[m,n+1,o],
					spm_ext[m,n+1,o+1],
					spm_ext[m+1,n-1,o-1],
					spm_ext[m+1,n-1,o],
					spm_ext[m+1,n-1,o+1],
					spm_ext[m+1,n,o-1],
					spm_ext[m+1,n,o],
					spm_ext[m+1,n,o+1],
					spm_ext[m+1,n+1,o-1],
					spm_ext[m+1,n+1,o],
					spm_ext[m+1,n+1,o+1]]
					if spm_ext[m,n,o] > np.max(surroundings):
						res =pd.DataFrame(data=[[m-1,n-1,o-1,spm_ext[m,n,o]]],columns=labels)
						peaks=peaks.append(res)
	peaks = peaks.set_index([range(len(peaks))])
	return peaks
