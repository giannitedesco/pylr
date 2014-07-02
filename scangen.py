#!/usr/bin/python

from argparse import ArgumentParser
from bootstrap import parse, ParseTree, AstLiteral, DFA

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
		p = ParseTree(k)
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
	opts = ArgumentParser(description='Generate a tokenizer')
	opts.add_argument('production',
				metavar='production', type=str,
				help = 'Name of the root token rule')
	opts.add_argument('files', metavar='file', type=str, nargs='+',
				help = 'BNF file')
	opts.add_argument('--includedir',
				metavar = 'dir',
				type = str,
				default = '.',
				help = 'Directory to place header file')
	opts.add_argument('--srcdir',
				metavar = 'dir',
				type = str,
				default = '.',
				help = 'Directory to place C file')
	opts.add_argument('--dump-graph',
				action = 'store_true',
				default = False,
				help = 'Dump dotty graphs')
	opts.add_argument('--no-optimize',
				action = 'store_true',
				default = False,
				help = 'Disable DFA optimization')
	opts.add_argument('--base-name',
				metavar = 'basename',
				default = 'lex',
				type = str,
				help = 'Set the output filename')
	opts.add_argument

	args = opts.parse_args()

	tbl = {}
	builtin_productions(tbl)
	map(lambda x:parse_bnf(x, tbl), args.files)

	dfa = DFA(tbl[args.production], tbl)
	del tbl

	if args.dump_graph:
		dfa.dump_graph('dfa.dot')

	if not args.no_optimize:
		dfa.optimize()

	resolve_ambiguity(dfa)
	if not args.no_optimize and args.dump_graph:
		dfa.dump_graph('optimized.dot')

	dfa.dump_c(base_name = args.base_name,
			srcdir = args.srcdir,
			includedir = args.includedir)

	raise SystemExit, 0
