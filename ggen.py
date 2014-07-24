#!/usr/bin/python

from argparse import ArgumentParser
from bootstrap import *

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

def parse_bnf(fn, tbl = {}):
	for p in parse(fn):
		if tbl.has_key(p.name):
			raise Exception('%s multiply defind'%p.name)
		tbl[p.name] = p
	return tbl

def parse_terminals(fn, tbl = {}):
	for t in read_terminals(fn):
		tbl[t.name] = t
	return tbl

def normalize(name, r, g, tbl):
	if isinstance(r, AstLink):
		if isinstance(tbl[r.p], ParseTree):
			ret = normalize(tbl[r.p].symbol_name(),
					tbl[r.p].root, g, tbl)
			print ret
			return [r.symbol_name()]
		else:
			return [r.p]
	elif isinstance(r, AstLiteral):
		print 'Error: %s has literals'%(r.name)
		raise ValueError
	elif isinstance(r, AstConcat):
		a = normalize(name, r.a, g, tbl)
		b = normalize(name, r.b, g, tbl)
		return a + b
	elif isinstance(r, AstChoice):
		a = isinstance(r.a, AstLink) and \
				tbl[r.a.p].symbol_name() or 'NOTHING'
		b = isinstance(r.b, AstLink) and \
				tbl[r.b.p].symbol_name() or 'NOTHING'
		return ['%s_OR_%s'%(a, b)]
	else:
		#p = Production(g.get(name))
		#g.production(p)
		print name
		r.pretty_print()
		print
		return []

def make_grammar(r, tbl = {}):
	for p in tbl.values():
		if isinstance(p, ParseTree):
			p.root = p.root.flatten()

	g = Grammar()
	print r.symbol_name()
	r.root.pretty_print()
	print
	ret = normalize(r.symbol_name(), r.root, g, tbl)
	print ret

	return g

def main(argv):
	EXIT_SUCCESS = 0
	EXIT_FAILURE = 1

	opts = ArgumentParser(description='Generate an LL parser table')
	opts.add_argument('start',
				metavar='production', type=str,
				help = 'Name of the start nonterminal')
	opts.add_argument('files', metavar='file', type=str, nargs='+',
				help = 'BNF file')
	opts.add_argument('--base-name',
				metavar = 'basename',
				default = 'lex',
				type = str,
				help = 'Set the output filename')
	opts.add_argument('--includedir',
				metavar = 'dir',
				type = str,
				default = '.',
				help = 'Directory to place header file')
	opts.add_argument('--terminals',
				metavar = 'dir',
				action = 'append',
				type = str,
				default = [],
				help = 'Read token terminals')


	args = opts.parse_args()

	tbl = {}
	map(lambda x:parse_terminals(x, tbl), args.terminals)
	map(lambda x:parse_bnf(x, tbl), args.files)

	g = make_grammar(tbl[args.start], tbl)
	for x in g:
		print x
	return EXIT_SUCCESS

if __name__ == '__main__':
	from sys import argv
	raise SystemExit, main(argv)
