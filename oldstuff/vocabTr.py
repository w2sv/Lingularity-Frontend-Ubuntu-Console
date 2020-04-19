from numpy import random
from random import shuffle
import os
from time import sleep
import sys

sleeptime = 17
class PhraseFile():
	def __init__(self,lanAbb):
		self.phrasesLink = f'C:/Users/User/Documents/W2SV/Data/TextData/LanguageData/{lanAbb}.txt'
		self.phraseData = self.getPhraseData()
		self.frenchPhrases = [i.split('\t')[1] for i in self.phraseData]
		self.englishPhrases = [i.split('\t')[0] for i in self.phraseData]
	def getPhraseData(self):
		with open(self.phrasesLink,'r',encoding='utf-8') as phrFile:
			return phrFile.readlines()
	def showPhrases(self,facedWords):
		print('Commencing phrase display\n')
		shuffle(facedWords)
		for completeFrench in facedWords:
			trunkatedFrench = ""
			if completeFrench.startswith('le') or completeFrench.startswith('la') or completeFrench.startswith("l'"): # article handling
				trunkatedFrench = completeFrench[2:]
			if completeFrench.endswith('er') or completeFrench.endswith('re') or completeFrench.endswith('ir'): # verb handling
				trunkatedFrench = completeFrench[:-2]
			completeFrench = trunkatedFrench if trunkatedFrench != "" else completeFrench
			phraseList = []
			phraseCounter = 0
			for i in range(len(self.frenchPhrases)):
				if completeFrench in self.frenchPhrases[i] and phraseCounter <= 20:
					phraseList.append(i)
					phraseCounter += 1
				if phraseCounter == 20:
					break
			if len(phraseList) > 0:
				drawnPhraseIndex = phraseList[random.randint(len(phraseList))]
				print(self.englishPhrases[drawnPhraseIndex])
				try:
					input("pending...")
				except SyntaxError:
					pass
				print(self.frenchPhrases[drawnPhraseIndex])
				print('______________')
		sleep(2)
		os.system('cls')
		return []
class VocableFile():
	def __init__(self,language):
		self.vocableLink = f'C:\\Users\\Apollo\\Documents\\TxtDoks\\Languages\\wordlist {language}.txt'
		self.docLink = f'C:\\Users\\Apollo\\languageDocFiles\\{language}VocDoc.txt'
		self.vocData = self.removeDuplicates()
		self.docData = self.openDocFile()
		self.writeZerosIfNec()
		self.knownWords = self.setIndexLists()[0]
		self.newWords = self.setIndexLists()[1]
		self.facedWords = []
		self.correct = 0
		self.facedCounter = 0
		self.phraseFile = PhraseFile(language[:3])
		self.removedLine = False
	def removeDuplicates(self):
		data = open(self.vocableLink,'r',encoding='latin').readlines()
		removedLines = 0
		for selInd in range(len(data)):
			line = data[selInd-removedLines]
			delimiterPos = line.find(' - ') if line.find(' - ') != -1 else line.find('=')
			wordSplits = line[:delimiterPos].split(' ')	# in case of articles, word group; words of target language(left side) in splits
			for searchInd in range(selInd+1-removedLines,len(data)):
				compareLine = data[searchInd]
				delimiterPos = compareLine.find('-') if compareLine.find('-') != -1 else compareLine.find('=')
				wordSplitsComp = compareLine[:delimiterPos].split(' ')
				if wordSplits == wordSplitsComp:
					print(f'removing "{line[:-1]}" due to "{compareLine[:-1]}".')
					self.removedLine = True
					del data[selInd]
					removedLines+=1
					break
		print(f'Vocable file contains: {len(data)} words/phrases')
		return data
	def openDocFile(self):
		try:
			return open(self.docLink,'r').readlines()
		except Exception:
			print("Created new documentation file.")
			open(self.docLink,'w+')
			return open(self.docLink,'r').readlines()
	def writeZerosIfNec(self):
		self.vocData = [i.strip('\n') for i in self.vocData]
		lengthDiff = len(self.vocData) - len(self.docData)
		for i in range(len(self.vocData)-lengthDiff-1,len(self.vocData)):
			self.docData.append(self.vocData[i]+' 0\n')	#	'\n' if desidered 
		vocDataSplits = [i.split(' ') for i in self.vocData]
		[i.append('\n') for i in vocDataSplits]		# no assignment for whatever reason
		self.vocData = [' '.join(i) for i in vocDataSplits]
	def getScore(self,index):
		scoreline = self.docData[index]
		if scoreline.endswith('\n') != True:
			scoreline+='\n'
		return int(scoreline[-2])	# needs incoming data to contain newline
	def setIndexLists(self):
		knownWords = [i for i in range(len(self.docData)) if self.getScore(i)<5 and self.getScore(i)>0]
		unknownWords = [i for i in range(len(self.docData)) if self.getScore(i)==0]
		shuffle(unknownWords)
		shuffle(knownWords)
		return knownWords, unknownWords
	def tolerance(self,entered,correctConst):
		correctWords = correctConst.split(',')
		for correct in correctWords:
			correct = correct.strip(' ')
			if entered == correct:
				return True
			counter = 0
			enteredList = list(entered)
			correctList = list(correct)
			for letter in correctList:
				if letter in enteredList:
					counter+=1
					enteredList[enteredList.index(letter)] = '0'
			if counter >= len(correct)-1:
				print('almost correct: ' + ''.join(correctList),end=' ')
				return True
		return False
	def showNewWords(self):
		# index drawing
		print("Mots inconnus:")
		threshold = 10 if len(self.newWords)>=10 else len(self.newWords)
		indices = []
		corrPassing = 0
		for k in range(threshold):
			wordInd = self.newWords[random.randint(0,len(self.newWords))]
			indices.append(wordInd)
			self.newWords.remove(wordInd)
		[print(self.docData[k][:-2],'\n') for k in indices]	# printing words with translations
		sleep(sleeptime)
		os.system('cls')
		# presenting words, capturing response
		for j in range(len(indices)):
			self.facedCounter += 1
			currInd = indices[j]
			currLine = self.docData[currInd][:-3]	# excluding score for presentation 
			breakPos = currLine.find(' - ') if currLine.find(' - ') != -1 else currLine.find(' = ')
			completeFrench = currLine[:breakPos]
			translations = currLine[breakPos+3:]
			# score updating
			score = int(scoreSplits[-1])
			print(f'{translations} = ',end="")
			response = input()
			if self.tolerance(response,completeFrench)==True:
				self.correct += 1
				score+=1
				print("+1")
				corrPassing += 1
			else:
				print(f'{completeFrench}\n')
				self.knownWords.append(currInd)
			self.facedWords.append(completeFrench)
			scoreSplits[-1] = str(score)
			self.docData[currInd] = ' '.join(scoreSplits)
			self.docData[currInd] += '\n'

		print(f'You got {corrPassing} out of {len(indices)} correct.')
		self.facedWords = self.phraseFile.showPhrases(self.facedWords)	# returns empty list
	def showKnownWords(self):
		print("Mots connus:")
		threshold = 10 if len(self.knownWords)>=10 else len(self.knownWords)
		indices = []
		corrPassing = 0
		for k in range(threshold):
			wordInd = self.knownWords[random.randint(0,len(self.knownWords))]
			indices.append(wordInd)
			self.knownWords.remove(wordInd)
		os.system('cls')
		# presenting words, capturing response
		for j in range(len(indices)):
			self.facedCounter += 1
			currInd = indices[j]
			currLine = self.docData[currInd][:-3]	# excluding score for presentation 
			breakPos = currLine.find(' - ') if currLine.find(' - ') != -1 else currLine.find(' = ')
			completeFrench = currLine[:breakPos]
			translations = currLine[breakPos+3:]
			# score updating
			scoreSplits = self.docData[currInd].split(' ') # including score
			score = int(scoreSplits[-1])
			print(f'{translations} = ',end="")
			response = input()
			if self.tolerance(response,completeFrench)==True:
				self.correct += 1
				score+=1
				print("+1")
				corrPassing += 1
			else:
				print(f'{completeFrench}\n')
				self.knownWords.append(currInd)
			self.facedWords.append(completeFrench)
			scoreSplits[-1] = str(score)
			self.docData[currInd] = ' '.join(scoreSplits)
			self.docData[currInd] += '\n'
				
		print(f'You got {corrPassing} out of {len(indices)} correct.')
		self.facedWords = self.phraseFile.showPhrases(self.facedWords)	# returns empty list
	def getSeizableWords(self):
		return len(self.newWords) + len(self.knownWords)
	def write2DocFile(self):
		with open(self.docLink,'w') as wFile:
			wFile.writelines(self.docData)
	def write2VocFile(self):
		[print(i) for i in self.vocData]
		confirmation = input('write to file? (y/n)')
		if confirmation == 'y':
			with open(self.vocLink,'w') as wFile:
				wFile.writelines(self.vocData)
#-----------main loop------------
def main():
	def exitProgram():
		print("\nWriting new scores to file...")
		words.write2DocFile()
		if words.removedLine == True:
			words.write2VocFile()
		print(f'{words.correct} out of {words.facedCounter} correctly answered.')
		sys.exit()
	
	language = input('Language whose vocables you want to train: ')
	words = VocableFile(language)
	print("number of already correctly faced words: " + str(len(words.knownWords)))
	while words.getSeizableWords() > 0:
		pick = random.randint(0,2)
		try:
			if pick==0 and len(words.newWords) > 0:
				words.showNewWords()
			if pick==1 and len(words.knownWords) > 0:
				words.showKnownWords()
			if len(words.newWords)==0 and len(words.knownWords)==0:
				print("There are no learnable words left. Sick job my man.")
				exitProgram()
		except KeyboardInterrupt:
			exitProgram()

if __name__=='__main__':
	
	main()