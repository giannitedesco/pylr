from .symbol import *

def write_stack_item(f):
    print(file=f)
    print('''\nclass StackItem:
    __slots__ = ('st',)

    def __init__(self, st):
        super(StackItem, self).__init__()
        self.st = st

    def __str__(self):
        return f'{self.__class__.__name__}({self.st})'

    def __repr__(self):
        return str(self)


class TokItem(StackItem):
    __slots__ = ('tok',)

    def __init__(self, st, tok):
        super(TokItem, self).__init__(st)
        self.tok = tok''', file=f)

def write_sym_enum(lr, f):
    def line(sym):
        print('    %s = %d'%(sym.basename, sym.val), file=f)

    for nt in sorted(lr.lang.reachables):
        line(nt)

def write_goto_table(lr, f):
    print('    GOTO = {', file=f)
    for ((i, A), j) in sorted(lr.goto.items()):
        print('        (%d, %s): %d,'%(i, A.pyname, j), file=f)
    print('    }', file=f)

def write_production_table(lr, f):
    print('    productions = {', file=f)
    for v, k in sorted([(v, k) for (k, v) in \
                list(lr.productions.items())]):
        (index, plen, head) = v
        print('        %s: (%d, %s),'%(index, plen, head.pyname),
                file=f)
    print('    }\n', file=f)

def write_action_table(lr, f):
    print('    ACTION = {', file=f)
    for ((i,a), (c, v)) in sorted(lr.action.items()):
        if c == 'shift':
            print('        (%d, %s): (\'shift\', %d),'%(\
                    i, a.pyname, v), file=f)
        elif c == 'reduce':
            index, r = v
            print('        (%d, %s): (\'reduce\', %d),'%(\
                    i, a.pyname, index), file=f)
        elif c == 'accept':
            print('        (%d, %s): (\'accept\', None),'%(\
                    i, a.pyname), file=f)
    print('    }', file=f)

def write_sym_names(lr, f):
    print('''    def __getitem__(self, key):
        try:
            return Sym[key]
        except KeyError:
            pass
        try:
            return Sym(key)
        except KeyError:
            pass''', file=f)

def write_init(lr, f):
    print('    def __init__(self):', file=f)
    print('        super(Parser, self).__init__()', file=f)
    print('        self.stack = []', file=f)
    print('        self._push(StackItem(self.initial_state))', file=f)

def write_parse_func(lr, f):
    print('''    # Parsing methods
    def _stack_top(self):
        assert(len(self.stack))
        return self.stack[-1]

    def _push(self, item):
        assert(isinstance(item, StackItem))
        self.stack.append(item)

    def _multipop(self, cnt):
        if not cnt:
            return ()
        assert(len(self.stack) >= cnt)
        ret = tuple(self.stack[-cnt:])
        self.stack = self.stack[:-cnt]
        return ret

    def _dispatch(self, head, args, nxt):
        self._push(StackItem(nxt))

    def _accept(self, root):
        print('ACCEPT', root)

    def feed(self, tok):
        while True:
            toktype = tok.toktype
            akey = (self._stack_top().st, toktype)
            if akey not in self.ACTION:
                raise Exception(f'Parse Error {akey}')
            (a, v) = self.ACTION[akey]

            if a == 'accept':
                root = self._multipop(2)
                if not root:
                    raise Exception('bad accept')
                assert(not self.stack)
                self._accept(root[1])
                return

            assert(v is not None)

            if a == 'shift':
                self._push(TokItem(v, tok))
                if toktype == Sym.EOF:
                    continue
            elif a == 'reduce':
                (l, head) = self.productions[v]
                args = self._multipop(l)
                gkey = (self._stack_top().st, head)
                if gkey not in self.GOTO:
                    raise Exception('GOTO Error')
                j = self.GOTO[gkey]
                self._dispatch(head, args, j)
                continue
            else:
                raise Exception('bad action')

            return''', file=f)

# This should be the rule class, remove pos
def lrgen_py(lr, name, srcdir, incdir):
    from os.path import join

    fn = join(srcdir, name + '.py')
    print('writing', fn)

    f = open(fn, 'w')
    print('# vim: set fileencoding=utf8 :', file=f)
    print('# Auto-generated by https://github.com/giannitedesco/pylr/', file=f)
    print('from enum import IntEnum', file=f)

    write_stack_item(f)

    print(file=f)
    print('\nclass Sym(IntEnum):', file=f)
    write_sym_enum(lr, f)

    print(file=f)
    print('\nclass Parser:', file=f)
    print('    __slots__ = (\'stack\',)\n', file=f)
    print('    initial_state = %d'%lr.initial, file=f)
    print('', file=f)

    write_production_table(lr, f)
    write_action_table(lr, f)
    print('', file=f)

    write_goto_table(lr, f)
    print('', file=f)

    write_sym_names(lr, f)
    print('', file=f)

    write_init(lr, f)
    print('', file=f)

    write_parse_func(lr, f)
