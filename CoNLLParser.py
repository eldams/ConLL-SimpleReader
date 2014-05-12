#!/usr/bin/python
# A very simple CoNLL format parser
# Written by Damien Nouvel

class CoNLLSentence:
	
	def __init__(self, lines):
		self.nodes = {}
		previousNode = False
		for line in lines:
			line = line.strip()
			lineInfos = line.split('\t')
			if len(lineInfos) == 11:
				node = CoNLLNode(lineInfos, self)
				node.previousNode = previousNode
				previousNode = node
				self.nodes[node.id] = node
		self.linkNodes()

	def linkNodes(self):
		for node in self.getNodes():
			node.outDependency = None
			node.inDependencies = []
		for node in self.getNodes():
			if node.outDependencyId in self.nodes:
				node.outDependency = self.nodes[node.outDependencyId]
				if not node in node.outDependency.inDependencies:
					node.outDependency.inDependencies.append(node)

	def getNodes(self, pos = None, decoration = None):
		nodes = [self.nodes[i] for i in sorted(self.nodes.keys())]
		if pos:
			nodes = [node for node in nodes if node.pos == pos]
		if decoration:
			nodes = [node for node in nodes if decoration in node.decorations and node.decorations[decoration]]
		return nodes
	
	def __str__(self):
		return '\n'.join([str(node) for node in self.getNodes()])
	
	def distributeCoordinations(self):
		for node in self.getNodes():
			if node.outDependencyType == 'dep_coord' and node.outDependency:
				coordNode = node.outDependency
				while coordNode.outDependencyType == 'coord' and coordNode.outDependency:
					coordNode = coordNode.outDependency
				node.outDependencyType = coordNode.outDependencyType
				node.outDependencyId = coordNode.outDependencyId
		self.linkNodes()
	
	def tagLemmasFromList(self, l, t = 'T', rd = False):
		for node in self.getNodes():
			lemma = node.lemma
			if rd:
				from unidecode import unidecode
				lemma = unidecode(unicode(lemma, 'utf-8'))
			if lemma in l:
				node.tags[t] = True
	
	def decorate(self, lemmaDecorations, pos = False):
		for node in self.getNodes():
			if (not pos or node.pos == pos) and node.lemma in lemmaDecorations:
				for decoration in lemmaDecorations[node.lemma]:
					node.decorations[decoration] = True
	
	def toFeatures(self):
		return [node.toFeatures() for node in self.getNodes()]
	
	def getTag(self, t = 'T'):
		return [node.getTag(t) for node in self.getNodes()]
	
	def getTaggedLemmas(self, c, v, t = 'T', rd = False):
		nodesLen = len(self.getNodes())
		nodesIds = []
		for node in self.getNodes():
			if c.predict(v.transform([node.toFeatures()]))[0]:
				nodesIds.append(node.id)
		# Adds lemmas linked by a P
		for i in range(1, nodesLen - 1):
			if i in self.nodes and i - 1 in self.nodes and i + 1 in self.nodes:
				if self.nodes[i].pos == 'P' and i - 1 in nodesIds and i + 1 in nodesIds:
					nodesIds.append(i)
		lemmas = []
		lemmaParts = []
		for i in range(nodesLen + 1):
			if len(lemmaParts) and (i == nodesLen or i not in nodesIds):
				lemmas.append('-'.join(lemmaParts))
				lemmaParts = []
			elif i in nodesIds:
				lemma = self.nodes[i].lemma
				if rd:
					from unidecode import unidecode
					lemma = unidecode(unicode(lemma, 'utf-8'))
				lemmaParts.append(lemma)
		return lemmas

class CoNLLNode:

	mode = 'CoNLL-MaltParser'

	def __init__(self, l, s, t = 'CoNLL'):
		self.sentence = s
		self.tags = {}
		if self.__class__.mode == 'CoNLL':
			(id, token, lemma, cpos, pos, morpho, outDependencyId, outDependencyType, phead, pdep) = l
		elif self.__class__.mode == 'CoNLL-MaltParser':
			(id, token, lemma, cpos, pos, morpho, cluster, outDependencyId, outDependencyType, phead, pdep) = l
		elif self.__class__.mode == 'CoNLL-PropBank':
			# ID FORM LEMMA PLEMMA POS PPOS FEAT PFEAT HEAD PHEAD DEPREL PDEPREL FILLPRED PRED APREDs
			# FEAT is a set of morphological features (separated by |) defined for a particular language, e.g. more detailed part of speech, number, gender, case, tense, aspect, degree of comparison, etc.
			# The P-columns (PLEMMA, PPOS, PFEAT, PHEAD and PDEPREL) are the autoamtically predicted variants of the gold-standard LEMMA, POS, FEAT, HEAD and DEPREL columns. They are produced by independently (or cross-)trained taggers and parsers.
			# PRED is the same as in the 2008 English data. APREDs correspond to 2008's ARGs. FILLPRED contains Y for lines where PRED is/should be filled. 
			(id, token, lemma, cpos, pos, morpho, cluster, outDependencyId, outDependencyType, phead, pdep) = l
		self.id = int(id)
		self.token = token
		self.lemma = lemma
		self.pos = cpos
		self.outDependency = None
		self.outDependencyId = int(outDependencyId)
		self.outDependencyType = outDependencyType
		self.inDependencies = []
		self.decorations = {}
		
	def __str__(self):
		return '\t'.join([str(self.id), self.token, self.lemma, self.pos, str(self.outDependencyId), self.outDependencyType, ','.join(self.decorations.keys()), ','.join(self.tags.keys())])
	
	def toFeatures(self):
		features = {'TOK': self.token, 'LEM': self.lemma, 'POS': self.pos, 'DEP': self.outDependencyType}
		if self.outDependency:
			features.update(dict([(self.outDependencyType+'-'+decoration, True) for decoration in self.outDependency.decorations]))
		return features
	
	def getTag(self, t = 'T'):
		return t in self.tags

