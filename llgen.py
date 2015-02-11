#!/usr/bin/python

from argparse import ArgumentParser
from bootstrap import *
from os.path import join

def read_file(fn):
	for l in iter(open(fn).readline, ''):
		yield l.rstrip('\r\n')

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
	for p in parse(fn, break_terminals=False):
		if tbl.has_key(p.name):
			raise Exception('%s multiply defind'%p.name)
		tbl[p.name] = p
	return tbl

def parse_terminals(fn, tbl = {}):
	for t in read_terminals(fn):
		tbl[t.name] = t
	return tbl

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
				default = 'grammar',
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

	s = {}
	nt = {}
	map(lambda x:parse_terminals(x, s), args.terminals)
	map(lambda x:parse_bnf(x, nt), args.files)

	g = Grammar().from_bnf(nt, s)
	if g is None:
		return EXIT_FAILURE

	# Add start symbol as RealStart then EOF
	start_sym = args.start.upper().replace(' ', '_')
	print 'Taking %s as start symbol'%start_sym
	#g.augment(start_sym)
	g.symbol(NonTerminal('S'))
	g.production(Production(g['S'], [g[start_sym], SymEof()]))

	# Add productions for any nonterminals without thmm
	g.construct_markers()

	g.remove_singletons()
	#g.dump()

	# CNF step #1
	#g.wrap_terminals()

	# CNF step #2
	#g.normalize()

	# CNF step #4, #3 is handled by augment, above
	#g.eliminate_epsilons()

	# CNF step #5
	#g.eliminate_unit_rules()


	# now we are ready to eliminate left recursion
	g.eliminate_left_recursion()

	#g.dump()

	g.left_factor()

	#g.dump()
	p = LLGen(g, 'S')

	p.write_tables(args.base_name, path=args.includedir)

	#for i in sorted(map(lambda x:x.nt, g.p.values())):
	#	print i.val, i
	return EXIT_SUCCESS

if __name__ == '__main__':
	from sys import argv
	raise SystemExit, main(argv)
