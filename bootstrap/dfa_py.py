from os.path import splitext, basename, join

def do_token(f, name, idnum, action = 'discard'):
    d = {
        'discard': 'lambda self, x: None',
        'uint': 'lambda self, x: int(x, 0)',
        'int': 'lambda self, x: int(x, 0)',
        'str': 'str',
    }
    name = 'TOK_' + name
    print >>f, 'class %s(TokType):'%name
    print >>f, '\tid_number = %d'%idnum
    print >>f, '\taction = %s'%d[action]

def write_tokens(dfa, f):
    print >>f, '''
class TokType(object):
    def __init__(self):
        super(TokType, self).__init__()
'''
    do_token(f, 'EOF', -2)
    do_token(f, 'UNKNOWN', 0)
    s = set()
    for v in dfa.final.values():
        s.update([x for x in v])
    s = sorted([(x.lineno, x.rule_name, x.action) for x in s])
    i = 1
    for (lineno,x,action) in s:
        tn = '%s'%x.upper().replace(' ', '_')
        do_token(f, tn, i, action)
        i += 1

def dfa_py(dfa, base_name, srcdir, includedir, table):
    fn = join(srcdir, base_name + '.py')
    f = open(fn, 'w')

    print >>f, '# vim: set fileencoding=utf8 :'

    write_tokens(dfa, f)

    d = {
        'initial_state':1,
    }
    print >>f, '''
class Token(object):
    def __init__(self, toktype, line, col, val = None):
        super(Token, self).__init__()
        self.toktype = toktype
        self.line = line
        self.col = col
        self.val = val

class Lexer(object):
    initial_state = %(initial_state)d
'''%d

    print >>f, '\taccept = {'
    for i in xrange(dfa.num_states):
        if i in dfa.final:
            x = dfa.final[i][0]
            v = x.rule_name.upper().replace(' ', '_')
        else:
            continue
        print >>f, '\t\t%s: TOK_%s,'%(i + 1, v)
    print >>f, '\t}'

    print >>f, '\ttrans = {'
    for pre, d in dfa.trans.items():
        print >>f, '\t\t%u: {'%(pre + 1)
        for sym, post in sorted(d.items()):
            print >>f, '\t\t\tord(\'%s\'): %u,'%(sym, post + 1)
        print >>f, '\t\t},'
    print >>f, '\t}'

    print >>f, '''
    def __init__(self, cb):
        super(Lexer, self).__init__()
        self.clear_buf()
        self.state = self.initial_state
        self.line = 1
        self.col = 0
        self.cb = cb

    def next_state(self, old, sym):
        try:
            return self.trans[old][ord(sym)]
        except KeyError:
            return 0

    def emit(self, toktype):
        val = toktype().action(self.buf)
        tok = Token(toktype, self.line, self.col, val)
        if self.cb is not None:
            self.cb(tok)

    def clear_buf(self):
        self.buf = ''

    def to_buf(self, s):
        self.buf = self.buf + s

    def symbol(self, sym):
        assert(len(sym) == 1)

        if sym == '\\n':
            self.line += 1
            self.col = 0
        else:
            self.col += 1
        self.__symbol(sym)

    def __symbol(self, sym):
        old = self.state
        self.state = new = self.next_state(old, sym)

        if old and old in self.accept and not new:
            self.emit(self.accept[old])
            self.clear_buf()
            self.to_buf(sym)
            self.__symbol(sym)
            return

        if new:
            if old == self.initial_state:
                self.clear_buf()
            self.to_buf(sym)
        else:
            if old == self.initial_state:
                es = 'unexpected \\\\x%%.2x(%%c)'%%(ord(sym), sym)
                raise Exception(es)
            else:
                self.state = self.initial_state
                self.__symbol(sym)
                return

    def eof(self):
        self.symbol('\\n')
        self.emit(TOK_EOF)

    def lex_file(self, f):
        while True:
            s = f.read(1024)
            if not s:
                self.eof()
                return
            for x in s:
                self.symbol(x)
    def lex_buf(self, s):
        for x in s:
            self.symbol(x)
'''%d

    f.close()
