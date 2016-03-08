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
	shape = spm.shape
	spm = None
	# initiate variables
	x = []
	y = []
	z = []
	val = []
	# check for each voxel whether it's a peak, if it is, add to table
	for m in xrange(1,shape[0]+1):
		for n in xrange(1,shape[1]+1):
			for o in xrange(1,shape[2]+1):
				if spm_ext[m,n,o]>exc:
					surroundings = [spm_ext[m-1,n-1,o-1],
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
						x.append(m-1)
						y.append(n-1)
						z.append(o-1)
						val.append(spm_ext[m,n,o])
					del surroundings
	del spm_ext
	# initate table
	labels=['x','y','z','peak']
	d = {'x':x,
		'y':y,
		'z':z,
		'peak':val}
	peaks = pd.DataFrame(data=d)

	peaks = peaks.set_index([range(len(peaks))])
	return peaks
