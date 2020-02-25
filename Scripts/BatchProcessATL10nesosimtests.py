""" BatchProcessATL10.py
	
	Processing sea ice thickness with ICESat-2 freeboards
	Initial code written by Alek Petty (01/06/2019)
	
	Input:
		ICESat-2 freeboards, NESOSIM snow depths/densities, OSISAF ice type

	Output:
		Ice thickness using various snow depth assumptions.

	Python dependencies:
		See below for the relevant module imports. Of note:
		xarray/pandas
		netCDF4
		matplotlib
		basemap

	GSFC: W99mod5 snow depth/density, 915 kg/m3 ice density
	CPOM: regional mean W99mod5, 882, 917 kg/m3 ice density
	JPL: W99mod5 (bus using ice type fraction), 
	AWI: W99mod5, 882, 917 kg/m3 ice density
	Petty: NESOSIM distributed, 899 MYI, 916 

		More information on installation is given in the README file.

	Update history:
		01/06/2019: Version 1.
    
"""

import matplotlib, sys
matplotlib.use('Agg')
from mpl_toolkits.basemap import Basemap
import numpy as np
from pylab import *
import numpy.ma as ma
import xarray as xr
import pandas as pd
import os
from glob import glob
import netCDF4 as nc4
from scipy.interpolate import griddata
from netCDF4 import Dataset
import time
import common_functions as cF

from itertools import repeat, product
import concurrent.futures


def main(fileT, beamNum):
	""" Main ICESat-2 processing module 
	
	Convert the ATL10 shot freeboard data to ice thickness using various snow loading input estimates
	
	
	Args:
		fileT (str): the ATL10 file path
		beamNum (int): ATLAS beam number from 1 to 6

	"""

	#====================== Configuration ========================

	regionflags=1
	icetype=1
	warrensnow=1
	modwarrensnow5=1

	nesosim=1
	nesosim2=1
	nesosim3=1
	nesosim4=1
	nesosim5=1
	nesosim6=1
	nesosimdisttributed=1

	savedata=0
	saveNetCDFX=1
	
	
	# Map projection
	mapProj = Basemap(projection='npstere',boundinglat=55,lon_0=0, resolution='l' , round=False)

	# Get freeboard files
	start = time.time()
	print ('Grabbing freeboard data...')
	dF, fileStr = cF.getATL10FreeboardShotData(fileT, mapProj, beamNum=beamNum)
	
	if isinstance(dF, pd.DataFrame):
		print('Good file') 
	else:
		# Bad file so skip
		print('Bad file')
		return

	if (dF.shape[0]<10):
		# If file had no good freeboard data break
		print('Not enough data in file', dF.count)
		return
	
	print ('Got good ATL10 freeboard data in '+str(np.round((time.time()-start), 2))+' seconds')
	beamStr=dF['beamStr'].iloc[0]
	print('beam:', beamStr)
	# ----- Region flags -------
	if (regionflags==1):
		print ('Assign NSIDC region mask...')
		dF=cF.assignRegionMask(dF, mapProj, ancDataPath=ancDataPath)
		#print(dF.head(3)) 
		print ('Complete')

	
	# ----- Get colocated ice type data -------
	if (icetype==1):
		start = time.time()
		print ('Processing ice type data...')
		dF = cF.getIceType(dF, iceTypePath, mapProj, res=4, returnRaw=0)
		print ('Processed ice type in '+str(np.round((time.time()-start), 2))+' seconds')
		#dF.head(3)
	
	#------- Get Warren snow depths -----------
	if (warrensnow==1):
		start = time.time()
		print ('Processing Warren snow depths...')
		dF = cF.getWarrenData(dF, outSnowVar='snow_depth_W99', outDensityVar='snow_density_W99')
		print ('Processed Warren snow depths in '+str(np.round((time.time()-start), 2))+' seconds')
		#dF.head(3)
	
	#------- Get modified (50%) Warren snow depths -----------
	if (modwarrensnow5==1):
		start = time.time()
		print ('Processing Warren mod5 snow depths...')
		dF = cF.getWarrenData(dF, outSnowVar='snow_depth_W99mod5', outDensityVar='None', modFactor=0.5)
		print ('Processed Warren snow depths in '+str(np.round((time.time()-start), 2))+' seconds')
		#dF.head(3)
	


	#------- Get NESOSIM snow depths -----------
	if (nesosim==1):
		# ----- Get dates and coincident NESOSIM file -------
		print ('Grabbing NESOSIM file and dates...')
		dateStr= cF.getDate(dF['year'].iloc[0], dF['month'].iloc[0], dF['day'].iloc[0])
		fileNESOSIM, dateStr = cF.getNesosimDates(dF, snowPath)
		dF = cF.gridNESOSIMtoFreeboard(dF, mapProj, fileNESOSIM, dateStr, outSnowVar='snow_depth_N', outDensityVar='snow_density_N')

	
	if (nesosim2==1):
		# ----- Get dates and coincident NESOSIM file -------
		print ('Grabbing NESOSIM file and dates...')
		dateStr= cF.getDate(dF['year'].iloc[0], dF['month'].iloc[0], dF['day'].iloc[0])
		fileNESOSIM, dateStr = cF.getNesosimDates(dF, snowPath2)
		dF = cF.gridNESOSIMtoFreeboard(dF, mapProj, fileNESOSIM, dateStr, outSnowVar='snow_depth_Nera5', outDensityVar='snow_density_Nera5')
		
		#dF.head(3)

	if (nesosim3==1):
		# ----- Get dates and coincident NESOSIM file -------
		print ('Grabbing NESOSIM file and dates...')
		dateStr= cF.getDate(dF['year'].iloc[0], dF['month'].iloc[0], dF['day'].iloc[0])
		fileNESOSIM, dateStr = cF.getNesosimDates(dF, snowPath3)
		dF = cF.gridNESOSIMtoFreeboard(dF, mapProj, fileNESOSIM, dateStr, outSnowVar='snow_depth_Nerai_s', outDensityVar='snow_density_Nerai_s')


	if (nesosim4==1):
		# ----- Get dates and coincident NESOSIM file -------
		print ('Grabbing NESOSIM file and dates...')
		dateStr= cF.getDate(dF['year'].iloc[0], dF['month'].iloc[0], dF['day'].iloc[0])
		fileNESOSIM, dateStr = cF.getNesosimDates(dF, snowPath4)
		dF = cF.gridNESOSIMtoFreeboard(dF, mapProj, fileNESOSIM, dateStr, outSnowVar='snow_depth_Nera5_s', outDensityVar='snow_density_Nera5_s')

	if (nesosim5==1):
		# ----- Get dates and coincident NESOSIM file -------
		print ('Grabbing NESOSIM file and dates...')
		dateStr= cF.getDate(dF['year'].iloc[0], dF['month'].iloc[0], dF['day'].iloc[0])
		fileNESOSIM, dateStr = cF.getNesosimDates(dF, snowPath5)
		dF = cF.gridNESOSIMtoFreeboard(dF, mapProj, fileNESOSIM, dateStr, outSnowVar='snow_depth_Nera5_s2', outDensityVar='snow_density_Nera5_s2')


	if (nesosim6==1):
		# ----- Get dates and coincident NESOSIM file -------
		print ('Grabbing NESOSIM file and dates...')
		dateStr= cF.getDate(dF['year'].iloc[0], dF['month'].iloc[0], dF['day'].iloc[0])
		fileNESOSIM, dateStr = cF.getNesosimDates(dF, snowPath6)
		dF = cF.gridNESOSIMtoFreeboard(dF, mapProj, fileNESOSIM, dateStr, outSnowVar='snow_depth_Nera5_s3', outDensityVar='snow_density_Nera5_s3')




	#------- Get distributed NESOSIM snow depths -----------

	if (nesosimdisttributed==1):
		start = time.time()
		print ('Processing distributed NESOSIM snow depths...')
		dF = cF.distributeSnow(dF, inputSnowDepth='snow_depth_N', outSnowVar='snow_depth_NPdist', consIterations=11, gridSize=100000)

		dF = cF.distributeSnow(dF, inputSnowDepth='snow_depth_Nera5', outSnowVar='snow_depth_Nera5Pdist', consIterations=11, gridSize=100000)

		dF = cF.distributeSnow(dF, inputSnowDepth='snow_depth_Nerai_s', outSnowVar='snow_depth_Nerai_sPdist', consIterations=11, gridSize=100000)

		dF = cF.distributeSnow(dF, inputSnowDepth='snow_depth_Nera5_s', outSnowVar='snow_depth_Nera5_sPdist', consIterations=11, gridSize=100000)

		dF = cF.distributeSnow(dF, inputSnowDepth='snow_depth_Nera5_s2', outSnowVar='snow_depth_Nera5_sPdist2', consIterations=11, gridSize=100000)

		dF = cF.distributeSnow(dF, inputSnowDepth='snow_depth_Nera5_s3', outSnowVar='snow_depth_Nera5_sPdist3', consIterations=11, gridSize=100000)

		print ('Processed distributed NESOSIM snow depths in '+str(np.round((time.time()-start), 2))+' seconds')

		
	#-------Thickness conversion-----------
	print ('Processing thickness conversions...')
	if (warrensnow==1):
		# Convert freeboard to thickness using Warren data
		dF = cF.getSnowandConverttoThickness(dF, snowDepthVar='snow_depth_W99', snowDensityVar='snow_density_W99', outVar='ice_thickness_W99', rhoi=1)

	if (modwarrensnow5==1):	
		# Convert freeboard to thickness using modified Warren data
		dF = cF.getSnowandConverttoThickness(dF, snowDepthVar='snow_depth_W99mod5', snowDensityVar='snow_density_W99', outVar='ice_thickness_W99mod5', rhoi=1)
		#dF.head(3)


	if (nesosim==1):
		# Convert freeboard to thickness using NESOSIM data
		dF = cF.getSnowandConverttoThickness(dF, snowDepthVar='snow_depth_N', snowDensityVar='snow_density_N', outVar='ice_thickness_N', rhoi=1)

	if (nesosimdisttributed==1):
		# Convert freeboard to thickness using distributed NESOSIM data
		dF = cF.getSnowandConverttoThickness(dF, snowDepthVar='snow_depth_NPdist', snowDensityVar='snow_density_N', outVar='ice_thickness_NPdist', rhoi=1)
		dF = cF.getSnowandConverttoThickness(dF, snowDepthVar='snow_depth_Nera5Pdist', snowDensityVar='snow_density_Nera5', outVar='ice_thickness_Nera5Pdist', rhoi=1)
		dF = cF.getSnowandConverttoThickness(dF, snowDepthVar='snow_depth_Nerai_sPdist', snowDensityVar='snow_density_Nerai_s', outVar='ice_thickness_Nerai_sPdist', rhoi=1)
		dF = cF.getSnowandConverttoThickness(dF, snowDepthVar='snow_depth_Nera5_sPdist', snowDensityVar='snow_density_Nera5_s', outVar='ice_thickness_Nera5_sPdist', rhoi=1)
		dF = cF.getSnowandConverttoThickness(dF, snowDepthVar='snow_depth_Nera5_sPdist2', snowDensityVar='snow_density_Nera5_s2', outVar='ice_thickness_Nera5_sPdist2', rhoi=1)
		dF = cF.getSnowandConverttoThickness(dF, snowDepthVar='snow_depth_Nera5_sPdist3', snowDensityVar='snow_density_Nera5_s3', outVar='ice_thickness_Nera5_sPdist3', rhoi=1)

	print ('Processed thickness conversions')
	#-------Uncertainty calculation-----------
	

	#-------Diagnostic plots-----------
	#cF.plotMap4(dF, mapProj, figPath, dateStr+'_F'+str(fileNum)+'W99shot', vars=['freeboard', 'snowDepthW99', 'snowDensityW99', 'iceThicknessW99'])
	#cF.plotMap4(dF, mapProj, figPath, dateStr+'_F'+str(fileNum)+'W99mod', vars=['freeboard', 'snowDepthW99mod5', 'snowDensityW99mod5', 'iceThicknessW99mod5'])
	#cF.plotMap4(dF, mapProj, figPath, dateStr+'_F'+str(fileNum)+'W99mod', vars=['freeboard', 'snowDepthW99mod7', 'snowDensityW99mod7', 'iceThicknessW99mod7'])
	#cF.plotMap4(dF, mapProj, figPath, dateStr+'_F'+str(fileNum)+'Nshot', vars=['freeboard', 'snowDepthN', 'snowDensityN', 'iceThicknessN'])
	#cF.plotMap4(dF, mapProj, figPath, dateStr+'_F'+str(fileNum)+'NPdistshot', vars=['freeboard', 'snowDepthNPdist', 'snowDensityN', 'iceThicknessNPdist'])
	#cF.plotMap4(dF, mapProj, figPath, dateStr+'_F'+str(fileNum)+'Ndist', vars=['freeboard', 'snowDepthNdist', 'snowDensityN', 'iceThicknessNdist'])
	#plotMap4(dF, mapProj, figPath, dateStr+'_F'+str(fileNum)+'NKdist', vars=['freeboard', 'snowDepthNKdist', 'snowDensityNK', 'iceThicknessNKdist'])

	#-------Output-----------
	if (savedata==1):
		outStr=fileT.split("/")[-1][:-3]
		print ('Saving data file to:', dataOutPath+'IS2'+outStr+'_bnum'+str(beamNum)+beamStr)
		dF.to_pickle(dataOutPath+'IS2'+outStr+'_bnum'+str(beamNum)+beamStr)
		print ('Saved data')
	if (saveNetCDFX==1):
		outStr=fileT.split("/")[-1][:-3]
		print ('Saving netCDF (xarray) data file to:', dataOutPath+'IS2'+outStr+'_bnum'+str(beamNum)+beamStr)
		dFX=xr.Dataset.from_dataframe(dF)

		dFX.to_netcdf(dataOutPath+'IS2'+outStr+'_bnum'+str(beamNum)+beamStr+'.nc')

if __name__ == '__main__':
	
	iceTypePath='/cooler/scratch1/aapetty/Data/ICETYPE/OSISAF/'
	snowPath='/cooler/scratch1/aapetty/Data/NESOSIM/OSISAFsig150_ERAI_sf_SICCDR_Rhovariable_IC4_DYN1_WP1_LL1_WPF5.8e-07_WPT5_LLF2.9e-07-100kmnrt4v2/final/'
	
	snowPath2='/cooler/scratch1/aapetty/Data/NESOSIM/OSISAFsig150_ERA5_sf_SICCDR_Rhovariable_IC4_DYN1_WP1_LL1_WPF5.8e-07_WPT5_LLF2.9e-07-100kmnrtICv2/'
	snowPath3='/cooler/scratch1/aapetty/Data/NESOSIM/scaled_regional_lin_OSISAFsig150_ERAI_sf_SICCDR_Rhovariable_IC4_DYN1_WP1_LL1_WPF5.8e-07_WPT5_LLF2.9e-07-100kmnrtICv2/'
	snowPath4='/cooler/scratch1/aapetty/Data/NESOSIM/scaled_regional_lin_OSISAFsig150_ERA5_sf_SICCDR_Rhovariable_IC4_DYN1_WP1_LL1_WPF5.8e-07_WPT5_LLF2.9e-07-100kmnrtICv2/'
	snowPath5='/cooler/scratch1/aapetty/Data/NESOSIM/scaled_regional_lin_OSISAFsig150_ERA5_sf_SICCDR_Rhovariable_IC4_DYN1_WP1_LL1_WPF5.8e-07_WPT5_LLF5.8e-07-100kmnrtICv2/final/'
	snowPath6='/cooler/scratch1/aapetty/Data/NESOSIM/scaled_regional_lin_OSISAFsig150_ERA5_sf_SICCDR_Rhovariable_IC4_DYN1_WP1_LL1_WPF5.8e-07_WPT5_LLF1.16e-06-100kmnrtICv2/final/'

	dataOutPathM='/cooler/scratch1/aapetty/DataOutput/IS2/'
	figPathM='/cooler/scratch1/aapetty/Figures/IS2/'
	ancDataPath='../AncData/'
	
	releaseStr='rel002'
	runStr='runAC'

	ATL10path='/cooler/I2-ASAS/'+releaseStr+'/ATL10-01/'

	# ATL10 dates to process
	dateStr='201904' 

	global figPath, dataOutPath
	figPath=figPathM+releaseStr+'/'+runStr+'/'
	dataOutPath=dataOutPathM+releaseStr+'/'+runStr+'/raw/'
	if not os.path.exists(dataOutPath):
		os.makedirs(dataOutPath)
	if not os.path.exists(figPath):
		os.makedirs(figPath)
	
	#The -01 is for Northern Hemisphere datafiles (-02 is for Southern Hemisphere)
	ATL10files = glob(ATL10path+'/ATL10-01_'+dateStr+'*.h5')
	print('ATL10 files:', ATL10path+'/ATL10-01_'+dateStr+'*.h5')
	print('ATL10 release:',releaseStr)
	print('Processing run:',runStr)
	print('Number of ATL10 files: '+str(size(ATL10files)))
	print(ATL10files)


	beamNums=[1, 2, 3, 4, 5, 6]

	# If you don't want to use concurrent futures and just run over one cpu then use this code
	#for ATL10file in ATL10files:
	#	main(ATL10file, beamNums[0])
	
	with concurrent.futures.ProcessPoolExecutor(max_workers=10) as executor:

		# args=((campaign, beam) for beam in beams)
		# print(args)
		# itertools.repeat to add a fixed argument
		# Not very elegant but whatever..d
		result1=executor.map(main, ATL10files, repeat(beamNums[0]))
		#result2=executor.map(main, ATL10files, repeat(beamNums[2]))
		#result3=executor.map(main, ATL10files, repeat(beamNums[4]))
		#result4=executor.map(main, ATL10files, repeat(beamNums[1]))
		#result5=executor.map(main, ATL10files, repeat(beamNums[3]))
		#result6=executor.map(main, ATL10files, repeat(beamNums[5]))
		
		#result4=executor.map(main, ATL10files, repeat(beamNums[3]))
		#result5=executor.map(main, ATL10files, repeat(beamNums[4]))
		#result6=executor.map(main, ATL10files, repeat(beamNums[5]))
	
	#end = time.time()
	#campaignTime = end-start
	#campaignTimestr=str(np.round(campaignTime/(60.), 2))
	#print ('Proceesing time (minutes): '+campaignTimestr)







