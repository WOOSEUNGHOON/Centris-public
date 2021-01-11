
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
import tlsh

"""GLOBALS"""
currentPath		= os.getcwd()
theta			= 0.1
resultPath		= currentPath + "/res/"
repoFuncPath	= "../osscollector/repo_functions/"
verIDXpath		= "../preprocessor/verIDX/"
initialDBPath	= "../preprocessor/initialSigs/"
finalDBPath		= "../preprocessor/componentDB/"
metaPath		= "../preprocessor/metaInfos/"
aveFuncPath		= metaPath + "aveFuncs"
weightPath		= metaPath + "weights/"


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

def readAllVers(repoName):
	allVerList 	= []
	idx2Ver		= {}
	
	with open(verIDXpath + repoName + "_idx", 'r', encoding = "UTF-8") as fp:
		tempVerList = json.load(fp)

		for eachVer in tempVerList:
			allVerList.append(eachVer["ver"])
			idx2Ver[eachVer["idx"]] = eachVer["ver"]

	return allVerList, idx2Ver

def readWeigts(repoName):
	weightDict = {}

	with open(weightPath + repoName + "_weights", 'r', encoding = "UTF-8") as fp:
		weightDict = json.load(fp)

	return weightDict

def detector(inputDict, inputRepo):
	componentDB 	= {}

	componentDB = readComponentDB()
	

	fres		= open(resultPath + "result_" + inputRepo, 'w')
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
			verPredictDict 	= {}
			allVerList, idx2Ver = readAllVers(repoName)
			
			for eachVersion in allVerList:
				verPredictDict[eachVersion] = 0.0

			weightDict 		= readWeigts(repoName)

			with open(initialDBPath + OSS, 'r', encoding = "UTF-8") as fi:
				jsonLst = json.load(fi)
				for eachHash in jsonLst:
					hashval = eachHash["hash"]
					verlist = eachHash["vers"]

					if hashval in commonFunc:
						for addedVer in verlist:
							verPredictDict[idx2Ver[addedVer]] += weightDict[hashval]

			sortedByWeight 	= sorted(verPredictDict.items(), key=lambda x: x[1], reverse=True)
			predictedVer	= sortedByWeight[0][0]
			
			predictOSSDict = {}
			with open(repoFuncPath + repoName + '/fuzzy_' + predictedVer + '.hidx', 'r', encoding = "UTF-8") as fo:
				body = ''.join(fo.readlines()).strip()
				for eachLine in body.split('\n')[1:]:

					ohash = eachLine.split('\t')[0]
					opath = eachLine.split('\t')[1]

					predictOSSDict[ohash] = opath.split('\t')


			used 	  = 0
			unused 	  = 0
			modified  = 0
			strChange = False

			for ohash in predictOSSDict:
				flag = 0

				for thash in inputDict:
					if ohash == thash:
						used += 1

						nflag = 0
						for opath in predictOSSDict[ohash]:
							for tpath in inputDict[thash]:
								if opath in tpath:
									nflag = 1

						if nflag == 0:
							strChange = True

						flag = 1

					else:
						score = tlsh.diffxlen(ohash, thash)
						if int(score) <= 30:
							modified += 1

						nflag = 0
						for opath in predictOSSDict[ohash]:
							for tpath in inputDict[thash]:
								if opath in tpath:
									nflag = 1

						if nflag == 0:
							strChange = True

						flag = 1

					if flag == 0:
						unused += 1

			fres.write(inputRepo, repoName, predictedVer, used, unused, modified, strChange, '\n')
	fres.close()


def main(inputPath, inputRepo):
	resDict, fileCnt, funcCnt, lineCnt = OSS_Collector.hashing(inputPath)
	detector(resDict, inputRepo)


""" EXECUTE """
if __name__ == "__main__":
	
	testmode = 0

	if testmode:
		inputPath = currentPath + "/crown"
	else:
		inputPath = sys.argv[1]

	inputRepo = inputPath.split('/')[-1]

	main(inputPath, inputRepo)