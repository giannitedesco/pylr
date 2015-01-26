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

class gState(object):
	def __init__(self, g, name = '', num_primes = 0):
		self.g = g
		self.name = name.upper().replace(' ', '_')
		self.num_primes = num_primes
	def new_prime(self):
		self.num_primes += 1
		name = self.name + '_PRIME%d'%self.num_primes
		assert(not self.g.sym.has_key(name))
		p = Production(NonTerminal(name))
		return p

def recurse(node, s):
	if isinstance(node, AstUnary):
		op = recurse(node.op, s)
	elif isinstance(node, AstBinary):
		a = recurse(node.a, s)
		b = recurse(node.b, s)

	if isinstance(node, AstSquares):
		# [A] -> A | epsilon
		p = s.new_prime()
		p.rule(op)
		p.rule([SymEpsilon()])
		s.g.production(p)
		return [p.nt]
	elif isinstance(node, AstClosure):
		# A* -> A | AA
		p = s.new_prime()
		p.rule(op)
		p.rule(op + op)
		s.g.production(p)
		return [p.nt]
	elif isinstance(node, AstChoice):
		# two new prime productions
		p = s.new_prime()
		p.rule(a)
		p.rule(b)
		s.g.production(p)
		return [p.nt]
	elif isinstance(node, AstLink):
		return [s.g[node.p.upper().replace(' ', '_')]]
	elif isinstance(node, AstConcat):
		return a + b
	else:
		print node
		assert(False)

def bnf_to_production(g, name, bnf):
	#print '--', name
	#bnf.pretty_print()
	#print

	# First check the tree
	for node in bnf:
		if isinstance(node, AstLiteral):
			print 'rule "%s", literal "%s" not allowed'%(\
					name, node.literal)
			return

	s = gState(g, name = name, num_primes = 0)
	r = recurse(bnf, s)

	p = Production(g[name.upper().replace(' ', '_')])
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

	g.symbol(NonTerminal('S'))
	g.production(Production(g['S'], [g[start_sym], SymEof()]))

	g.eliminate_unit_rules()
	g.construct_markers()
	g.eliminate_left_recursion()

	p = LLGen(g, 'S')

	p.write_tables(args.base_name, path=args.includedir)

	return EXIT_SUCCESS

if __name__ == '__main__':
	from sys import argv
	raise SystemExit, main(argv)
