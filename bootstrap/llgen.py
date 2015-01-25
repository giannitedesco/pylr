from symbol import *
from grammar import Grammar

class LLGen(object):
	def __init__(self, g, start):
		super(LLGen, self).__init__()
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
		for nt in self.g.sym.values():
			if not isinstance(nt, NonTerminal):
				continue
			do_FOLLOW(nt, f)
		f['S'] = set([SymEof()])

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
				if SymEpsilon() in s:
					s -= set([SymEpsilon()])
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
