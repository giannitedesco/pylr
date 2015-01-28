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

def recurse(nt, node, g):

	if isinstance(node, AstUnary):
		op = recurse(nt, node.op, g)
	elif isinstance(node, AstBinary):
		a = recurse(nt, node.a, g)
		b = recurse(nt, node.b, g)

	if isinstance(node, AstSquares):
		# [A] -> A | epsilon
		s = nt.new_prime()
		g.symbol(s)
		p = Production(s)
		p.rule(op)
		p.rule([SymEpsilon()])
		g.production(p)
		return [p.nt]
	elif isinstance(node, AstClosure):
		# A* -> A | AA
		s = nt.new_prime()
		g.symbol(s)
		p = Production(s)
		p.rule(op)
		p.rule(op + op)
		g.production(p)
		return [p.nt]
	elif isinstance(node, AstChoice):
		# two new prime productions
		s = nt.new_prime()
		g.symbol(s)
		p = Production(s)
		p.rule(a)
		p.rule(b)
		g.production(p)
		return [p.nt]
	elif isinstance(node, AstLink):
		return [g[node.p.upper().replace(' ', '_')]]
	elif isinstance(node, AstConcat):
		return a + b
	else:
		print node
		assert(False)

def bnf_to_production(g, name, bnf):
	sym_name = name.upper().replace(' ', '_')
	sym = g[sym_name]

	#print '--', name
	#bnf.pretty_print()
	#print

	# First check the tree
	for node in bnf:
		if isinstance(node, AstLiteral):
			print 'rule "%s", literal "%s" not allowed'%(\
					name, node.literal)
			return

	r = recurse(sym, bnf, g)

	p = Production(sym)
	p.rule(r)
	g.production(p)

	return p 

def make_grammar(r, p = {}, s = {}):
	g = Grammar()
	for v in s.values():
		g.symbol(v)
	for k in p:
		g.symbol(NonTerminal(k.upper().replace(' ', '_')))
	for k,v in p.items():
		p = bnf_to_production(g, k, v.root)
		if p is None:
			return None
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

	g = make_grammar(nt[args.start], nt, s)
	if g is None:
		return EXIT_FAILURE

	# Add start symbol as RealStart then EOF
	start_sym = args.start.upper().replace(' ', '_')
	print 'Taking %s as start symbol'%start_sym
	g.augment(start_sym)

	# Add productions for any nonterminals without thmm
	g.construct_markers()

	# CNF step #1
	g.wrap_terminals()

	# CNF step #2
	g.normalize()

	# CNF step #4, #3 is handled by augment, above
	g.eliminate_epsilons()

	# CNF step #5
	g.eliminate_unit_rules()

	# now we are ready to eliminate left recursion
	#g.eliminate_left_recursion()

	p = LLGen(g, 'S')

	p.write_tables(args.base_name, path=args.includedir)

	return EXIT_SUCCESS

if __name__ == '__main__':
	from sys import argv
	raise SystemExit, main(argv)
