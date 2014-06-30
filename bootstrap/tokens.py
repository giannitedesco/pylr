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

