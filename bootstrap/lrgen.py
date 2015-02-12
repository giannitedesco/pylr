from symbol import *
from grammar import Grammar

# This should be the rule class, remove pos
# item should be a pair of ints, (rule_idx, pos)
class Item(tuple):
	def __new__(cls, arg = [], **kwargs):
		if arg and arg[-1] is SymEof():
			arg = arg[:-1]
		return super(Item, cls).__new__(cls, arg)
	def __init__(self, arg = [], **kwargs):
		self.head = kwargs.pop('head')
		self.pos = int(kwargs.pop('pos'))
		if arg and arg[-1] is SymEof():
			arg = arg[:-1]
		super(Item, self).__init__(arg, **kwargs)
		assert(self.pos >= 0)
		assert(self.pos <= len(self))
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
		r = cmp(tuple(a), tuple(b))
		if r:
			return r
		return cmp(a.pos, b.pos)
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
		self.g = g
		self.start = g[start]
		if not isinstance(self.g, Grammar):
			raise TypeError
		if not isinstance(self.start, NonTerminal):
			raise TypeError

		self.C = self.canonical_collection()

		self.g.eliminate_left_recursion()
		self.g.construct_FOLLOW()

		self.parse = self.construct_action_table()

	def start_item(self):
		s = self.g.p['S']
		return Item(s.rules[0], head = s.nt, pos = 0)

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
				for r in self.g.p[B.name]:
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
		C = set()

		C.add(self.closure(frozenset([self.start_item()])))

		fixpoint = False
		while not fixpoint:
			fixpoint = True

			for I in list(C):
				for X in self.g.reachables():
					g = self.GOTO(I, X)
					if g and g not in C:
						C.add(g)
						fixpoint = False
		return frozenset(C)

	def construct_action_table(self):
		print 'Construct action table...'

		numbering = {}
		for i, I in enumerate(self.C):
			numbering[I] = i

		action = {}

		for (I, inum) in numbering.items():
			if self.start_item() in I:
				key = (inum, SymEof())
				val = ('accept', True)
				if action.has_key(key):
					assert(val == action[key])

				action[key] = val

			for i in I:
				try:
					nxt = i[i.pos]
				except IndexError:
					if len(i) == 1 and i[0] is SymEpsilon():
						continue
					if i.head is SymStart():
						continue
					for a in self.g.FOLLOW[i.head.name]:
						key = (inum, a)
						val = ('reduce', (i.head, tuple(i)))
						if action.has_key(key):
							assert(val == action[key])
						action[key] = val
					continue
				g = self.GOTO(I, nxt)
				val = numbering.get(g, None)
				if val is None:
					continue
				val = ('shift', val)
				key = inum, nxt

				if action.has_key(key):
					assert(val == action[key])

				action[key] = val

		for k, v in sorted(action.items()):
			print k, '->', v

		print len(action), 'entries'
		return action

	def write_tables(self, name, path='.'):
		from os.path import join

		fn = join(path, name + '.h')
		print 'writing', fn

		def cname(s):
			if s is SymEpsilon():
				return 'SYM_EPSILON'
			if s is SymEof():
				return 'SYM_EOF'
			if isinstance(s, NonTerminal):
				return 'SYM_' + s.name.replace("'", '_PRIME')
			else:
				return s.name

		f = open(fn, 'w')
		f.write('#ifndef _%s_H\n'%name.upper())
		f.write('#define _%s_H\n'%name.upper())
		f.write('\n')

		f.write('#define SYM_EOF %d\n'%SymEof().val)
		f.write('#define SYM_EPSILON %d\n'%SymEpsilon().val)
		for nt in sorted(self.g.sym.values()):
			if not isinstance(nt, NonTerminal):
				continue
			f.write('#define %s %d\n'%(cname(nt), nt.val))
		f.write('\n')

		f.write('static inline const char *sym_name(int sym)\n')
		f.write('{\n')
		f.write('\tswitch(sym) {\n')
		for nt in sorted(self.g.sym.values()):
			f.write('\tcase %s:\n'%(cname(nt)))
			f.write('\t\treturn "%s";\n'%(cname(nt)))
		f.write('\tcase SYM_EOF:\n')
		f.write('\t\treturn "EOF";\n')
		f.write('\tcase SYM_EPSILON:\n')
		f.write('\t\treturn "EPSILON";\n')
		f.write('\tdefault:\n')
		f.write('\t\treturn "UNKNOWN";\n')
		f.write('\t}\n')
		f.write('}\n\n')

		f.write('\n')
		f.write('#endif /* _%s_H */\n'%name.upper())
