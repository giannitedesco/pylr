#!/usr/bin/python

from argparse import ArgumentParser
from bootstrap import *
from os.path import join

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
	def __init__(self, name = '', num_primes = 0):
		self.name = name.upper().replace(' ', '_')
		self.num_primes = num_primes
	def new_prime(self):
		self.num_primes += 1
		return self.name + '_PRIME%d'%self.num_primes

def recurse(node, s):
	if isinstance(node, AstUnary):
		op = recurse(node.op, s)
	elif isinstance(node, AstBinary):
		a = recurse(node.a, s)
		b = recurse(node.b, s)

	if isinstance(node, AstSquares):
		# [A] -> A | epsilon
		np = s.new_prime()
		print '%s -> %s'%(np, op)
		print '%s ->'%(np)
		return [np]
	elif isinstance(node, AstClosure):
		# A* -> A | AA
		np = s.new_prime()
		print '%s -> %s'%(np, op)
		print '%s -> %s %s'%(np, op, op)
		return
	elif isinstance(node, AstChoice):
		# two new prime productions
		np = s.new_prime()
		print '%s -> %s'%(np, a)
		print '%s -> %s'%(np, b)
		return [np]
	elif isinstance(node, AstLink):
		return [node.p.upper().replace(' ', '_')]
	elif isinstance(node, AstConcat):
		return a + b
	else:
		print node
		assert(False)

def bnf_to_production(name, bnf):
	print '--', name
	bnf.pretty_print()
	print

	# First check the tree
	for node in bnf:
		if isinstance(node, AstLiteral):
			print 'rule "%s", literal "%s" not allowed'%(\
					name, node.literal)
			return

	s = gState(name = name, num_primes = 0)
	r = recurse(bnf, s)
	print '%s -> %s'%(s.name, r)

	return True

def make_grammar(r, p = {}, s = {}):
	for k,v in p.items():
		if bnf_to_production(k, v.root) is None:
			return False
		print
	return True

def main(argv):
	EXIT_SUCCESS = 0
	EXIT_FAILURE = 1

	opts = ArgumentParser(description='Generate an LR parser table')
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

	s = {}
	nt = {}
	map(lambda x:parse_terminals(x, s), args.terminals)
	map(lambda x:parse_bnf(x, nt), args.files)

	if not make_grammar(nt[args.start], nt, s):
		return EXIT_FAILURE

	gfn = join(args.includedir, 'grammar.h')
	open(gfn, 'w')
	return EXIT_SUCCESS

if __name__ == '__main__':
	from sys import argv
	raise SystemExit, main(argv)
