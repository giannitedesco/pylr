from .symbol import *

def write_stack_item(f):
    print('''class StackItem(object):
    def __init__(self, st):
        super(StackItem, self).__init__()
        self.st = st
    def __repr__(self):
        return 'StackItem(%s)'%self.st
class TokItem(StackItem):
    def __init__(self, st, tok):
        super(TokItem, self).__init__(st)
        self.tok = tok
    def __repr__(self):
        return 'TokItem(%s, %s)'%(self.st, self.tok.val)
''', file=f)

def write_sym_defs(lr, f):
    print('    SYM_EOF = %d'%SymEof().val, file=f)
    print('    SYM_EPSILON = %d'%SymEpsilon().val, file=f)
    for nt in sorted(lr.lang.reachables):
        if not isinstance(nt, NonTerminal):
            continue
        print('    %s = %d'%(nt.cname(), nt.val), file=f)
    
    print('    __names= {', file=f)
    for nt in sorted(lr.lang.reachables):
        print('        %d: "%s",'%(nt.val, nt.name), file=f)
        print('        "%s": %d,'%(nt.name, nt.val), file=f)
        print('', file=f)
    print('    }', file=f)

def write_goto_table(lr, f):
    print('    GOTO = {', file=f)
    for ((i, A), j) in sorted(lr.goto.items()):
        print('        (%d, %d): %d,'%(i, A.val, j), file=f)
    print('    }', file=f)

def write_production_table(lr, f):
    print('    productions = {', file=f)
    for v, k in sorted([(v, k) for (k, v) in \
                list(lr.productions.items())]):
        (index, plen, head) = v
        print('        %s: (\'%s\', %d, %d),'%(index, k,
                            plen, head.val), file=f)
    print('    }\n', file=f)

def write_action_table(lr, f):
    print('    ACTION = {', file=f)
    for ((i,a), (c, v)) in sorted(lr.action.items()):
        if c == 'shift':
            print('        (%d, %d): (\'shift\', %d),'%(\
                    i, a.val, v), file=f)
        elif c == 'reduce':
            index, r = v
            print('        (%d, %d): (\'reduce\', %d),'%(\
                    i, a.val, index), file=f)
        elif c == 'accept':
            print('        (%d, %d): (\'accept\', None),'%(\
                    i, a.val), file=f)
    print('    }', file=f)

def write_sym_names(lr, f):
    print('    def __getitem__(self, key):', file=f)
    print('        return self.__names[key]', file=f)

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
            return []
        assert(len(self.stack) >= cnt)
        ret = self.stack[-cnt:]
        self.stack = self.stack[:-cnt]
        return ret

    def _dispatch(self, k, args, nxt):
        self._push(StackItem(nxt))

    def _accept(self, root):
        print('ACCEPT', root)

    def feed(self, tok):
        while True:
            toktype = tok.toktype.id_number
            akey = (self._stack_top().st, toktype)
            if not akey in self.ACTION:
                raise Exception('Parse Error')
            (a, v) = self.ACTION[akey]

            if a == 'accept':
                root = self._multipop(2)
                if not root:
                    raise Exception('bad accept')
                assert(not self.stack)
                self._accept(root[1])
            elif a == 'shift':
                self._push(TokItem(v, tok))
                if toktype == self.SYM_EOF:
                    continue
            elif a == 'reduce':
                (k, l, head) = self.productions[v]
                args = self._multipop(l)
                gkey = (self._stack_top().st, head)
                if not gkey in self.GOTO:
                    raise Exception('GOTO Error')
                j = self.GOTO[gkey]
                self._dispatch(k, args, j)
                continue
            else:
                raise Exception('bad action')

            return

''', file=f)

# This should be the rule class, remove pos
def lrgen_py(lr, name, srcdir, incdir):
    from os.path import join

    fn = join(srcdir, name + '.py')
    print('writing', fn)

    f = open(fn, 'w')
    print('# vim: set fileencoding=utf8 :\n', file=f)

    write_stack_item(f)

    print('class Parser(object):', file=f)
    write_sym_defs(lr, f)
    print('', file=f)

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
