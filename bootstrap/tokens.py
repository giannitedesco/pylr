class Token(object):
    def __init__(self, name, lno):
        assert(name is None or isinstance(name, str))
        assert(isinstance(lno, int))
        self.name = name
        self.lineno = lno
        super(Token, self).__init__()
    def __str__(self):
        return '%s(%s)'%(self.__class__.__name__, self.name)
    def __repr__(self):
        return '%s(%s)'%(self.__class__.__name__, self.name)

class TokHead(Token):
    def __init__(self, name, lno):
        super(TokHead, self).__init__(name, lno)
class TokIdentifier(Token):
    def __init__(self, name, lno):
        super(TokIdentifier, self).__init__(name, lno)
class TokLiteral(Token):
    def __init__(self, name, lno):
        super(TokLiteral, self).__init__(name, lno)

class TokOperator(Token):
    def __init__(self, lno):
        super(TokOperator, self).__init__(None, lno)
    def __str__(self):
        return '%s'%(self.__class__.__name__)
    def __repr__(self):
        return '%s'%(self.__class__.__name__)

class TokOpRewrite(TokOperator):
    def __init__(self, lno):
        super(TokOpRewrite, self).__init__(lno)
class TokOpUnary(TokOperator):
    def __init__(self, lno):
        super(TokOpUnary, self).__init__(lno)
class TokOpBinary(TokOperator):
    def __init__(self, lno):
        super(TokOpBinary, self).__init__(lno)
class TokOpLSquare(TokOperator):
    def __init__(self, lno):
        self.confus = '['
        super(TokOpLSquare, self).__init__(lno)
class TokOpRSquare(TokOperator):
    def __init__(self, lno):
        self.confus = ']'
        super(TokOpRSquare, self).__init__(lno)
class TokOpLBrace(TokOperator):
    def __init__(self, lno):
        self.confus = '{'
        super(TokOpLBrace, self).__init__(lno)
class TokOpRBrace(TokOperator):
    def __init__(self, lno):
        self.confus = '}'
        super(TokOpRBrace, self).__init__(lno)

class TokOpChoice(TokOpBinary):
    def __init__(self, lno):
        self.confus = '|'
        super(TokOpChoice, self).__init__(lno)

class TokOpEllipsis(TokOpUnary):
    def __init__(self, lno):
        super(TokOpEllipsis, self).__init__(lno)
