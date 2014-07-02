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
		'__lt__': '<',
		'__gt__': '>',
		'__lsq__': '[',
		'__rsq__': ']',
		'__lbr__': '{',
		'__rbr__': '}',
		'__vbar__': '|',
	}
	for k, v in d.items():
		p = Production(k)
		p.root = AstLiteral(v)
		tbl[p.name] = p
	return tbl

def resolve_ambiguity(dfa):
	nf = {}
	while dfa.final:
		i, f = dfa.final.popitem()
		if len(f) <= 1:
			nf[i] = f
			continue
		x = sorted([(x.lineno, x) for x in f])
		f = ', '.join(map(lambda x:'%s'%x.rule_name, sorted(f)))
		print 'Ambiguity: %s, picked %s'%(f, x[0][1].rule_name)
		#print x[0][1]
		nf[i] = [x[0][1]]
	dfa.final = nf

if __name__ == '__main__':
	from sys import argv

	tbl = {}
	builtin_productions(tbl)
	map(lambda x:parse_bnf(x, tbl), argv[2:])

	dfa = DFA(tbl[argv[1]], tbl)
	del tbl

	dfa.dump_graph('dfa.dot')
	dfa.optimize()

	resolve_ambiguity(dfa)
	dfa.dump_graph('optimized.dot')

	dfa.dump_c('lex.c', 'lex.h', includedir='./include')

	raise SystemExit, 0
