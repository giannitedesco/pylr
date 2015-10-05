from symbol import *

def write_stack_item(f):
	print >>f, '''class StackItem(object):
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
'''

def write_sym_defs(lr, f):
	print >>f, '\tSYM_EOF = %d'%SymEof().val
	print >>f, '\tSYM_EPSILON = %d'%SymEpsilon().val
	for nt in sorted(lr.lang.reachables):
		if not isinstance(nt, NonTerminal):
			continue
		print >>f, '\t%s = %d'%(nt.cname(), nt.val)
	
	print >>f, '\t__names= {'
	for nt in sorted(lr.lang.reachables):
		print >>f, '\t\t%d: "%s",'%(nt.val, nt.name)
		print >>f, '\t\t"%s": %d,'%(nt.name, nt.val)
		print >>f, ''
	print >>f, '\t}'

def write_goto_table(lr, f):
	print >>f, '\tGOTO = {'
	for ((i, A), j) in sorted(lr.goto.items()):
		print >> f, '\t\t(%d, %d): %d,'%(i, A.val, j)
	print >>f, '\t}'

def write_production_table(lr, f):
	print >>f, '\tproductions = {'
	for v, k in sorted([(v, k) for (k, v) in \
				lr.productions.items()]):
		(index, plen, head) = v
		print >>f, '\t\t%s: (\'%s\', %d, %d),'%(index, k,
							plen, head.val)
	print >>f, '\t}\n'

def write_action_table(lr, f):
	print >>f, '\tACTION = {'
	for ((i,a), (c, v)) in sorted(lr.action.items()):
		if c == 'shift':
			print >>f, '\t\t(%d, %d): (\'shift\', %d),'%(\
					i, a.val, v)
		elif c == 'reduce':
			index, r = v
			print >>f, '\t\t(%d, %d): (\'reduce\', %d),'%(\
					i, a.val, index)
	print >>f, '\t}'

def write_sym_names(lr, f):
	print >>f, '\tdef __getitem__(self, key):'
	print >>f, '\t\treturn self.__names[key]'

def write_init(lr, f):
	print >>f, '\tdef __init__(self):'
	print >>f, '\t\tsuper(Parser, self).__init__()'
	print >>f, '\t\tself.stack = []'
	print >>f, '\t\tself.push(StackItem(self.initial_state))'

def write_parse_func(lr, f):
	print >>f, '''\t# Parsing methods
	def stack_top(self):
		assert(len(self.stack))
		return self.stack[-1]
	
	def push(self, item):
		assert(isinstance(item, StackItem))
		self.stack.append(item)

	def multipop(self, cnt):
		if not cnt:
			return []
		assert(len(self.stack) >= cnt)
		ret = self.stack[-cnt:]
		self.stack = self.stack[:-cnt]
		return ret

	def dispatch(self, k, args, nxt):
		self.push(StackItem(nxt))

	def feed(self, tok):
		while True:
			toktype = tok.toktype.id_number
			akey = (self.stack_top().st, toktype)
			if not self.ACTION.has_key(akey):
				raise Exception('Parse Error')
			(a, v) = self.ACTION[akey]

			if a == 'accept':
				if not self.accept(self.multipop(2)):
					raise Exception('bad accept')
			elif a == 'shift':
				self.push(TokItem(v, tok))
				if toktype == self.SYM_EOF:
					continue
			elif a == 'reduce':
				(k, l, head) = self.productions[v]
				args = self.multipop(l)
				gkey = (self.stack_top().st, head)
				if not self.GOTO.has_key(gkey):
					raise Exception('GOTO Error')
				j = self.GOTO[gkey]
				self.dispatch(k, args, j)
				continue
			else:
				raise Exception('bad action')

			return

'''

# This should be the rule class, remove pos
def lrgen_py(lr, name, path):
	from os.path import join

	fn = join(path, name + '.py')
	print 'writing', fn

	f = open(fn, 'w')
	print >>f, '# vim: set fileencoding=utf8 :\n'

	write_stack_item(f)

	print >>f, 'class Parser(object):'
	write_sym_defs(lr, f)
	print >>f, ''

	print >>f, '\tinitial_state = %d'%lr.initial
	print >>f, ''

	write_production_table(lr, f)
	write_action_table(lr, f)
	print >>f, ''

	write_goto_table(lr, f)
	print >>f, ''

	write_sym_names(lr, f)
	print >>f, ''

	write_init(lr, f)
	print >>f, ''

	write_parse_func(lr, f)
