from .symbol import *
from .grammar import Grammar
from .lrgen_c import lrgen_c
from .lrgen_py import lrgen_py

class kernel(frozenset):
    def __new__(cls, s):
        k = [x for x in s if x.is_kernel()]
        return super().__new__(cls, k)

class Language(object):
    def __init__(self, g):
        super(Language, self).__init__()
        self.p = g.p
        g.construct_FIRST()
        g.construct_FOLLOW()
        self.FIRST = g.FIRST
        self.FOLLOW = g.FOLLOW
        self.reachables = list(g.reachables())

class Collection(object):
    def __init__(self, lang):
        super(Collection, self).__init__()
        self.lang = lang
        self.create_canonical_collection()

    def start_item(self):
        s = self.lang.p['S']
        return Item(s.rules[0], head = s.nt, pos = 0)

    def end_item(self):
        s = self.lang.p['S']
        return Item(s.rules[0], head = s.nt, pos = 1)

    def GOTO(self, I, t):
        assert(isinstance(t, Sym))

        s = set()
        for i in I:
            try:
                x = i[i.pos]
            except IndexError:
                continue
            if x == t:
                s.add(Item(i, head = i.head, pos = i.pos + 1,
                        lookahead = i.lookahead))

        return self.closure(s)

class LR0(Collection):
    def create_canonical_collection(self):
        print('Construct canonical %s collection'%\
            self.__class__.__name__)
        C = set()
        C.add(self.closure(frozenset([self.start_item()])))

        fixpoint = False
        while not fixpoint:
            fixpoint = True

            for I in list(C):
                d = dict()
                for i in I:
                    try:
                        x = i[i.pos]
                    except IndexError:
                        continue
                    new = Item(i, head = i.head,
                        pos = i.pos + 1,
                        lookahead = i.lookahead)
                    d.setdefault(x, set()).add(new)

                for g in map(self.closure, list(d.values())):
                    if g and g not in C:
                        C.add(g)
                        fixpoint = False

        self.state_number = {}
        self.state = {}
        c = {}
        k = {}
        for i, I in enumerate(C):
            self.state_number[I] = i
            self.state[i] = I
            c[i] = I
            k[i] = kernel(I)
        self.canonical = c
        self.kernels = c


    def reduce_symbols(self, item):
        return self.lang.FOLLOW[item.head.name]

    def __init__(self, lang):
        super(LR0, self).__init__(lang)

    def closure(self, I):
        J = set(I) # copy it
        fixpoint = False
        while not fixpoint:
            fixpoint = True
            for j in list(J):
                try:
                    B = j[j.pos]
                except IndexError:
                    continue
                if not isinstance(B, NonTerminal):
                    continue
                for r in self.lang.p[B.name]:
                    i = Item(r, head = B, pos = 0)
                    if i in J:
                        continue
                    fixpoint = False
                    J.add(i)
        return frozenset(J)

class LR1(LR0):
    def __init__(self, lang):
        super(LR1, self).__init__(lang)

    def start_item(self):
        s = self.lang.p['S']
        return Item(s.rules[0], head = s.nt, pos = 0,
                lookahead = SymEof)

    def reduce_symbols(self, item):
        return [item.lookahead]

    def closure(self, I):
        def do_round(J, j):
            try:
                B = j[j.pos]
            except IndexError:
                return False
            if not isinstance(B, NonTerminal):
                return False
            for r in self.lang.p[B.name]:
                try:
                    beta = j[j.pos + 1]
                except IndexError:
                    beta = SymEpsilon
                if beta is not SymEpsilon:
                    if isinstance(beta, NonTerminal):
                        ff = self.lang.FIRST[beta.name]
                    else:
                        ff = [beta]
                else:
                    ff = [j.lookahead]

                for x in ff:
                    i = Item(r, head = B, pos = 0,
                        lookahead = x)
                    if i in J:
                        continue
                    J.add(i)
                    return True
            return False

        J = set(I) # copy it
        fixpoint = False
        while not fixpoint:
            fixpoint = True
            for j in list(J):
                if do_round(J, j):
                    fixpoint = False
        return frozenset(J)


class LALR1(LR1):
    def __init__(self, lang):
        super(LALR1, self).__init__(lang)

    def create_canonical_collection(self):
        print('Generating LALR(1) kernels')

        self.lr0 = LR0(self.lang)
        self.kernels = {}
        self.state_number = {}
        self.canonical = {}

        for k,v in list(self.lr0.kernels.items()):
            self.kernels[k] = set(v)

        for k,v in list(self.lr0.kernels.items()):
            I = self.closure(v)
            self.canonical[k] = I
            self.state_number[I] = k

        for inum, K in list(self.lr0.kernels.items()):
            print(' - do a set with', len(K), 'items')
            for k in K:
                if k.is_start():
                    k.lookahead = SymEof
            #self.generate_lookaheads(inum, K)
            for x in self.closure(K):
                print(x)
            print()


    def generate_lookaheads(self, inum, K):
        for j in self.closure(K):
            # if ( [B -> g.Xd, a] is in J, and a is not # )
            # conclude that lookahead a is generated spontaneously
            # for item B -> gX.d in GOTO(I, X);
            def gen_lookahead(j, X):
                new = Item(j, head = j.head, pos = j.pos + 1)
                item_set = self.GOTO(self.canonical[inum], X)
                print(inum, 'generate', j.lookahead)
                print(j)
                print('in')
                for x in item_set:
                    print('', x)
                print()
                assert(new.is_kernel())

            # if ( [B -> g.Xd, #] is in J )
            # conclude that lookaheads propagate from A -> a.b in I
            #    B -> gX.d in GOTO(I, X);
            def propagate_lookahead(j, X):
                new = Item(j, head = j.head, pos = j.pos + 1)
                #print 'Propagate', k.lookahead
                #print X
                #print j
                #print new
                #print
                return

            try:
                X = j[j.pos]
            except IndexError:
                continue
            if j.lookahead:
                gen_lookahead(j, X)
            else:
                propagate_lookahead(j, X)


# item should be a pair of ints, (rule_idx, pos)
class Item(tuple):
    def __new__(cls, arg = (), **kwargs):
        if arg:
            if arg[-1] is SymEof:
                arg = arg[:-1]
            elif len(arg) == 1 and arg[0] == SymEpsilon:
                arg = []
        if arg:
            if arg[-1] is SymEof:
                arg = arg[:-1]
            elif len(arg) == 1 and arg[0] == SymEpsilon:
                arg = []
        self = super().__new__(cls, arg)
        self.head = kwargs.pop('head')
        self.pos = int(kwargs.pop('pos'))
        self.lookahead = kwargs.pop('lookahead', None)
        assert(self.pos >= 0)
        assert(not arg or self.pos <= len(self))
        return self

    def __str__(self):
        def f(xxx_todo_changeme):
            (i, x) = xxx_todo_changeme
            if i == self.pos:
                return '. ' + x.name
            elif i == len(self) - 1 and self.pos == len(self):
                return x.name + ' .'
            return x.name
        if self:
            body = ' '.join(map(f, enumerate(self)))
        else:
            body = '.'
        if self.lookahead is None:
            return 'Item(%s -> %s)'%(self.head.name, body)
        return 'Item(%s -> %s, %s)'%(self.head.name,
                        body, self.lookahead.name)
    def __repr__(self):
        return str(self)

    def sortkey(self):
        return (self.head, self.pos, self.lookahead, tuple(self))
    def __eq__(a, b):
        return a.sortkey() == b.sortkey()
    def __neq__(a, b):
        return a.sortkey() != b.sortkey()
    def __gt__(a, b):
        return a.sortkey() > b.sortkey()
    def __lt__(a, b):
        return a.sortkey() < b.sortkey()
    def __gte__(a, b):
        return a.sortkey() >= b.sortkey()
    def __lte__(a, b):
        return a.sortkey() <= b.sortkey()
    def __hash__(self):
        return super(Item, self).__hash__() \
            ^ hash(self.pos) \
            ^ hash(self.head) \
            ^ hash(self.lookahead)
    def is_start(self):
        if self.head is SymStart and not self.pos:
            return True
        return False

    def is_kernel(self):
        if self.is_start():
            return True
        if self.pos > 0:
            return True
        return False

    def pre_position(self):
        "Everything before the dot"

        return self[:self.pos]
    def post_position(self):
        "Everything after the dot"

        return self[self.pos:]

    def dot_after(self):
        if len(self) <= self.pos:
            return None

        pre = self[:self.pos]
        after = self[self.pos]
        post = self[self.pos + 1:]
        return (pre, after, post)

class LRGen(object):
    def __init__(self, g, start):
        super(LRGen, self).__init__()
        if not isinstance(g, Grammar):
            raise TypeError

        self.start = g[start]
        if not isinstance(self.start, NonTerminal):
            raise TypeError

        self.lang = Language(g)
        self.C = LR0(self.lang)
        self.productions = {}

        # TODO: map kernel items to lookaheads
        # TODO: repeat lookahead generation until fixpoint

        # TODO: close each kernel using CLOSURE from LR(1) Fig 4.40
        # TODO: LR(1) table entries using LR(1) algo 4.56
        print('Constructing parse tables')
        self.action = self.construct_action_table()
        self.goto = self.construct_goto()
        self.initial = self.initial_state()

    def initial_state(self):
        s = self.C.start_item()
        for (I, inum) in list(self.C.state_number.items()):
            if s in I:
                return inum

    def construct_action_table(self):
        print('Construct action table...')

        action = {}

        def handle_conflict(key, new):
            try:
                old = action[key]
            except KeyError:
                action[key] = new
                return

            if old == new:
                return

            print('shift/reduce conflict')
            print(old)
            print(new)
            if old[0] == 'accept':
                action[key] = new
            elif new[0] == 'accept':
                pass
            elif old[0] == 'reduce' and new[0] == 'shift':
                action[key] = new
            elif old[0] == 'shift' and new[0] == 'reduce':
                pass
            else:
                print('unable to resolve')
                raise Exception('action table conflict')

        def prod_name(r):
            t = [x.name.lower() for x in r]
            if not t:
                t = ('epsilon',)

            t = r.head.name.upper()
            f = [x.name.upper() for x in r]
            if not f:
                f = ('EPSILON',)

            return '%s__FROM__%s'%(t, '_'.join(f))

        def do_reduce(r):
            if len(r) == 1 and r[0] is SymEpsilon:
                return
            if r.head is SymStart:
                return

            n = prod_name(r)
            try:
                index = self.productions[n][0]
            except KeyError:
                index = len(self.productions)
                plen = len(r)
                head = r.head
                p = (index, plen, head)
                self.productions[n] = p

            for a in self.C.reduce_symbols(r):
                key = (inum, a)
                val = ('reduce', (index, r))
                handle_conflict(key, val)

        for (I, inum) in list(self.C.state_number.items()):
            if self.C.end_item() in I:
                key = (inum, SymEof)
                val = ('accept', True)
                handle_conflict(key, val)

            for i in I:
                try:
                    nxt = i[i.pos]
                except IndexError:
                    do_reduce(i)
                    continue
                g = self.C.GOTO(I, nxt)
                val = self.C.state_number.get(g, None)
                assert(val is not None)
                if val is None:
                    continue
                val = ('shift', val)
                key = inum, nxt

                handle_conflict(key, val)

        #for k, v in sorted(action.items()):
        #    print k, '->', v

        print('action table:', len(action), 'entries')
        return action

    def construct_goto(self):
        print('Construct goto table...')

        goto = {}
        for (I, inum) in list(self.C.state_number.items()):
            for t in self.lang.reachables:
                if not isinstance(t, NonTerminal):
                    continue
                g = self.C.GOTO(I,t)
                out = self.C.state_number.get(g, None)
                if out is None:
                    continue
                key = (inum, t)
                val = out
                goto[key] = val

        print('goto table:', len(goto), 'entries')
        return goto


    def write_tables(self, name, srcdir = '.',
                incdir = '.', language = 'C'):
        fns = {
            'C':lrgen_c,
            'py':lrgen_py,
            'py2':lrgen_py,
            'python':lrgen_py,
            }
        fns[language](self, name, srcdir, incdir)
