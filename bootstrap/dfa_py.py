from os.path import splitext, basename, join
from .symbol import SymEof

def write_tokens(dfa, f):

    # Sort and uniquify the final states
    s = set()
    for v in list(dfa.final.values()):
        s.update([x for x in v])
    s = tuple(sorted(s, key = lambda x:(x.lineno, x.rule_name, x.action)))

    print(file=f)
    print('class Tok(IntEnum):', file=f)
    print('    EOF = %d'%SymEof.val, file=f)
    print('    UNKNOWN = 0', file=f)
    for i, tok in enumerate(s, 1):
        tn = '%s'%tok.rule_name.upper().replace(' ', '_')
        print('    %s = %d'%(tn, i), file=f)

    d = {
        'discard': '_action_discard',
        'uint': '_action_int',
        'int': '_action_int',
        'str': 'str',
    }

    print(file=f)
    print('_action = {', file=f)
    print('    Tok.EOF: %s,'%(d['discard']), file=f)
    for i, tok in enumerate(s, 1):
        tn = '%s'%tok.rule_name.upper().replace(' ', '_')
        print('    Tok.%s: %s,'%(tn, d[tok.action]), file=f)
    print('}', file=f)

def dfa_py(dfa, base_name, srcdir, includedir, table):
    fn = join(srcdir, base_name + '.py')
    f = open(fn, 'w')

    print('# vim: set fileencoding=utf8 :', file=f)
    print('from enum import IntEnum', file=f)
    print('from typing import NamedTuple, Any', file=f)
    print('', file=f)

    print('def _action_discard(x): return', file=f)
    print('def _action_int(x): return int(x, 0)', file=f)

    write_tokens(dfa, f)

    d = {
        'initial_state':1,
    }
    print('''
class Token(NamedTuple):
    toktype : Tok
    line : int
    col : int
    val : Any

class Lexer:
    __slots__ = (
        'buf',
        'state',
        'line',
        'col',
        '_cb',
    )
    initial_state = %(initial_state)d
'''%d, file=f)

    print('    accept = {', file=f)
    for i in range(dfa.num_states):
        if i in dfa.final:
            x = dfa.final[i][0]
            v = x.rule_name.upper().replace(' ', '_')
        else:
            continue
        print('        %s: Tok.%s,'%(i + 1, v), file=f)
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
        self._cb = cb

    def next_state(self, old, sym):
        try:
            return self.trans[old][ord(sym)]
        except KeyError:
            return 0

    def emit(self, toktype):
        val = _action[toktype](self.buf)
        tok = Token(toktype, self.line, self.col, val)
        if self._cb is not None:
            self._cb(tok)

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
        self.emit(Tok.EOF)

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
