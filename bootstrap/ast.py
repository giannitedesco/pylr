# vim: set fileencoding=utf8 :

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

