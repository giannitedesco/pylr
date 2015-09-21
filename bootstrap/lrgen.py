from symbol import *
from grammar import Grammar
from lrgen_c import lrgen_c
from lrgen_py import lrgen_py

# item should be a pair of ints, (rule_idx, pos)
class Item(tuple):
	def __new__(cls, arg = [], **kwargs):
		if arg:
			if arg[-1] is SymEof():
				arg = arg[:-1]
			elif len(arg) == 1 and arg[0] == SymEpsilon():
				arg = []
		return super(Item, cls).__new__(cls, arg)
	def __init__(self, arg = [], **kwargs):
		self.head = kwargs.pop('head')
		self.pos = int(kwargs.pop('pos'))
		if arg:
			if arg[-1] is SymEof():
				arg = arg[:-1]
			elif len(arg) == 1 and arg[0] == SymEpsilon():
				arg = []
		super(Item, self).__init__(arg, **kwargs)
		assert(self.pos >= 0)
		assert(not arg or self.pos <= len(self))
	def __str__(self):
		def f((i, x)):
			if i == self.pos:
				return '. ' + x.name
			elif i == len(self) - 1 and self.pos == len(self):
				return x.name + ' .'
			return x.name
		if self:
			body = ' '.join(map(f, enumerate(self)))
		else:
			body = '.'
		return 'Item(%s -> %s)'%(self.head.name, body)
	def __repr__(self):
		return str(self)

	def __cmp(a, b):
		r = cmp(a.head, b.head)
		if r:
			return r
		r = cmp(a.pos, b.pos)
		if r:
			return r
		r = cmp(tuple(a), tuple(b))
		if r:
			return r
		return 0
	def __eq__(a, b):
		return (a.__cmp(b) == 0)
	def __neq__(a, b):
		return (a.__cmp(b) != 0)
	def __gt__(a, b):
		return (a.__cmp(b) > 0)
	def __lt__(a, b):
		return (a.__cmp(b) < 0)
	def __gte__(a, b):
		return (a.__cmp(b) >= 0)
	def __lte__(a, b):
		return (a.__cmp(b) <= 0)
	def __hash__(self):
		return super(Item, self).__hash__() \
			^ hash(self.pos) \
			^ hash(self.head)

class LRGen(object):
	def __init__(self, g, start):
		super(LRGen, self).__init__()
		if not isinstance(g, Grammar):
			raise TypeError

		self.start = g[start]
		if not isinstance(self.start, NonTerminal):
			raise TypeError


		self.p = g.p
		g.construct_FOLLOW()
		self.FOLLOW = g.FOLLOW
		self.reachables = list(g.reachables())

		self.productions = {}
		self.C = self.canonical_collection()
		self.state_number = self.number_states(self.C)
		self.action = self.construct_action_table()
		self.goto = self.construct_goto()
		self.initial = self.initial_state()

	def number_states(self, C):
		state_number = {}
		for i, I in enumerate(C):
			#print i, I
			#print
			state_number[I] = i
		return state_number

	def start_item(self):
		s = self.p['S']
		return Item(s.rules[0], head = s.nt, pos = 0)

	def end_item(self):
		s = self.p['S']
		return Item(s.rules[0], head = s.nt, pos = 1)

	def initial_state(self):
		s = self.start_item()
		for (I, inum) in self.state_number.items():
			if s in I:
				return inum

	def closure(self, I):
		J = set(I) # copy it
		fixpoint = False
		while not fixpoint:
			fixpoint = True
			for j in list(J):
				try:
					B = j[j.pos]
				except IndexError:
					continue
				if not isinstance(B, NonTerminal):
					continue
				for r in self.p[B.name]:
					i = Item(r, head = B, pos = 0)
					if i in J:
						continue
					fixpoint = False
					J.add(i)
		return frozenset(J)

	def GOTO(self, I, t):
		assert(isinstance(t, Sym))

		s = set()
		for i in I:
			try:
				x = i[i.pos]
			except IndexError:
				continue
			if x == t:
				s.add(Item(i, head = i.head, pos = i.pos + 1))

		return self.closure(s)

	def canonical_collection(self):
		print 'Construct canonical LR(0) collection'
		C = set()

		C.add(self.closure(frozenset([self.start_item()])))

		fixpoint = False
		while not fixpoint:
			fixpoint = True

			for I in list(C):
				for X in self.reachables:
					g = self.GOTO(I, X)
					if g and g not in C:
						C.add(g)
						fixpoint = False
		return frozenset(C)

	def construct_action_table(self):
		print 'Construct action table...'

		action = {}

		def handle_conflict(key, new):
			try:
				old = action[key]
			except KeyError:
				action[key] = new
				return

			if old == new:
				return

			print 'shift/reduce conflict'
			print old
			print new
			if old[0] == 'accept':
				action[key] = new
			elif new[0] == 'accept':
				pass
			elif old[0] == 'reduce' and new[0] == 'shift':
				action[key] = new
			elif old[0] == 'shift' and new[0] == 'reduce':
				pass
			else:
				print 'unable to resolve'
				raise Exception('action table conflict')

		def prod_name(r):
			t = map(lambda x:x.name.lower(), r)
			if not t:
				t = ('epsilon',)

			t = r.head.name.upper()
			f = map(lambda x:x.name.upper(), r)
			if not f:
				f = ('EPSILON',)

			return '%s__FROM__%s'%(t, '_'.join(f))

		def do_reduce(r):
			if len(r) == 1 and r[0] is SymEpsilon():
				return
			if r.head is SymStart():
				return

			n = prod_name(r)
			try:
				index = self.productions[n][0]
			except KeyError:
				index = len(self.productions)
				plen = len(r)
				head = r.head
				p = (index, plen, head)
				self.productions[n] = p

			for a in self.FOLLOW[r.head.name]:
				key = (inum, a)
				val = ('reduce', (index, r))
				handle_conflict(key, val)

		for (I, inum) in self.state_number.items():
			if self.end_item() in I:
				key = (inum, SymEof())
				val = ('accept', True)
				handle_conflict(key, val)

			for i in I:
				try:
					nxt = i[i.pos]
				except IndexError:
					do_reduce(i)
					continue
				g = self.GOTO(I, nxt)
				val = self.state_number.get(g, None)
				assert(val is not None)
				if val is None:
					continue
				val = ('shift', val)
				key = inum, nxt

				handle_conflict(key, val)

		#for k, v in sorted(action.items()):
		#	print k, '->', v

		print 'action table:', len(action), 'entries'
		return action

	def construct_goto(self):
		print 'Construct goto table...'

		goto = {}
		for (I, inum) in self.state_number.items():
			for t in self.reachables:
				if not isinstance(t, NonTerminal):
					continue
				g = self.GOTO(I,t)
				out = self.state_number.get(g, None)
				if out is None:
					continue
				key = (inum, t)
				val = out
				goto[key] = val

		print 'goto table:', len(goto), 'entries'
		return goto


	def write_tables(self, name, path = '.', language = 'C'):
		fns = {
			'C':lrgen_c,
			'py':lrgen_py,
			'py2':lrgen_py,
			'python':lrgen_py,
			}
		fns[language](self, name, path)
