from symbol import *
from grammar import Grammar

# This should be the rule class, remove pos
# item should be a pair of ints, (rule_idx, pos)
class Item(tuple):
	def __new__(cls, *args, **kwargs):
		return super(Item, cls).__new__(cls, *args)
	def __init__(self, *args, **kwargs):
		self.head = kwargs.pop('head')
		self.pos = int(kwargs.pop('pos'))
		super(Item, self).__init__(*args, **kwargs)
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
		#self.g.construct_FIRST()
		#self.g.construct_FOLLOW()
		self.items = self.construct_items()
		self.parse = self.construct_parse_table()

		s = self.g.p['S']
		print self.closure(set([Item(s.rules[0], head = s.nt, pos = 0)]))

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
		return J

	def construct_items(self):
		print 'Constructing items'

		I = set()

		for nt in self.g.reachables():
			if not self.g.p.has_key(nt.name):
				continue
			for r in self.g.p[nt.name]:
				if r == [SymEpsilon()]:
					i = Item(head = nt, pos = 0)
					I.add(i)
					print i
					continue
				for p in xrange(len(r) + 1):
					i = Item(r, head = nt, pos = p)
					I.add(i)
					print i

		return I

	def construct_parse_table(self):
		print 'Construct parse table...'

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
