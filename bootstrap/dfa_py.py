from os.path import splitext, basename, join

def do_token(f, name, idnum, action = 'discard'):
    d = {
        'discard': 'lambda self, x: None',
        'uint': 'lambda self, x: int(x, 0)',
        'int': 'lambda self, x: int(x, 0)',
        'str': 'str',
    }
    name = 'TOK_' + name
    print('class %s(TokType):'%name, file=f)
    print('    id_number = %d'%idnum, file=f)
    print('    action = %s'%d[action], file=f)

def write_tokens(dfa, f):
    print('''
class TokType(object):
    def __init__(self):
        super(TokType, self).__init__()
''', file=f)
    do_token(f, 'EOF', -2)
    do_token(f, 'UNKNOWN', 0)
    s = set()
    for v in list(dfa.final.values()):
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

    print('# vim: set fileencoding=utf8 :', file=f)

    write_tokens(dfa, f)

    d = {
        'initial_state':1,
    }
    print('''
class Token(object):
    def __init__(self, toktype, line, col, val = None):
        super(Token, self).__init__()
        self.toktype = toktype
        self.line = line
        self.col = col
        self.val = val

class Lexer(object):
    initial_state = %(initial_state)d
'''%d, file=f)

    print('    accept = {', file=f)
    for i in range(dfa.num_states):
        if i in dfa.final:
            x = dfa.final[i][0]
            v = x.rule_name.upper().replace(' ', '_')
        else:
            continue
        print('        %s: TOK_%s,'%(i + 1, v), file=f)
    print('    }', file=f)

    print('    trans = {', file=f)
    for pre, d in list(dfa.trans.items()):
        print('        %u: {'%(pre + 1), file=f)
        for sym, post in sorted(d.items()):
            print('            ord(\'%s\'): %u,'%(sym, post + 1), file=f)
        print('        },', file=f)
    print('    }', file=f)

    print('''
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
'''%d, file=f)

    f.close()
