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
		self.g.construct_FIRST()
		self.g.construct_FOLLOW()
		self.parse = self.construct_parse_table()

	def construct_parse_table(self):
		print 'Construct parse table...'
		t = {}
		for p in self.g:
			for r in p:
				A = p.nt
				first = r[0]
				if isinstance(first, NonTerminal):
					s = self.g.FIRST[first.name]
				else:
					s = set([first])
				if SymEpsilon() in s:
					s -= set([SymEpsilon()])
					s |= self.g.FOLLOW[A.name]
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
