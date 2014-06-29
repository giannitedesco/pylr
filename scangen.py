#!/usr/bin/python
# vim: set fileencoding=utf8 :

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
	def finals(self, out = []):
		return
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
		if self.followpos is not None:
			print self, self.literal
		assert(self.followpos is None)
		self.followpos = set()

class AstEpsilon(AstNode):
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
	def copy(self):
		return AstEpsilon()

class AstAccept(AstNode):
	def __init__(self, name):
		self.rule_name = name
		super(AstAccept, self).__init__()
	def pretty_print(self, depth = 0):
		pfx = ' ' * depth * 2
		print '%s"# %s"'%(pfx, self.rule_name)
	def __str__(self):
		return '#(%s)'%self.rule_name
	def __repr__(self):
		return '#(%s)'%self.rule_name
	def _calc_nullable(self):
		return False
	def _calc_firstpos(self):
		return set({self.position})
	def _calc_lastpos(self):
		return set({self.position})
	def copy(self):
		return AstAccept(self.rule_name)
	def finals(self, out = []):
		out.append(self)

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
	def copy(self):
		return AstLiteral(self.literal)

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
		ret = tbl[self.p].root.resolve_links(tbl, v).copy()
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
	def copy(self):
		return self.__class__(self.op.copy())
	def finals(self, out = []):
		self.op.finals(out)

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
	def copy(self):
		return self.__class__(self.a.copy(), self.b.copy())
	def finals(self, out = []):
		self.a.finals(out)
		self.b.finals(out)
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
		return AstConcat(self.op, AstClosure(self.op.copy()))

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
	def __init__(self, name, final = False):
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

		self.final = final
		super(Production, self).__init__()

	def make_final(self):
		self.final = True
		if isinstance(self.root, AstConcat) and \
				isinstance(self.root.b, AstAccept):
			return
		self.root = AstConcat(self.root, AstAccept(self.name))

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
		if self.final:
			self.make_final()

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
			if t.name[0] == '@':
				name = t.name[1:]
				final = True
			else:
				name = t.name
				final = False
			p = Production(name, final)
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
		f.write('digraph %s {\n'%self.q(name))
		f.write('\tgraph[rankdir=LR]\n')
		f.write('\tnode [shape = circle];\n')
		f.write('\n')
		self.f = f
		super(Graph, self).__init__()
	def q(self, s):
		return '\"%s\"'%s
	def add_node(self, n, **kwargs):
		n = self.q(n)
		a = ' '.join(map(lambda (k,v):'%s=%s'%(k, self.q(v)),
				kwargs.items()))
		self.f.write('%s [%s];\n'%(n,a))
	def add_edge(self, pre, post, label):
		pre = self.q(pre)
		post = self.q(post)
		if label == ' ':
			self.f.write('%s -> %s [label="SPACE" color=red];\n'%(pre, post))
			return
		if label == '"':
			label = '\\"'
		label = self.q(label)
		self.f.write('%s -> %s [label=%s];\n'%(pre, post, label))
	def __del__(self):
		#print 'finishing graph'
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
	def state_type(self, num_states):
		if num_states + 1 < 2**8:
			t = 'uint8_t'
		elif num_states + 1 < 2**16:
			t = 'uin16_t'
		elif num_states + 1 < 2**32:
			t = 'uint32_t'
		else:
			t = 'uint64_t'
		self.write('typedef %s dfa_state_t;\n\n'%t)
	def transition_table(self, dfa):
		self.write('static const dfa_state_t ')
		self.write('trans[%u][0x100] = {\n'%(dfa.num_states + 1))
		for pre, d in dfa.trans.items():
			self.write('\t[ %u ] = {\n'%(pre + 1))
			for sym, post in sorted(d.items()):
				self.write('\t\t[\'%s\'] = %u,\n'%\
						(sym, post + 1))
			self.write('\t},\n')
		self.write('};\n\n')
	def accept_table(self, dfa):
		self.write('static const dfa_state_t ')
		self.write('accept[%u] = {\n'%(dfa.num_states + 1))
		for i in xrange(dfa.num_states):
			self.write('\t[ %u ] = %u,\n'%(
					i + 1,
					int(i in dfa.final)))
		self.write('};\n\n')

		self.write('static const dfa_state_t ')
		self.write('initial_state = %s;\n\n'%(dfa.initial + 1))
	def action_table(self, dfa):
		# TODO: optimise this
		self.write('static const char * ')
		self.write('action[%u] = {\n'%(dfa.num_states + 1))
		for i,v in dfa.final.items():
			self.write('\t[ %u ] = "%s",\n'%(
					i + 1,
					'|'.join(map(lambda x:x.rule_name,
						dfa.final[i]))))
		self.write('};\n\n')
	def __del__(self):
		self.close()

class Block(frozenset):
	def __init__(self, *args, **kwargs):
		super(Block, self).__init__(*args, **kwargs)
	def stable_refinement(self, func):
		#    partition b into subgroups such that two states s and t
		#    are in the same subgroup if and only if for all
		#    input symbols a, states s and t have transitions on a
		#    to states in the same group of S
		#    replace b in Snew by the set of all subgroups formed
		r = {}
		#print '', self
		for x in self:
			ff = func.get(x, frozenset({}))
			r.setdefault(ff, []).append(x)
		ret = map(Block, r.values())
		#for k,v in r.items():
		#	print '%s -> %s'%(k, v)
		#print self
		#print ret
		#print

		if len(ret) > 1:
			return ret
		return None

class Partition(set):
	def __init__(self, *args, **kwargs):
		self.item_mapping = {}
		super(Partition, self).__init__()
		if len(args):
			for x in args[0]:
				self.add(x)
	def add(self, item):
		assert(isinstance(item, Block))
		for x in item:
			assert(not self.item_mapping.has_key(x))
			self.item_mapping[x] = item
		super(Partition, self).add(item)
	def update(self, s):
		for item in s:
			self.add(item)
	def popitem(self):
		item = super(Partition, self).popitem()
		for x in item:
			assert(self.item_mapping.has_key(x))
			del self.item_mapping[x]
		return item
	def block_func(self, func):
		# re-write the function to indicate the block which the
		# item is bucketed in to
		f = {}
		for k,v in func.items():
			f[k] = frozenset(map(lambda (x,y):
					(x, self.item_mapping[y]),
					v.items()))
		return f
	def refine(self, func):
		# for each block in S
		ret = Partition()
		delta = False
		f = self.block_func(func)
		for b in self:
			new = b.stable_refinement(f)
			if new is None:
				ret.add(b)
				continue
			ret.update(new)
			delta = True
		if delta:
			return ret
		else:
			return None

class DFA(object):
	def __init__(self, r, tbl):
		# Check for cycles and resolve all production references
		r.root = r.root.resolve_links(tbl)

		r.make_final()

		# Flatten the tree and add the end-of-pattern marker
		r.root = r.root.flatten()

		# Display the flattened parse tree
		#print 'Parse tree for: %s'%r.name
		#r.root.pretty_print()

		# Construct the position table
		postbl = []
		r.root.leaves(postbl)
		for (pos, x) in zip(xrange(len(postbl)), postbl):
			x.position = pos

		print 'NFA has %u positions'%len(postbl)

		# Calculate the followpos function
		r.root.calc_followpos(postbl)
		#self.graph_followpos(postbl, r.root.firstpos())

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

		f = []
		r.root.finals(f)
		f = set(map(lambda x:x.position, f))

		# free up state sets and use the renumbering
		final = {}
		init = None
		while states:
			x, i = states.popitem()
			for fpos in f.intersection(x):
				final.setdefault(i,[]).append(\
					postbl[fpos])
			s[i] = None
			if x == initial:
				assert(init is None)
				init = i

		self.initial = init
		self.num_states = num_states
		self.final = final
		self.trans = trans

		print 'DFA has %u states and %u transitions'%(\
						self.num_states,
						self.num_trans)
		super(DFA, self).__init__()

	def shrink(self, obsolete):
		def new_number(v, o):
			ret = v
			for x in o:
				assert(v != x)
				if v < x:
					break
				if v > x:
					ret -= 1
			return ret

		def replace(v, o):
			return o.get(v, v)

		def renumber(r, o, s):
			ret = {}
			for k,v in r.items():
				assert(k not in obsolete)
				ret[k] = replace(v, o)
			r = ret
			for k,v in r.items():
				assert(k not in obsolete)
				ret[k] = new_number(v, s)
			return ret

		# renumber the states
		new = {}
		num_trans = 0
		s = sorted(obsolete.keys())
		for k, v in self.trans.items():
			v = renumber(v, obsolete, s)
			new[new_number(k, s)] = v
			num_trans += len(v)

		ni = new_number(self.initial, s)

		# now all final states in the group apply so we
		# need to do merge them in here as we renumber
		nf = {}
		for k,v in self.final.items():
			nk = obsolete.get(k, k)
			if nk != k:
				v = list(set(self.final.get(nk, []) + v))
			nk = new_number(nk, s)
			nf[nk] = v

		self.trans = new
		self.num_states -= len(obsolete)
		self.num_trans = num_trans
		self.initial = ni
		self.final = nf

	def optimize(self):
		# 1. partition in to final and non-final, S
		f = Block(self.final)
		nf = Block(set(xrange(self.num_states)).difference(f))
		S = Partition({f, nf})

		# 2. until fix-point
		while True:
			Snew = S.refine(dfa.trans)
			if Snew is None:
				break
			S = Snew

		obsolete = {}
		for b in S:
			if len(b) == 1:
				continue
			i = iter(b)
			v = i.next()
			for k in i:
				obsolete[k] = v
				try:
					del self.trans[k]
				except KeyError:
					pass

		self.shrink(obsolete)
		print 'DFA has %d states and %d transitions (optimal)'%(\
			self.num_states, self.num_trans)

	def dump_graph(self, fn):
		g = Graph('DFA', fn)

		for i in xrange(self.num_states):
			kwargs = {'label': str(i + 1)}
			if i in self.final:
				kwargs['shape'] = 'doublecircle'
				kwargs['color'] = 'red'
				kwargs['label'] = '\\n'.join(\
					map(lambda x:x.rule_name,
						self.final[i]))
			if i == self.initial:
				kwargs['color'] = 'blue'
			g.add_node(str(i + 1), **kwargs)

		for pre, d in dfa.trans.items():
			for sym, post in sorted(d.items()):
				g.add_edge(pre + 1, post + 1, sym)

	def dump_c(self, cfn, hfn):
		c = CFile(cfn, incl=[hfn])
		c.state_type(self.num_states)
		c.transition_table(self)
		c.accept_table(self)
		c.action_table(self)
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
		'__cr__': '\\r',
		'__tab__': '\\t',
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
	del tbl
	dfa.dump_graph('dfa.dot')
	dfa.optimize()
	for f in dfa.final.values():
		if len(f) <= 1:
			continue
		f = ', '.join(map(lambda x:x.rule_name, f))
		print 'Ambiguity: %s'%f
	dfa.dump_graph('optimized.dot')
	dfa.dump_c('lex.c', 'lex.h')
	raise SystemExit, 0
