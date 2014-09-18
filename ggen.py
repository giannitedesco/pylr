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
	for p in parse(fn, break_terminals=False):
		if tbl.has_key(p.name):
			raise Exception('%s multiply defind'%p.name)
		tbl[p.name] = p
	return tbl

def parse_terminals(fn, tbl = {}):
	for t in read_terminals(fn):
		tbl[t.name] = t
	return tbl

def make_grammar(r, tbl = {}):
	for r in tbl.values():
		r.root.pretty_print()
		print

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

	t = {}
	nt = {}
	map(lambda x:parse_terminals(x, t), args.terminals)
	map(lambda x:parse_bnf(x, nt), args.files)

	make_grammar(nt[args.start], nt)
	return EXIT_SUCCESS

if __name__ == '__main__':
	from sys import argv
	raise SystemExit, main(argv)
