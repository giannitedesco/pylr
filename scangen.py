#!/usr/bin/python

from bootstrap import parse, Production, AstLiteral, DFA

def parse_bnf(fn, tbl = {}):
	for p in parse(fn):
		if tbl.has_key(p.name):
			raise Exception('%s multiply defind'%p.name)
		tbl[p.name] = p
	return tbl

def builtin_productions(tbl = {}):
	d = {
		'__lf__': '\\n',
		'__cr__': '\\r',
		'__tab__': '\\t',
		'__space__': ' ',
		'__hash__': '#',
	}
	for k, v in d.items():
		p = Production(k)
		p.root = AstLiteral(v)
		tbl[p.name] = p
	return tbl

if __name__ == '__main__':
	from sys import argv

	tbl = {}
	builtin_productions(tbl)
	map(lambda x:parse_bnf(x, tbl), argv[2:])

	dfa = DFA(tbl[argv[1]], tbl)
	del tbl

	dfa.dump_graph('dfa.dot')
	dfa.optimize()
	dfa.dump_graph('optimized.dot')

	for f in dfa.final.values():
		if len(f) <= 1:
			continue
		f = ', '.join(map(lambda x:x.rule_name, f))
		print 'Ambiguity: %s'%f

	dfa.dump_c('lex.c', 'lex.h')

	raise SystemExit, 0
