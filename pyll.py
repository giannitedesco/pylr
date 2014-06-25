#!/usr/bin/python
# vim: set fileencoding=utf8 :

class Symbol(object):
	__val = 0
	def __init__(self, name, val = None):
		self.name = name
		if val is None:
			self.val = Symbol.__val
			Symbol.__val += 1
		else:
			self.val = val
		super(Symbol, self).__init__()
	def __str__(self):
		return '%s(%s)'%(self.__class__.__name__, self.name)
	def __repr__(self):
		return '%s(%s)'%(self.__class__.__name__, self.name)
	def __cmp__(a, b):
		if not isinstance(b, Symbol):
			raise TypeError
		return a.val.__cmp__(b.val)

class Epsilon(Symbol):
	__instance = None
	def __new__(cls, *args, **kwargs):
		if cls.__instance is None:
			cls.__instance = super(Epsilon, cls).__new__(cls, \
							*args, **kwargs)
		return cls.__instance
	def __init__(self):
		super(Epsilon, self).__init__('ε', -1)
	def __str__(self):
		return self.name
	def __repr__(self):
		return self.name

class Eof(Symbol):
	__instance = None
	def __new__(cls, *args, **kwargs):
		if cls.__instance is None:
			cls.__instance = super(Eof, cls).__new__(cls, \
							*args, **kwargs)
		return cls.__instance
	def __init__(self):
		super(Eof, self).__init__('$', -2)
	def __str__(self):
		return self.name
	def __repr__(self):
		return self.name

class Terminal(Symbol):
	def __init__(self, name):
		super(Terminal, self).__init__(name)

class NonTerminal(Symbol):
	def __init__(self, name):
		super(NonTerminal, self).__init__(name)

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
			if not isinstance(x, Symbol):
				raise TypeError
		self.rules.append(r)
	def __or__(a, b):
		if a.nt is not b.nt:
			raise ValueError
		p = Production(a.nt)
		p.rules = a.rules + b.rules
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
			self.t |= set([sym.val])
		elif isinstance(sym, NonTerminal):
			self.nt |= set([sym.val])
		else:
			raise TypeError
		self.sym[sym.name] = sym
		self.lookup[sym.val] = sym

	def production(self, p):
		if not isinstance(p, Production):
			raise TypeError
		try:
			p = self.p[p.nt.name] | p
		except KeyError:
			pass
		self.p[p.nt.name] = p

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
				self.p[s.name] = Production(s, [Epsilon()])

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
		#print p
		p.rules = new
		#print p
		self.production(np)
		np.rules.append([Epsilon()])
		self.symbol(prime)
		#print np 
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


class Parser(object):
	def __init__(self, g, start):
		super(Parser, self).__init__()
		self.g = g
		self.start = g[start]
		if not isinstance(self.g, Grammar):
			raise TypeError
		if not isinstance(self.start, NonTerminal):
			raise TypeError
		self.FIRST = self.construct_FIRST()
		self.FOLLOW = self.construct_FOLLOW()
		self.parse = self.construct_parse_table()

	def construct_FIRST(self):
		print 'Construct FIRST function..'
		# FIXME: Detect left recursion and abort
		def do_FIRST(nt, f):
			if f.has_key(nt.name):
				return f[nt.name]
			p = self.g.p[nt.name]
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
		for nt in self.g.sym.values():
			if not isinstance(nt, NonTerminal):
				continue
			do_FIRST(nt, f)

		#for k, v in sorted(f.items()):
		#	print ' ->', k, v

		return f

	def construct_FOLLOW(self):
		print 'Construct FOLLOW function..'
		def do_FOLLOW(nt, f):
			if f.has_key(nt.name):
				return f[nt.name]
			s = set()
			rec = []
			for p in self.g:
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
						if Epsilon() in tmp:
							rec.append(n)
						s |= tmp - set([Epsilon()])
					else:
						s |= set([n])
			f[nt.name] = s
			for n in sorted(set(rec)):
				s |= do_FOLLOW(n, f)
				f[nt.name] = s
			return s

		f = {}
		for nt in self.g.sym.values():
			if not isinstance(nt, NonTerminal):
				continue
			do_FOLLOW(nt, f)
		f['S'] = set([Eof()])

		for k, v in sorted(f.items()):
			if v & self.FIRST[k]:
				print ' FIRST/FOLLOW conflict ->', k,\
						v & self.FIRST[k]
			#print ' ->', k, v

		return f

	def construct_parse_table(self):
		print 'Construct parse table...'
		t = {}
		for p in self.g:
			for r in p:
				A = p.nt
				first = r[0]
				if isinstance(first, NonTerminal):
					s = self.FIRST[first.name]
				else:
					s = set([first])
				if Epsilon() in s:
					s -= set([Epsilon()])
					s |= self.FOLLOW[A.name]
				for a in s:
					if t.has_key((A,a)):
						print 'AMBIGUOUS', A, a
						continue
					t[A,a] = r
		#for k, v in t.items():
		#	print ' ->', k, v
		return t

	def write_tables(self, name, path='.'):
		from os.path import join

		fn = join(path, name + '.h')
		print 'writing', fn

		def cname(s):
			if s is Epsilon():
				return 'SYM_EPSILON'
			if s is Eof():
				return 'SYM_EOF'
			if isinstance(s, NonTerminal):
				return 'SYM_' + s.name.replace("'", '_PRIME')
			else:
				return s.name

		f = open(fn, 'w')
		f.write('#ifndef _%s_H\n'%name.upper())
		f.write('#define _%s_H\n'%name.upper())
		f.write('\n')

		f.write('#define SYM_EOF %d\n'%Eof().val)
		f.write('#define SYM_EPSILON %d\n'%Epsilon().val)
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

		f.write('struct parse_table_entry {\n')
		f.write('\tint A;\n')
		f.write('\tint a;\n')
		f.write('\tunsigned int len;\n')
		f.write('\tconst int *w;\n')
		f.write('};\n\n')
		f.write('static const struct parse_table_entry ' + \
			'parse_table[] = {\n')
		for (A,a), v in sorted(self.parse.items()):
			rtxt = '(int []){' + ', '.join(map(cname, v)) + '}'
			f.write('\t{%s, %s, %d,\n\t\t%s},\n'%(cname(A),
							cname(a),
							len(v),
							rtxt))
		f.write('};\n')

		f.write('\n')
		f.write('#endif /* _%s_H */\n'%name.upper())

def read_file(fn):
	f = open(fn)
	while True:
		l = f.readline()
		if l == '':
			break
		l = l.rstrip('\r\n')
		yield l

def read_terminals(fn):
	state = 0
	for l in read_file(fn):
		if not l:
			continue
		if state == 0:
			if l == 'enum tok {':
				state = 1
		elif state == 1:
			if l == '};':
				break
			l = l.split(',', 1)
			yield Terminal(l[0].strip())

def read_nonterminals(fn):
	for l in read_file(fn):
		if not l or l[0] == '#':
			continue
		yield l

def read_productions(g, fn):
	for l in read_file(fn):
		if not l or l[0] == '#':
			continue
		l = l.split()
		assert(l[1] == '->')
		if not l[2:]:
			r = [Epsilon()]
		else:
			r = map(lambda x:g[x], l[2:])
		p = Production(g[l[0]], r)
		yield p

def main(argv):
	EXIT_SUCCESS = 0
	EXIT_FAILURE = 1

	g = Grammar()
	for t in read_terminals('include/tok.h'):
		g.symbol(t)

	start_sym = None
	for nt in read_nonterminals(argv[1]):
		if start_sym == None:
			start_sym = nt
		g.symbol(NonTerminal(nt))

	for p in read_productions(g, argv[2]):
		g.production(p)

	# Add start symbol as RealStart then EOF
	print 'Taking %s as start symbol'%start_sym
	g.symbol(NonTerminal('S'))
	g.production(Production(g['S'], [g[start_sym], Eof()]))

	g.construct_markers()
	g.eliminate_left_recursion()
	p = Parser(g, 'S')

	p.write_tables('grammar', path='./include')

	return EXIT_SUCCESS

if __name__ == '__main__':
	from sys import argv
	raise SystemExit, main(argv)
