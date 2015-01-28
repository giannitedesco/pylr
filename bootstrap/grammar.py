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
	def __getitem__(self, k):
		return self.rules[k]
	def __delitem__(self, k):
		del self.rules[k]

class Grammar(object):
	def __init__(self):
		super(Grammar, self).__init__()
		self.sym = {}
		self.lookup = {}
		self.t = set()
		self.nt = set()
		self.p = {}
		self.FIRST = None
		self.FOLLOW = None

	def augment(self, start_sym):
		self.symbol(SymStart())
		self.production(Production(SymStart(),
				[self[start_sym], SymEof()]))

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

	def wrap_terminals(self):
		print 'wrap terminals...'
		for t in map(self.__getitem__, self.t):
			s = NonTerminal('TERMINAL_%s'%t.name)
			s.terminal_marker = True
			self.symbol(s)
			p = Production(s)
			p.rule([t])
			self.production(p)

		def do_wrap(sym):
			if isinstance(sym, Terminal):
				n = 'TERMINAL_%s'%sym.name
				return self[n]
			return sym

		def wrap(rule):
			return map(do_wrap, rule)

		for nt, p in self.p.items():
			if self[nt].terminal_marker:
				continue
			p.rules = map(wrap, p.rules)

	def normalize(self):
		print 'normalize...'
		def long_rules():
			for nt, p in self.p.items():
				for r in p:
					if len(r) <= 2:
						continue
					yield p, r

		for p, r in long_rules():

			# create new chain of rules
			#print p.nt
			#print r

			n = [p.nt.new_prime() for x in r[1:-1]]
			map(self.symbol, n)

			for j, w in enumerate(r[:-1]):
				if not j:
					np = p
				else:
					np = Production(n[j - 1])

				try:
					np.rule([w, n[j]])
				except IndexError:
					np.rule([w, r[j + 1]])

				if j:
					#print '+', np
					self.production(np)
			#print

		# remove all the old, long rules
		for nt, p in self.p.items():
			for r in p:
				p.rules = filter(lambda x:len(x) <= 2,
							p.rules)

	def eliminate_epsilons(self):
		print 'eliminate epsilon productions...'
		rcopy = []
		for nt, rules in self.p.items():
			for r in rules:
				rcopy.append((self[nt], r))

		def erules(rcopy):
			for (l,r) in rcopy:
				if r[0] is SymEpsilon():
					yield l
		e = frozenset(erules(rcopy))

		#print 'nullables:', e
		#print
		for (l,r) in rcopy:
			if len(r) == 1:
				if r[0] in e:
					print 'delete rule', l, r
				continue
			assert(len(r) == 2)
			#if frozenset(r) & e:
			#	print l.name, '->', \
			#		' '.join(map(lambda x:x.name, r))
			if r[0] in e:
				#print l.name, '->', r[1].name
				self.p[l.name].rules.append([r[1]])
				#print
			elif r[1] in e:
				#print l.name, '->', r[0].name
				self.p[l.name].rules.append([r[0]])
				#print

		# FIXME: if StartSym -> epsilon, then keep it
		def f(r):
			if frozenset(r) & e:
				return False
			return r[0] is not SymEpsilon()

		for nt, p in self.p.items():
			p.rules = filter(f, p.rules)

	def eliminate_unit_rules(self):
		print 'eliminate unit rules...'
		for l, p in self.p.items():
			if self[l].terminal_marker:
				continue
			for r in p:
				if len(r) == 2:
					continue
				assert(len(r) == 1)
				print l, '->', \
					' '.join(map(lambda x:x.name, r))
		raise SystemExit

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
		# FIXME: do this properly for all left-recursion
		lrp = []
		for p in self:
			for r in p:
				left = r[0]
				if left is p.nt:
					lrp.append(p)
					break

		for p in lrp:
			self.eliminate_immediate_left_recursion(p)

	def construct_FIRST(self):
		print 'Construct FIRST function..'
		if self.FIRST is not None:
			return self.FIRST
		def do_FIRST(nt, f):
			if f.has_key(nt.name):
				return f[nt.name]
			p = self.p[nt.name]
			s = set()
			for r in p:
				start = r[0]
				if isinstance(start, NonTerminal):
					tmp = do_FIRST(start, f)
				else:
					tmp = set([start])
				if s & tmp:
					print ' FIRST/FIRST conflict ->', \
						nt.name, s & tmp
				s |= tmp
			f[nt.name] = s
			return s

		f = {}
		for nt in self.sym.values():
			if not isinstance(nt, NonTerminal):
				continue
			do_FIRST(nt, f)

		#for k, v in sorted(f.items()):
		#	print ' ->', k, v

		self.FIRST = f
		return f

	def construct_FOLLOW(self):
		if self.FOLLOW is not None:
			return self.FOLLOW
		self.construct_FIRST()
		print 'Construct FOLLOW function..'
		def do_FOLLOW(nt, f):
			if f.has_key(nt.name):
				return f[nt.name]
			s = set()
			rec = []
			for p in self:
				for r in p:
					if r[-1] is nt:
						rec.append(p.nt)
					try:
						i = r.index(nt)
					except ValueError:
						continue
					if i + 1 >= len(r):
						continue
					n = r[i + 1]
					if isinstance(n, NonTerminal):
						tmp = self.FIRST[n.name]
						if SymEpsilon() in tmp:
							rec.append(n)
						s |= tmp - set([SymEpsilon()])
					else:
						s |= set([n])
			f[nt.name] = s
			for n in sorted(set(rec)):
				s |= do_FOLLOW(n, f)
				f[nt.name] = s
			return s

		f = {}
		for nt in self.sym.values():
			if not isinstance(nt, NonTerminal):
				continue
			do_FOLLOW(nt, f)
		f['S'] = set([SymEof()])

		for k, v in sorted(f.items()):
			if v & self.FIRST[k]:
				print ' FIRST/FOLLOW conflict ->', k,\
						v & self.FIRST[k]
			#print ' ->', k, v

		self.FOLLOW = f
		return f
