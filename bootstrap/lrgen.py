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

		self.numbering = self.number_states(self.C)
		self.action = self.construct_action_table()
		self.goto = self.construct_goto()
		self.initial = self.initial_state()

	def number_states(self, C):
		numbering = {}
		for i, I in enumerate(C):
			print i, I
			numbering[I] = i
		print
		print
		return numbering

	def start_item(self):
		s = self.g.p['S']
		return Item(s.rules[0], head = s.nt, pos = 0)

	def end_item(self):
		s = self.g.p['S']
		return Item(s.rules[0], head = s.nt, pos = 1)

	def initial_state(self):
		s = self.start_item()
		for (I, inum) in self.numbering.items():
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
		print 'construct canonical LR(0) collection'
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

		action = {}

		for (I, inum) in self.numbering.items():
			if self.end_item() in I:
				key = (inum, SymEof())
				val = ('accept', True)
				if action.has_key(key):
					assert(val == action[key])

				action[key] = val

			for i in I:
				try:
					nxt = i[i.pos]
				except IndexError:
					print i, self.g.FOLLOW[i.head.name]
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
				val = self.numbering.get(g, None)
				if val is None:
					continue
				val = ('shift', val)
				key = inum, nxt

				if action.has_key(key):
					assert(val == action[key])

				action[key] = val

		#for k, v in sorted(action.items()):
		#	print k, '->', v

		print 'action table:', len(action), 'entries'
		return action

	def construct_goto(self):
		print 'Construct goto table...'

		goto = {}
		for (I, inum) in self.numbering.items():
			for t in self.g.reachables():
				if not isinstance(t, NonTerminal):
					continue
				g = self.GOTO(I,t)
				out = self.numbering.get(g, None)
				if out is None:
					continue
				key = (inum, t)
				val = out
				goto[key] = val

		print 'goto table:', len(goto), 'entries'
		return goto

	def write_sym_defs(self, f):
		f.write('#define SYM_EOF %d\n'%SymEof().val)
		f.write('#define SYM_EPSILON %d\n'%SymEpsilon().val)
		for nt in sorted(self.g.sym.values()):
			if not isinstance(nt, NonTerminal):
				continue
			f.write('#define %s %d\n'%(nt.cname(), nt.val))

	def write_sym_names(self, f):
		f.write('static inline const char *sym_name(int sym)\n')
		f.write('{\n')
		f.write('\tswitch(sym) {\n')
		for nt in sorted(self.g.sym.values()):
			f.write('\tcase %s:\n'%(nt.cname()))
			f.write('\t\treturn "%s";\n'%(nt.name))
		f.write('\tcase SYM_EOF:\n')
		f.write('\t\treturn "EOF";\n')
		f.write('\tcase SYM_EPSILON:\n')
		f.write('\t\treturn "EPSILON";\n')
		f.write('\tdefault:\n')
		f.write('\t\treturn "<<UNKNOWN>>";\n')
		f.write('\t}\n')
		f.write('}\n')

	def write_goto_table(self, f):
		print >>f, 'static const struct {'
		print >>f, '\tunsigned int i;'
		print >>f, '\tint A;'
		print >>f, '\tunsigned int j;'
		print >>f, '}GOTO[] = {'
		for ((i, A), j) in sorted(self.goto.items()):
			print >> f, '\t{ %d, %s, %d },'%(i, A.cname(), j)
		print >>f, '};'

	def write_action_table(self, f):
		print >>f, '#define ACTION_ERROR\t0'
		print >>f, '#define ACTION_ACCEPT\t1'
		print >>f, '#define ACTION_SHIFT\t2'
		print >>f, '#define ACTION_REDUCE\t3'
		print >>f
		print >>f, 'struct shift_move {'
		print >>f, '\tunsigned int t;'
		print >>f, '};'
		print >>f
		print >>f, 'struct reduce_move {'
		print >>f, '\tunsigned int len;'
		print >>f, '\tint head;'
		print >>f, '\tconst char *reduction;'
		print >>f, '};'
		print >>f
		print >>f, 'static const struct action {'
		print >>f, '\tunsigned int i;'
		print >>f, '\tint a;'
		print >>f, '\tuint8_t action;;'
		print >>f, '\tunion {'
		print >>f, '\t\tstruct shift_move shift;'
		print >>f, '\t\tstruct reduce_move reduce;'
		print >>f, '\t}u;'
		print >>f, '}ACTION[] = {'
		for ((i,a), (c, v)) in sorted(self.action.items()):
			print >>f, '\t{'
			print >>f, '\t\t.i = %d,'%i
			print >>f, '\t\t.a = %s,'%a.cname()
			print >>f, '\t\t.action = ACTION_%s,'%c.upper()
			if c == 'shift':
				print >>f, '\t\t.u.shift = { .t = %d },'%v
			elif c == 'reduce':
				l = len(v[1])
				r = '%s -> %s'%(v[0].name,
					' '.join(map(lambda x:x.name, v[1])))
				print >>f, '\t\t.u.reduce = {'
				print >>f, '\t\t\t.len = %d,'%l
				print >>f, '\t\t\t.head = %s,'%v[0].cname()
				print >>f, '\t\t\t.reduction = "%s",'%r
				print >>f, '\t\t},'
			print >>f, '\t},'
		print >>f, '};'

	def write_tables(self, name, path='.'):
		from os.path import join

		fn = join(path, name + '.h')
		print 'writing', fn

		f = open(fn, 'w')
		f.write('#ifndef _%s_H\n'%name.upper())
		f.write('#define _%s_H\n'%name.upper())
		f.write('\n')

		self.write_sym_defs(f)
		f.write('\n')

		self.write_sym_names(f)
		f.write('\n')

		f.write('#define INITIAL_STATE %d\n'%self.initial)
		f.write('\n')

		self.write_action_table(f)
		f.write('\n')

		self.write_goto_table(f)
		f.write('\n')

		f.write('#endif /* _%s_H */\n'%name.upper())
