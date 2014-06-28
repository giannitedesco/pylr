#!/usr/bin/python
# vim: set fileencoding=utf8 :

from pydot import quote_if_necessary
from os.path import splitext, basename

def read_file(fn):
	f = open(fn)
	while True:
		l = f.readline()
		if l == '':
			break
		l = l.rstrip('\r\n')
		yield l

def lexemes(fn):
	for l in read_file(fn):
		if l == '':
			yield ''
			continue
		elif l[0] == '#':
			continue
		while l:
			l = l.lstrip()
			if not l:
				continue
			if len(l) > 1 and l[0] == '<':
				x = l.split('>', 1)
				if len(x) > 1:
					x[0] = x[0] + '>'
			else:
				x = l.split(None, 1)
				x2 = l.split('<', 1)

				if len(x2[0]) < len(x[0]) and len(x2[0]):
					x = x2
					x[1] = '<' + x[1]

			if len(x) == 2:
				if len(x[0]) > 3 and x[0][-3:] == '...':
					x[0] = x[0][0:-3]
					x[1] = '... ' + x[1]
				l = x[1]
				yield x[0]
			else:
				yield x[0]
				l = ''
				continue

class Token(object):
	def __init__(self, name):
		self.name = name
		super(Token, self).__init__()
	def __str__(self):
		return '%s(%s)'%(self.__class__.__name__, self.name)
	def __repr__(self):
		return '%s(%s)'%(self.__class__.__name__, self.name)

class TokHead(Token):
	def __init__(self, name):
		super(TokHead, self).__init__(name)
class TokIdentifier(Token):
	def __init__(self, name):
		super(TokIdentifier, self).__init__(name)
class TokLiteral(Token):
	def __init__(self, name):
		super(TokLiteral, self).__init__(name)

class TokOperator(Token):
	def __init__(self):
		super(TokOperator, self).__init__(None)
	def __str__(self):
		return '%s'%(self.__class__.__name__)
	def __repr__(self):
		return '%s'%(self.__class__.__name__)

class TokOpRewrite(TokOperator):
	def __init__(self):
		super(TokOpRewrite, self).__init__()
class TokOpUnary(TokOperator):
	def __init__(self):
		super(TokOpUnary, self).__init__()
class TokOpBinary(TokOperator):
	def __init__(self):
		super(TokOpBinary, self).__init__()
class TokOpLSquare(TokOperator):
	def __init__(self):
		self.confus = '['
		super(TokOpLSquare, self).__init__()
class TokOpRSquare(TokOperator):
	def __init__(self):
		self.confus = ']'
		super(TokOpRSquare, self).__init__()
class TokOpLBrace(TokOperator):
	def __init__(self):
		self.confus = '{'
		super(TokOpLBrace, self).__init__()
class TokOpRBrace(TokOperator):
	def __init__(self):
		self.confus = '}'
		super(TokOpRBrace, self).__init__()

class TokOpChoice(TokOpBinary):
	def __init__(self):
		self.confus = '|'
		super(TokOpChoice, self).__init__()

class TokOpEllipsis(TokOpUnary):
	def __init__(self):
		super(TokOpEllipsis, self).__init__()

class re_escape(dict):
	__f = None
	__e = set('[]()|*+.?\\')
	def escape(self, x):
		return ''.join(self[s] for s in x if s in self.keys())

	def __init__(self):
		if re_escape.__f is None:
			f = {}
			for x in map(chr, xrange(0, 0x100)):
				if x in re_escape.__e:
					f[x] = '\\' + x
				else:
					f[x] = x
			re_escape.__f = f
		super(re_escape, self).__init__(re_escape.__f)

def tokens(fn):
	def is_id(l):
		return len(l) > 2 and l[0] == '<' and l[-1:] == '>'
	state = 0
	for l in lexemes(fn):
		if l == '':
			state = 0
			continue
		if state == 0:
			if is_id(l):
				state = 1
				yield TokHead(l[1:-1])
			else:
				raise Exception("expected identifier")
		elif state == 1:
			if l == '::=':
				state = 2
				yield TokOpRewrite()
			else:
				raise Exception("expected ::=")
		elif state == 2:
			if is_id(l):
				yield TokIdentifier(l[1:-1])
			elif l == '|':
				yield TokOpChoice()
			elif l == '[':
				yield TokOpLSquare()
			elif l == ']':
				yield TokOpRSquare()
			elif l == '{':
				yield TokOpLBrace()
			elif l == '}':
				yield TokOpRBrace()
			elif l == '...':
				yield TokOpEllipsis()
			else:
				yield TokLiteral(l)

class AstNode(object):
	def __init__(self):
		self._nullable = None
		self._firstpos = None
		self._lastpos = None
		self.followpos = None
		super(AstNode, self).__init__()

	# default is for leaves
	def resolve_links(self, tbl = {}, v = set()):
		return self
	def flatten(self):
		return self
	def leaves(self, out = []):
		out.append(self)
	def nullable(self):
		if self._nullable is None:
			self._nullable = self._calc_nullable()
		return self._nullable
	def firstpos(self):
		if self._firstpos is None:
			self._firstpos = frozenset(self._calc_firstpos())
		return self._firstpos
	def lastpos(self):
		if self._lastpos is None:
			self._lastpos = frozenset(self._calc_lastpos())
		return self._lastpos
	def calc_followpos(self, postbl = []):
		self.followpos = set()

class AstEpsilon(AstNode):
	__instance = None
	def __new__(cls, *args, **kwargs):
		if cls.__instance is None:
			cls.__instance = super(AstEpsilon, cls).__new__(cls, \
							*args, **kwargs)
		return cls.__instance
	def __init__(self):
		super(AstEpsilon, self).__init__()
	def pretty_print(self, depth = 0):
		pfx = ' ' * depth * 2
		print '%s"ε"'%(pfx)
	def __str__(self):
		return 'ε'
	def __repr__(self):
		return 'ε'
	def leaves(self, out = []):
		# don't count epsilon leaves
		pass
	def _calc_nullable(self):
		return True
	def _calc_firstpos(self):
		return set()
	def _calc_lastpos(self):
		return set()

class AstAccept(AstNode):
	def __init__(self):
		super(AstAccept, self).__init__()
	def pretty_print(self, depth = 0):
		pfx = ' ' * depth * 2
		print '%s"#"'%(pfx)
	def __str__(self):
		return '#'
	def __repr__(self):
		return '#'
	def _calc_nullable(self):
		return False
	def _calc_firstpos(self):
		return set({self.position})
	def _calc_lastpos(self):
		return set({self.position})

class AstLiteral(AstNode):
	def __init__(self, literal):
		#f = re_escape()
		#self.literal = f.escape(literal)
		if literal == '\'':
			literal = '\\\''
		self.literal = literal
		super(AstLiteral, self).__init__()
	def pretty_print(self, depth = 0):
		pfx = ' ' * depth * 2
		print '%s"%s"'%(pfx, self.literal)
	def _calc_nullable(self):
		return False
	def _calc_firstpos(self):
		return set({self.position})
	def _calc_lastpos(self):
		return set({self.position})

class AstLink(AstNode):
	def __init__(self, p):
		self.p = p
		super(AstLink, self).__init__()
	def pretty_print(self, depth = 0):
		pfx = ' ' * depth * 2
		print '%s-> %s'%(pfx, self.p)
	def resolve_links(self, tbl = {}, v = set()):
		if self.p in v:
			raise Exception('Cycle on %s'%self.p)
		v.add(self.p)
		#print 'Resolving', self.p
		ret = tbl[self.p].root.resolve_links(tbl, v)
		v.remove(self.p)
		return ret;

class AstUnary(AstNode):
	def __init__(self, op):
		self.op = op
		super(AstUnary, self).__init__()
	def pretty_print(self, depth = 0):
		pfx = ' ' * depth * 2
		print '%s<%s>'%(pfx, self.__class__.__name__)
		self.op.pretty_print(depth + 1)
	def __str__(self):
		return '%s(%s)'%(self.__class__.__name__, self.op)
	def __repr__(self):
		return '%s(%s)'%(self.__class__.__name__, self.op)
	def resolve_links(self, tbl = {}, v = set()):
		self.op = self.op.resolve_links(tbl, v)
		return self
	def flatten(self):
		self.op = self.op.flatten()
		return self
	def leaves(self, out = []):
		self.op.leaves(out)
	def calc_followpos(self, postbl = []):
		self.op.calc_followpos(postbl)

class AstBinary(AstNode):
	def __init__(self, a, b):
		self.a = a
		self.b = b
		super(AstBinary, self).__init__()
	def pretty_print(self, depth = 0):
		pfx = ' ' * depth * 2
		print '%s<%s>'%(pfx, self.__class__.__name__)
		for x in [self.a, self.b]:
			x.pretty_print(depth + 1)
	def resolve_links(self, tbl = {}, v = set()):
		self.a = self.a.resolve_links(tbl, v)
		self.b = self.b.resolve_links(tbl, v)
		return self
	def flatten(self):
		self.a = self.a.flatten()
		self.b = self.b.flatten()
		return self
	def leaves(self, out = []):
		self.a.leaves(out)
		self.b.leaves(out)
	def calc_followpos(self, postbl = []):
		self.a.calc_followpos(postbl)
		self.b.calc_followpos(postbl)

	def __str__(self):
		return '%s(%s, %s)'%(self.__class__.__name__, self.a, self.b)
	def __repr__(self):
		return '%s(%s, %s)'%(self.__class__.__name__, self.a, self.b)

class AstEllipsis(AstUnary):
	def __init__(self, op):
		super(AstEllipsis, self).__init__(op)
	def flatten(self):
		# <x>... is equivalent <x>+, or <x><x>*
		super(AstEllipsis, self).flatten()
		return AstConcat(self.op, AstClosure(self.op))

class AstClosure(AstUnary):
	def __init__(self, op):
		super(AstClosure, self).__init__(op)
	def _calc_nullable(self):
		return True
	def _calc_firstpos(self):
		return self.op.firstpos()
	def _calc_lastpos(self):
		return self.op.lastpos()
	def calc_followpos(self, postbl = []):
		super(AstClosure, self).calc_followpos(postbl)
		for i in self.lastpos():
			postbl[i].followpos.update(self.firstpos())

class AstBraces(AstUnary):
	def __init__(self, op):
		super(AstBraces, self).__init__(op)
	def flatten(self):
		return self.op.flatten()

class AstSquares(AstUnary):
	def __init__(self, op):
		super(AstSquares, self).__init__(op)
	def flatten(self):
		# [ <x>... ] idiom is equivalent to <x>*
		if isinstance(self.op, AstEllipsis):
			return AstClosure(self.op.op.flatten())
		return AstChoice(self.op.flatten(), AstEpsilon())

class AstConcat(AstBinary):
	def __init__(self, a, b):
		super(AstConcat, self).__init__(a, b)
	def _calc_nullable(self):
		return self.a.nullable() and self.b.nullable()
	def _calc_firstpos(self):
		if self.a.nullable():
			return self.a.firstpos().union(self.b.firstpos())
		else:
			return self.a.firstpos()
	def _calc_lastpos(self):
		if self.b.nullable():
			return self.a.lastpos().union(self.b.lastpos())
		else:
			return self.b.lastpos()
	def calc_followpos(self, postbl = []):
		super(AstConcat, self).calc_followpos(postbl)
		for i in self.a.lastpos():
			postbl[i].followpos.update(self.b.firstpos())

class AstChoice(AstBinary):
	def __init__(self, a, b):
		super(AstChoice, self).__init__(a, b)
	def flatten(self):
		super(AstChoice, self).flatten()
		return self
	def _calc_nullable(self):
		return self.a.nullable() or self.b.nullable()
	def _calc_firstpos(self):
		return self.a.firstpos().union(self.b.firstpos())
	def _calc_lastpos(self):
		return self.a.lastpos().union(self.b.lastpos())

class Production(object):
	def __init__(self, name):
		self.name = name
		self.root = None
		self.pstack = []
		self.stack = []
		self.nchoice = 0
		self.natom = 0
		self.__ready = False
		self.__last = None
		self.__cb = {
				TokOpChoice: Production.__chose,
				TokLiteral: Production.__atom,
				TokIdentifier: Production.__atom,
				TokOpEllipsis: Production.__ellipsis,
				TokOpLSquare: Production.__lparen,
				TokOpRSquare: Production.__rparen,
				TokOpLBrace: Production.__lparen,
				TokOpRBrace: Production.__rparen,
		}

		super(Production, self).__init__()

	def __binop(self, cls):
		b = self.stack.pop()
		a = self.stack.pop()
		self.stack.append(cls(a, b))

	def __clear_stack(self):
		while self.natom > 1:
			self.natom -= 1
			self.__binop(AstConcat)
		else:
			self.natom -= 1
		while self.nchoice > 0:
			self.__binop(AstChoice)
			self.nchoice -= 1

	def __chose(self, tok):
		if not self.stack and not self.natom and not self.nchoice:
			try:
				tok.confus
				return
			except:
				pass
		assert(self.natom)
		while self.natom > 1:
			self.natom -= 1
			self.__binop(AstConcat)
		else:
			self.natom -= 1
		self.nchoice += 1

	def __atom(self, tok):
		if self.natom > 1:
			self.natom -= 1
			self.__binop(AstConcat)
		if isinstance(tok, TokIdentifier):
			self.stack.append(AstLink(tok.name))
		elif isinstance(tok, TokLiteral):
			self.stack.append(AstLiteral(tok.name))
		else:
			assert(False)
		self.natom += 1

	def __ellipsis(self, tok):
		assert(self.natom)
		op = self.stack.pop()
		self.stack.append(AstEllipsis(op))

	def __lparen(self, tok):
		if self.natom > 1:
			self.natom -= 1
			self.__binop(AstConcat)
		self.pstack.append((self.nchoice, self.natom))
		self.nchoice = 0
		self.natom = 0
		return

	def __rparen(self, tok):
		if not self.stack and not self.natom and not self.nchoice:
			try:
				tok.confus
				return
			except:
				pass
		assert(self.pstack)
		self.__clear_stack()
		self.nchoice, self.natom = self.pstack.pop()
		self.natom += 1
		op = self.stack.pop()
		if isinstance(tok, TokOpRSquare):
			self.stack.append(AstSquares(op))
		elif isinstance(tok, TokOpRBrace):
			self.stack.append(AstBraces(op))
		return

	def feed(self, tok):
		assert(isinstance(tok, Token))

		if not self.__ready:
			assert(isinstance(tok, TokOpRewrite))
			self.__ready = True
			return

		self.__last = tok
		c = self.__cb[tok.__class__]
		c(self, tok)
	
	def eof(self):
		self.__clear_stack()
		if self.stack:
			self.root = self.stack.pop()
		else:
			assert(self.__last is not None)
			self.root = AstLiteral(self.__last.confus)

	def __str__(self):
		return '%s(%s)'%(self.__class__.__name__, self.name)
	def __repr__(self):
		return '%s(%s)'%(self.__class__.__name__, self.name)

def productions(fn):
	p = None
	for t in tokens(fn):
		if isinstance(t, TokHead):
			if p is not None:
				p.eof()
				yield p
			p = Production(t.name)
		elif isinstance(t, TokLiteral):
			map(lambda x:p.feed(TokLiteral(x)), t.name)
		else:
			p.feed(t)
	if p is not None:
		p.eof()
		yield p

class Graph(object):
	def __init__(self, name, fn):
		f = open(fn, 'w')
		f.write('digraph %s {\n'%quote_if_necessary(name))
		f.write('\tgraph[rankdir=LR]\n')
		f.write('\tnode [shape = circle];\n')
		f.write('\n')
		self.f = f
		super(Graph, self).__init__()
	def add_node(self, n, **kwargs):
		n = quote_if_necessary(n)
		a = ' '.join(map(lambda (k,v):'%s=%s'%(k, quote_if_necessary(v)),
				kwargs.items()))
		self.f.write('%s [label=%s %s];\n'%(n,n,a))
	def add_edge(self, pre, post, label):
		pre = quote_if_necessary(pre)
		post = quote_if_necessary(post)
		if label == ' ':
			self.f.write('%s -> %s [label="SPACE" color=red];\n'%(pre, post))
			return
		if label == '"':
			label = '\\"'
		label = quote_if_necessary(label)
		self.f.write('%s -> %s [label=%s];\n'%(pre, post, label))
	def __del__(self):
		print 'finishing graph'
		self.f.write('}\n')
		self.f.close()

class HFile(file):
	def __include_guard_top(self):
		self.write('#ifndef %s\n'%self.inclguard)
		self.write('#define %s\n'%self.inclguard)
	def __include_guard_bottom(self):
		self.write('\n#endif /* %s */\n'%self.inclguard)
	def __init__(self, fn):
		super(HFile, self).__init__(fn, 'w')
		self.write('/* auto generated by scangen.py */\n')
		self.inclguard = '_%s_H'%basename(splitext(fn)[0]).upper()
		self.__include_guard_top()
	def __del__(self):
		self.__include_guard_bottom()
		self.close()

class CFile(file):
	def sysinclude(self, path):
		self.write('#include <%s>\n'%path)
	def include(self, path):
		self.write('#include "%s"\n'%path)
	def newline(self):
		self.write('\n')
	def __init__(self, fn, incl=[], sysincl=[]):
		super(CFile, self).__init__(fn, 'w')
		self.write('/* auto generated by scangen.py */\n')
		self.sysinclude('stdint.h')
		for x in sysincl:
			self.sysinclude(x)
			self.newline()
		for x in incl:
			self.include(x)
		if incl:
			self.newline()
	def transition_table(self, dfa):
		if len(dfa.states) < 2**8:
			t = 'uint8_t'
		else:
			t = 'unsigned int'
		self.write('static const %s '%t)
		self.write('trans[%u][0x100] = {\n'%(len(dfa.states) + 1))
		for pre, d in dfa.trans.items():
			self.write('\t[ %u ] = {\n'%(pre + 1))
			for sym, post in sorted(d.items()):
				self.write('\t\t[\'%s\'] = %u,\n'%\
						(sym, post + 1))
			self.write('\t},\n')
		self.write('};\n\n')
	def state_table(self, dfa):
		if len(dfa.states) < 2**8:
			t = 'uint8_t'
		else:
			t = 'unsigned int'
		self.write('static const struct {\n')
		self.write('\tuint8_t accept;\n')
		self.write('}state[%u] = {\n'%(len(dfa.states) + 1))
		for (x, i) in dfa.states.items():
			self.write('\t[ %u ] = {\n'%(i + 1))
			self.write('\t\t.accept = %u,\n'%(int(x == dfa.final)))
			self.write('\t},\n')
		self.write('};\n\n')

		self.write('static const %s initial_state = %s;\n\n'%\
				(t, dfa.states[dfa.initial] + 1))
	def __del__(self):
		self.close()

class DFA(object):
	def graph_followpos(self, postbl, initials):
		g = Graph('NFA', 'nfa.dot')
		for i, p in zip(xrange(len(postbl)), postbl):
			kwargs = {}
			if isinstance(p, AstAccept):
				kwargs['shape'] = 'doublecircle'
				kwargs['color'] = 'red'
			if i in initials:
				kwargs['color'] = 'blue'
			g.add_node(str(i), **kwargs)
			for f in p.followpos:
				g.add_edge(str(i), str(f),
						p.literal)
	def __init__(self, r, tbl):
		# Don't let the root be a reference FIXME
		while isinstance(r.root, AstLink):
			r.root = tbl[r.root.p].root

		# Check for cycles and resolve all production references
		r.root = r.root.resolve_links(tbl)

		# Flatten the tree and add the end-of-pattern marker
		r.root = AstConcat(r.root.flatten(), AstAccept())

		# Display the flattened parse tree
		print 'Parse tree for: %s'%r.name
		r.root.pretty_print()

		# Construct the position table
		postbl = []
		r.root.leaves(postbl)
		for (pos, x) in zip(xrange(len(postbl)), postbl):
			x.position = pos

		# Calculate the followpos function
		r.root.calc_followpos(postbl)
		self.graph_followpos(postbl, r.root.firstpos())

		initial = r.root.firstpos().union(frozenset({}))
		states = {}
		Dstate = set({initial})
		Dtrans = {}

		num_states = 0
		while len(Dstate):
			S = Dstate.pop()
			assert(S not in states)
			states[S] = num_states # mark
			num_states += 1

			#print 'S = %s'%S
			S2 = filter(lambda x:isinstance(postbl[x],
					AstLiteral), S)
			SS = map(lambda x:(postbl[x].literal, x), S2)
			s = {}
			for a, p in SS:
				s.setdefault(a, set()).add(p)

			for a, v in s.items():
				U = set()
				for p in v:
					U.update(postbl[p].followpos)
				U = frozenset(U)

				if U not in Dstate and U not in states:
					Dstate.add(U)

				Dtrans[S,a] = U

		# Re-number transitions
		trans = {}
		self.num_trans = 0
		while Dtrans:
			((pre,sym),post) = Dtrans.popitem()
			trans.setdefault(states[pre], {})[sym] = \
					states[post]
			self.num_trans += 1

		# TODO: forget about state sets and use renumbering
		for x in states.keys():
			if r.root.b.position in x:
				final = x

		self.initial = initial
		self.final = final
		self.states = states
		self.trans = trans

		print 'DFA has %u states and %u transitions'%(len(self.states),
							self.num_trans)
		super(DFA, self).__init__()

	def dump_graph(self, fn):
		g = Graph('DFA', fn)

		for (x, i) in self.states.items():
			kwargs = {}
			if x == self.final:
				kwargs['shape'] = 'doublecircle'
				kwargs['color'] = 'red'
			if x == self.initial:
				kwargs['color'] = 'blue'
			kwargs['label'] = str(i + 1)
			g.add_node(str(i + 1), **kwargs)

		for pre, d in dfa.trans.items():
			for sym, post in sorted(d.items()):
				g.add_edge(pre + 1, post + 1, sym)

	def dump_c(self, cfn, hfn):
		c = CFile(cfn, incl=[hfn])
		c.transition_table(self)
		c.state_table(self)
		h = HFile(hfn)

def parse_bnf(fn, tbl = {}):
	for p in productions(fn):
		if tbl.has_key(p.name):
			raise Exception('%s multiply defind'%p.name)
		tbl[p.name] = p
	return tbl

def builtin_productions(tbl = {}):
	d = {
		'__lf__': '\\n',
		'__isspace__': '\\s',
		'__space__': ' ',
	}
	for k, v in d.items():
		p = Production(k)
		p.root = AstLiteral(v)
		tbl[p.name] = p
	return tbl

if __name__ == '__main__':
	from sys import argv, setrecursionlimit
	from resource import setrlimit, RLIMIT_STACK

	setrecursionlimit(100000)
	setrlimit(RLIMIT_STACK, (1 << 29, -1))

	tbl = {}
	builtin_productions(tbl)
	map(lambda x:parse_bnf(x, tbl), argv[2:])
	dfa = DFA(tbl[argv[1]], tbl)
	dfa.dump_graph('dfa.dot')
	dfa.dump_c('lex.c', 'lex.h')
	raise SystemExit, 0
