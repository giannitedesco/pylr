# vim: set fileencoding=utf8 :

class Sym(object):
	__val = 0
	def __init__(self, name, val = None):
		self.name = name
		if val is None:
			self.val = Sym.__val
			Sym.__val += 1
		else:
			self.val = val
		super(Sym, self).__init__()
	def __str__(self):
		return '%s(%s)'%(self.__class__.__name__, self.name)
	def __repr__(self):
		return '%s(%s)'%(self.__class__.__name__, self.name)
	def __cmp__(a, b):
		if not isinstance(b, Sym):
			raise TypeError
		return a.val.__cmp__(b.val)

class SymEpsilon(Sym):
	__instance = None
	def __new__(cls, *args, **kwargs):
		if cls.__instance is None:
			cls.__instance = super(SymEpsilon, cls).__new__(cls, \
							*args, **kwargs)
			super(SymEpsilon, cls.__instance).__init__('ε')
		return cls.__instance
	def __init__(self):
		pass
	def __str__(self):
		return self.name
	def __repr__(self):
		return self.name

class SymEof(Sym):
	__instance = None
	def __new__(cls, *args, **kwargs):
		if cls.__instance is None:
			cls.__instance = super(SymEof, cls).__new__(cls, \
							*args, **kwargs)
			super(SymEof, cls.__instance).__init__('$')
		return cls.__instance
	def __init__(self):
		pass
	def __str__(self):
		return self.name
	def __repr__(self):
		return self.name

class Terminal(Sym):
	def __init__(self, name):
		super(Terminal, self).__init__(name)

class NonTerminal(Sym):
	def __init__(self, name, prime_for = None, **kwargs):
		super(NonTerminal, self).__init__(name, **kwargs)
		self.prime_for = prime_for
		if self.is_prime() and not \
				isinstance(self.prime_for, NonTerminal):
			raise TypeError
		self.num_primes = 0
		self.terminal_marker = False
	def is_prime(self):
		return self.prime_for is not None
	def new_prime(self):
		p = self if self.prime_for is None else self.prime_for
		p.num_primes += 1
		name = '%s_PRIME%d'%(p.name, p.num_primes)
		return NonTerminal(name, prime_for = p)
	def __cmp__(a, b):
		if not isinstance(b, Sym):
			raise TypeError
		return a.val.__cmp__(b.val)


class SymStart(NonTerminal):
	__instance = None
	def __new__(cls, *args, **kwargs):
		if cls.__instance is None:
			cls.__instance = super(SymStart, cls).__new__(cls, \
							*args, **kwargs)
			super(SymStart, cls.__instance).__init__('S')
		return cls.__instance
	def __init__(self):
		pass
	def __str__(self):
		return self.name
	def __repr__(self):
		return self.name
