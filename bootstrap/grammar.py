from symbol import *
from graph import Graph

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
		for o in self.rules:
			if o == r:
				return
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
		assert(p.nt.val in self.nt)
		assert(p.nt.name in self.sym)
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
				if len(r) == 1 and r[0] is SymEpsilon():
					yield l
		e = frozenset(erules(rcopy))

		#print 'nullables:', e
		#print
		for (l,r) in rcopy:
			if len(r) == 1:
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
			nr = len(r) == 1 and r[0] is SymEpsilon()
			return not nr

		for nt, p in self.p.items():
			p.rules = filter(f, p.rules)

	def eliminate_unit_rules(self):
		print 'eliminate unit rules...'
		def unit_rules():
			for l, p in self.p.items():
				if self[l].terminal_marker:
					continue
				for r in p:
					if len(r) == 2:
						continue
					assert(len(r) == 1)
					yield self[l], r[0]

		def make_dot_file(gen):
			g = Graph('Unit Rules', 'unit.dot')
			s = set()
			for l, r in gen:
				if l.name not in s:
					g.add_node(l.name, shape='rectangle')
				if r.name not in s:
					g.add_node(r.name, shape='rectangle')
				s.add(l.name)
				s.add(r.name)
				g.add_edge(l.name, r.name, '')

		make_dot_file(unit_rules())

		fwd = dict()
		rev = dict()
		s = set()
		for l, r in unit_rules():
			fwd.setdefault(l.name, list()).append(r.name)
			rev.setdefault(r.name, list()).append(l.name)
			s.add(l.name)
			s.add(r.name)

		start = s - set(fwd.keys())

		def replace(e, f):
			# for each edge E -> F
			#print 'traversed edge: %s -> %s'%(e, f)

			e = self.p[e]
			f = self.p[f]

			# for each rule F -> CD
			for r in f:
				#  `- replace with E -> CD
				if len(r) == 2:
					e.rule(r)
					continue
			def nonunit(r):
				return len(r) == 2
			f.rules = filter(nonunit, e.rules)

			# remove rule E -> F
			def kill(rule):
				return rule != [f.nt]
			e.rules = filter(kill, e.rules)

		def traverse(x):
			try:
				l = rev[x]
			except KeyError:
				return
			for n in l:
				replace(n, x)
				traverse(n)

		for x in start:
			traverse(x)
			#print

	def dump(self):
		print '--'
		for l, p in sorted(self.p.items()):
			for r in p:
				print l, '->', \
					' '.join(map(lambda x:x.name, r))
		print '--'

	def eliminate_immediate_left_recursion(self, p):
		def f(r):
			return r[0] == p.nt
		lr = filter(f, p.rules)
		nlr = filter(lambda x: not f(x), p.rules)

		if not lr:
			return

		print p.nt.name, 'is left recursive'

		prime = p.nt.new_prime()
		self.symbol(prime)
		np = Production(prime)

		p.rules = []
		for beta in nlr:
			p.rule(beta + [prime])

		for alpha in lr:
			np.rule(alpha[1:] + [prime])

		self.production(np)

	def eliminate_left_recursion(self):
		print 'eliminate left recursion...'

		def num(p):
			return p.nt

		def pairs():
			for i in sorted(map(num, self.p.values())):
				for j in sorted(map(num, self.p.values())):
					if j >= i:
						break
					a = self.p[i.name]
					b = self.p[j.name]
					yield a, b

		def f(r, b, new):
			# no possibility of left recursion, keep it
			if r[0] != b.nt:
				return True

			for x in b.rules:
				nr = x + r[1:]
				new.append(nr)

			# remove old rule
			return False

		for a, b in list(pairs()):
			new = []
			a.rules = filter(lambda x:f(x, b, new), a.rules)
			a.rules.extend(new)

			self.eliminate_immediate_left_recursion(a)

	def left_factor(self):
		print 'Left factoring...'

		def cp(a, b):
			p = []
			for i in xrange(min(len(a), len(b))):
				if a[i] == b[i]:
					p.append(a[i])
				else:
					break
			return p

		def lcp(rules):
			i = 0
			while i + 1 < len(rules):
				x = cp(rules[i], rules[i+1])
				if x:
					return x
				i += 1
				continue
			return None

		def begins_with(s, prefix):
			if len(s) < len(prefix):
				return False
			return s[:len(prefix)] == prefix

		def replace(old_p, prefix, new_p):
			# replace
			# A-> aB1 | aB2 | ... | Abn | y
			# with
			# A -> aA' | y
			# A' -> B1 | B2 | ... | Bn

			old_rules = []
			new_rules = []
			plen = len(prefix)

			old_rules.append(prefix + [new_p.nt])
			for r in old_p.rules:
				if begins_with(r, prefix):
					n = r[plen:]
					if n:
						new_rules.append(r[plen:])
					else:
						new_rules.append([SymEpsilon()])
				else:
					old_rules.append(r)

			old_p.rules = old_rules
			new_p.rules = new_rules

		def factor():
			delta = False
			for nt, p in self.p.items():
				r = sorted(p.rules)
				c = lcp(r)
				if not c:
					continue

				ns = self[nt].new_prime()
				self.symbol(ns)
				np = Production(ns)

				replace(p, c, np)
				delta = True

				self.production(np)


			return delta

		fixpoint = False
		while not fixpoint:
			fixpoint = not factor()

	def construct_FIRST(self):
		if self.FIRST is not None:
			return self.FIRST
		print 'Construct FIRST function..'
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
