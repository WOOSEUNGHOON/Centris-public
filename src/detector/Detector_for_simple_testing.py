
"""
Dataset Collection Tool.
Author:		Seunghoon Woo (seunghoonwoo@korea.ac.kr)
Modified: 	December 16, 2020.
"""

import os
import sys
sys.path.insert(0, "../osscollector")
import OSS_Collector
import re
import shutil
import json

"""GLOBALS"""
currentPath		= os.getcwd()
theta			= 0.1
resultPath		= currentPath + "/res/"
finalDBPath		= "./componentDB/"
aveFuncPath		= "./aveFuncs"

shouldMake 	= [resultPath]
for eachRepo in shouldMake:
	if not os.path.isdir(eachRepo):
		os.mkdir(eachRepo)



def getAveFuncs():
	aveFuncs = {}
	with open(aveFuncPath, 'r', encoding = "UTF-8") as fp:
		aveFuncs = json.load(fp)
	return aveFuncs


def readComponentDB():
	componentDB = {}
	jsonLst 	= []

	for OSS in os.listdir(finalDBPath):
		componentDB[OSS] = []
		with open(finalDBPath + OSS, 'r', encoding = "UTF-8") as fp:
			jsonLst = json.load(fp)

			for eachHash in jsonLst:
				hashval = eachHash["hash"]
				componentDB[OSS].append(hashval)

	return componentDB


def detector(inputDict, inputRepo):
	componentDB 	= {}

	componentDB = readComponentDB()
	

	fres		= open("./result_" + inputRepo, 'w')
	aveFuncs 	= getAveFuncs()


	for OSS in componentDB:
		commonFunc 	= []
		repoName 	= OSS.split('_sig')[0]
		totOSSFuncs = float(aveFuncs[repoName])
		if totOSSFuncs == 0.0:
			continue
		comOSSFuncs = 0.0
		for hashval in componentDB[OSS]:
			if hashval in inputDict:
				commonFunc.append(hashval)
				comOSSFuncs += 1.0

		if (comOSSFuncs/totOSSFuncs) >= theta:
			fres.write("OSS: " + OSS + '\n')

	fres.close()


def main(inputPath, inputRepo):
	resDict, fileCnt, funcCnt, lineCnt = OSS_Collector.hashing(inputPath)
	detector(resDict, inputRepo)


""" EXECUTE """
if __name__ == "__main__":
	
	testmode = 0

	if testmode:
		inputPath = currentPath + "/redis"
	else:
		inputPath = sys.argv[1]

	inputRepo = inputPath.split('/')[-1]

	main(inputPath, inputRepo)