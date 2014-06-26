#!/usr/bin/python
# vim: set fileencoding=utf8 :

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
		super(AstNode, self).__init__()
	def __str__(self):
		return '%s'%(self.__class__.__name__)
	def __repr__(self):
		return '%s'%(self.__class__.__name__)

	# default is for leaves
	def check_for_cycles(self, tbl = {}, v = set()):
		return False
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
			self._firstpos = self._calc_firstpos()
		return self._firstpos
	def lastpos(self):
		if self._lastpos is None:
			self._lastpos = self._calc_lastpos()
		return self._lastpos

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
		# escape any regex characters here
		f = re_escape()
		self.literal = f.escape(literal)
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

class AstSet(AstNode):
	def __init__(self, raw_regex, esc = True):
		# Allow raw regex expressions here
		self.raw_regex = raw_regex
		super(AstSet, self).__init__()
	def pretty_print(self, depth = 0):
		pfx = ' ' * depth * 2
		print '%s"%s"'%(pfx, self.raw_regex)
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
	def check_for_cycles(self, tbl = {}, v = set()):
		if self.p in v:
			print 'CYCLE ON', self.tok.name
			print v
			return True
		v.add(self.p)
		#print self.tok.name
		if tbl[self.p].root.check_for_cycles(tbl, v):
			return True
		v.remove(self.p)

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
	def check_for_cycles(self, tbl = {}, v = set()):
		if self.op.check_for_cycles(tbl, v):
			return True
		while isinstance(self.op, AstLink):
			self.op = tbl[self.op.p].root
		return False
	def flatten(self):
		self.op = self.op.flatten()
		return self
	def leaves(self, out = []):
		self.op.leaves(out)

class AstBinary(AstNode):
	def __init__(self, a, b):
		self.a = a
		self.b = b
		super(AstBinary, self).__init__()
	def pretty_print(self, depth = 0):
		pfx = ' ' * depth * 2
		print '%s<%s>'%(pfx, self.__class__.__name__)
		for x in self.children():
			x.pretty_print(depth + 1)
	def check_for_cycles(self, a= {}, v = set()):
		if self.a.check_for_cycles(tbl, v) or \
				self.b.check_for_cycles(tbl, v):
			return True
		while isinstance(self.a, AstLink):
			self.a = tbl[self.a.p].root
		while isinstance(self.b, AstLink):
			self.b = tbl[self.b.p].root
		return False
	def children(self):
		return [self.a, self.b]
	def flatten(self):
		self.a = self.a.flatten()
		self.b = self.b.flatten()
		return self
	def leaves(self, out = []):
		self.a.leaves(out)
		self.b.leaves(out)

	def __str__(self):
		return '%s(%s, %s)'%(self.__class__.__name__, self.a, self.b)
	def __repr__(self):
		return '%s(%s, %s)'%(self.__class__.__name__, self.a, self.b)

class AstEllipsis(AstUnary):
	def __init__(self, op):
		super(AstEllipsis, self).__init__(op)
	def flatten(self):
		# <x>... is equivalent <x>+, or <x><x>*
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

class AstBraces(AstUnary):
	def __init__(self, op):
		super(AstBraces, self).__init__(op)

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

def gen_dfa(p, tbl):
	if p.root.check_for_cycles(tbl):
		return
	if isinstance(p.root, AstLink):
		p.root = tbl[p.root.p].root
	p.root = AstConcat(p.root.flatten(), AstAccept())
	print 'Parse tree for: %s'%p.name
	p.root.pretty_print()

	out = []
	p.root.leaves(out)
	for (pos, x) in zip(xrange(len(out)), out):
		x.position = pos + 1
	#print p.root.nullable(), p.root.firstpos(), p.root.lastpos()

def parse_bnf(fn, tbl = {}):
	for p in productions(fn):
		if tbl.has_key(p.name):
			raise Exception('%s multiply defind'%p.name)
		tbl[p.name] = p
	return tbl

def builtin_productions(tbl = {}):
	d = {
		'__lf__': '\\n',
		'__isspace__': '\\s'
	}
	for k, v in d.items():
		p = Production(k)
		p.root = AstSet(v)
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
	gen_dfa(tbl[argv[1]], tbl)
	raise SystemExit, 0
