from tokens import *
from ast import *
from tokenizer import tokenize

class ParseTree(object):
    def __init__(self, name, final = False, action = None, lineno = 0):
        self.name = name
        self.root = None
        self.pstack = []
        self.stack = []
        self.nchoice = 0
        self.natom = 0
        self.lineno = lineno
        self.__ready = False
        self.__last = None
        self.__cb = {
                TokOpChoice: ParseTree.__chose,
                TokLiteral: ParseTree.__atom,
                TokIdentifier: ParseTree.__atom,
                TokOpEllipsis: ParseTree.__ellipsis,
                TokOpLSquare: ParseTree.__lparen,
                TokOpRSquare: ParseTree.__rparen,
                TokOpLBrace: ParseTree.__lparen,
                TokOpRBrace: ParseTree.__rparen,
        }

        self.final = final
        self.action = action
        super(ParseTree, self).__init__()

    def symbol_name(self):
        return self.name.upper().replace(' ', '_')

    def make_final(self):
        self.final = True
        if isinstance(self.root, AstConcat) and \
                isinstance(self.root.b, AstAccept):
            return
        self.root = AstConcat(self.root,
                AstAccept(self.name,
                        self.lineno,
                        self.action))

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

    def __cmp__(a, b):
        assert(isinstance(b, ParseTree))
        return cmp(a.lineno, b.lineno)

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

def get_parms(t):
    kw = {}
    if t.name[0] == '@':
        name = t.name[1:]
        kw['final'] = True
        kw['action'] = 'discard'
    else:
        name = t.name
        kw['final'] = False

    x = name.split('{', 1)
    if len(x) > 1 and x[1] and x[1][-1] == '}':
        name = x[0]
        kw['action'] = x[1][:-1]
    
    kw['lineno'] = t.lineno

    #print '%s -> %s %s'%(t.name, name, kw)
    return (name, kw)

def parse(fn, break_terminals=True):
    p = None
    for t in tokenize(fn):
        if isinstance(t, TokHead):
            if p is not None:
                p.eof()
                yield p
            (name, kwargs) = get_parms(t)
            p = ParseTree(name, **kwargs)
        elif break_terminals and isinstance(t, TokLiteral):
            map(lambda x:p.feed(TokLiteral(x, t.lineno)), t.name)
        else:
            p.feed(t)
    if p is not None:
        p.eof()
        yield p

