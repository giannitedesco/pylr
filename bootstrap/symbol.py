# vim: set fileencoding=utf8 :

from operator import itemgetter

class Sym(tuple):
    __slots__ = ()
    _next_val = 0
    val = property(itemgetter(0))
    basename = property(itemgetter(1))
    name = property(itemgetter(2))

    def __new__(cls, name, *extra, val = None, basename = None):
        if val is None:
            val = Sym._next_val
            Sym._next_val += 1
        else:
            val = int(val)

        if basename is None:
            basename = name.upper().replace(' ', '_')

        args = (val, basename, name) + extra
        return super().__new__(cls, args)

    @property
    def cname(self):
        return 'SYM_' + self.basename

    @property
    def pyame(self):
        return 'Sym.' + self.basename

    def __str__(self):
        return '%s(%s)'%(self.__class__.__name__, self.name)
    def __repr__(self):
        return '%s(%s)'%(self.__class__.__name__, self.name)
    def __eq__(a, b):
        return a.val == b.val
    def __neq__(a, b):
        return a.val != b.val
    def __gt__(a, b):
        return a.val > b.val
    def __lt__(a, b):
        return a.val < b.val
    def __gte__(a, b):
        return a.val >= b.val
    def __lte__(a, b):
        return a.val <= b.val

class SymSpecial(Sym):
    def __str__(self):
        return self.name
    def __repr__(self):
        return self.name

    def __hash__(self):
        return hash(tuple(self))

SymEpsilon = SymSpecial('ε', val = -1, basename = 'EPSILON')
SymEof = SymSpecial('$', val = -2, basename = 'EOF')

class Terminal(Sym):
    def __new__(cls, name, **kwargs):
        return super().__new__(cls, name, **kwargs)

    def __hash__(self):
        return hash(tuple(self))

class NonTerminal(Sym):
    prime_for = property(itemgetter(3))

    def __new__(cls, name, prime_for = None, **kwargs):
        if prime_for is not None and not isinstance(prime_for, NonTerminal):
            raise TypeError

        self = super().__new__(cls, name, prime_for, **kwargs)
        self.num_primes = 0
        self.terminal_marker = False
        return self

    @property
    def is_prime(self):
        return self.prime_for is not None

    def new_prime(self):
        if self.is_prime:
            parent = self.prime_for
        else:
            parent = self
        parent.num_primes += 1
        name = '%s_PRIME%d'%(parent.name, parent.num_primes)
        return NonTerminal(name, prime_for = parent)

    def __hash__(self):
        return hash(tuple(self))

class SpecialNonTerminal(NonTerminal):
    def __str__(self):
        return self.name
    def __repr__(self):
        return self.name

SymStart = SpecialNonTerminal('S', val = -3, basename = 'START')
