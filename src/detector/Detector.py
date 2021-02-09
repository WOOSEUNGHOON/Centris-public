
"""
Detector.
Author:		Seunghoon Woo (seunghoonwoo@korea.ac.kr)
Modified: 	December 16, 2020.
"""

import os
import sys
#sys.path.insert(0, "../osscollector")
#import OSS_Collector
import subprocess
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
ctagsPath		= "/usr/local/bin/ctags"


shouldMake 	= [resultPath]
for eachRepo in shouldMake:
	if not os.path.isdir(eachRepo):
		os.mkdir(eachRepo)


# Generate TLSH
def computeTlsh(string):
	string 	= str.encode(string)
	hs 		= tlsh.forcehash(string)
	return hs


def removeComment(string):
	# Code for removing C/C++ style comments. (Imported from VUDDY and ReDeBug.)
	# ref: https://github.com/squizz617/vuddy
	c_regex = re.compile(
		r'(?P<comment>//.*?$|[{}]+)|(?P<multilinecomment>/\*.*?\*/)|(?P<noncomment>\'(\\.|[^\\\'])*\'|"(\\.|[^\\"])*"|.[^/\'"]*)',
		re.DOTALL | re.MULTILINE)
	return ''.join([c.group('noncomment') for c in c_regex.finditer(string) if c.group('noncomment')])

def normalize(string):
	# Code for normalizing the input string.
	# LF and TAB literals, curly braces, and spaces are removed,
	# and all characters are lowercased.
	# ref: https://github.com/squizz617/vuddy
	return ''.join(string.replace('\n', '').replace('\r', '').replace('\t', '').replace('{', '').replace('}', '').split(' ')).lower()

def hashing(repoPath):
	# This function is for hashing C/C++ functions
	# Only consider ".c", ".cc", and ".cpp" files
	possible = (".c", ".cc", ".cpp")
	
	fileCnt  = 0
	funcCnt  = 0
	lineCnt  = 0

	resDict  = {}

	for path, dir, files in os.walk(repoPath):
		for file in files:
			filePath = os.path.join(path, file)

			if file.endswith(possible):
				try:
					# Execute Ctgas command
					functionList 	= subprocess.check_output(ctagsPath + ' -f - --kinds-C=* --fields=neKSt "' + filePath + '"', stderr=subprocess.STDOUT, shell=True).decode()

					f = open(filePath, 'r', encoding = "UTF-8")

					# For parsing functions
					lines 		= f.readlines()
					allFuncs 	= str(functionList).split('\n')
					func   		= re.compile(r'(function)')
					number 		= re.compile(r'(\d+)')
					funcSearch	= re.compile(r'{([\S\s]*)}')
					tmpString	= ""
					funcBody	= ""

					fileCnt 	+= 1

					for i in allFuncs:
						elemList	= re.sub(r'[\t\s ]{2,}', '', i)
						elemList 	= elemList.split('\t')
						funcBody 	= ""

						if i != '' and len(elemList) >= 8 and func.fullmatch(elemList[3]):
							funcStartLine 	 = int(number.search(elemList[4]).group(0))
							funcEndLine 	 = int(number.search(elemList[7]).group(0))

							tmpString	= ""
							tmpString	= tmpString.join(lines[funcStartLine - 1 : funcEndLine])

							if funcSearch.search(tmpString):
								funcBody = funcBody + funcSearch.search(tmpString).group(1)
							else:
								funcBody = " "

							funcBody = removeComment(funcBody)
							funcBody = normalize(funcBody)
							funcHash = computeTlsh(funcBody)

							if len(funcHash) == 72 and funcHash.startswith("T1"):
								funcHash = funcHash[2:]
							elif funcHash == "TNULL" or funcHash == "" or funcHash == "NULL":
								continue

							storedPath = filePath.replace(repoPath, "")
							if funcHash not in resDict:
								resDict[funcHash] = []
							resDict[funcHash].append(storedPath)

							lineCnt += len(lines)
							funcCnt += 1

				except subprocess.CalledProcessError as e:
					print("Parser Error:", e)
					continue
				except Exception as e:
					print ("Subprocess failed", e)
					continue

	return resDict, fileCnt, funcCnt, lineCnt 

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

			fres.write('\t'.join([inputRepo, repoName, predictedVer, str(used), str(unused), str(modified), str(strChange)]) + '\n')
	fres.close()


def main(inputPath, inputRepo):
	resDict, fileCnt, funcCnt, lineCnt = hashing(inputPath)


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