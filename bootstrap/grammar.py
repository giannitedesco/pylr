from symbol import *

class Production(object):
	def __init__(self, nt, r = None):
		super(Production, self).__init__()
		if not isinstance(nt, NonTerminal):
			raise TypeError
		self.nt = nt
		self.rules = []
		if r is not None:
			self.rule(r)

	def rule(self, r):
		for x in r:
			if not isinstance(x, Sym):
				raise TypeError
		self.rules.append(r)

	def __or__(a, b):
		if a.nt is not b.nt:
			raise ValueError
		p = Production(a.nt)
		p.rules = a.rules | b.rules
		return p

	def __str__(self):
		return '%s(%s -> %s)'%(self.__class__.__name__,
						self.nt, self.rules)

	def __repr__(self):
		return '%s(%s -> %s)'%(self.__class__.__name__,
						self.nt, self.rules)
	def __iter__(self):
		return iter(self.rules)

class Grammar(object):
	def __init__(self):
		super(Grammar, self).__init__()
		self.sym = {}
		self.lookup = {}
		self.t = set()
		self.nt = set()
		self.p = {}

	def symbol(self, sym):
		if isinstance(sym, Terminal):
			self.t.add(sym.val)
		elif isinstance(sym, NonTerminal):
			self.nt.add(sym.val)
		else:
			raise TypeError
		self.sym[sym.name] = sym
		self.lookup[sym.val] = sym
		return sym

	def production(self, p):
		if not isinstance(p, Production):
			raise TypeError
		map(self.p.setdefault(p.nt.name, Production(p.nt)).rule,
			p.rules)

	def get(self, k):
		try:
			return self.sym[k]
		except KeyError:
			return self.symbol(NonTerminal(k))

	def __getitem__(self, k):
		if isinstance(k, str):
			return self.sym[k]
		elif isinstance(k, int):
			return self.lookup[k]
		else:
			raise TypeError

	def __iter__(self):
		return iter(self.p.values())

	def construct_markers(self):
		print 'construct markers...'
		for s in self.sym.values():
			if isinstance(s, NonTerminal) and \
					not self.p.has_key(s.name):
				self.p[s.name] = Production(s, [SymEpsilon()])

	def eliminate_immediate_left_recursion(self, p):
		prime = NonTerminal(p.nt.name + "'")
		new = []
		np = Production(prime)
		lr = None
		#print 'direct left recution', p.nt
		for r in p:
			left = r[0]
			if left is p.nt:
				lr = r[1:]
				lr.append(prime)
				np.rules.append(lr)
				continue
			r.append(prime)
			new.append(r)
		p.rules = new
		np.rules.append([SymEpsilon()])
		self.production(np)
		self.symbol(prime)
		#print

	def eliminate_left_recursion(self):
		print 'eliminate left recursion...'
		lrp = []
		for p in self:
			for r in p:
				left = r[0]
				if left is p.nt:
					lrp.append(p)
					break

		for p in lrp:
			self.eliminate_immediate_left_recursion(p)
