from ast import AstLiteral
from graph import Graph
from c import CFile, HFile
from os.path import join

class Block(frozenset):
	def __init__(self, *args, **kwargs):
		super(Block, self).__init__(*args, **kwargs)
	def stable_refinement(self, func):
		#    partition b into subgroups such that two states s and t
		#    are in the same subgroup if and only if for all
		#    input symbols a, states s and t have transitions on a
		#    to states in the same group of S
		#    replace b in Snew by the set of all subgroups formed
		r = {}
		#print '', self
		for x in self:
			ff = func.get(x, frozenset({}))
			r.setdefault(ff, []).append(x)
		ret = map(Block, r.values())
		#for k,v in r.items():
		#	print '%s -> %s'%(k, v)
		#print self
		#print ret
		#print

		if len(ret) > 1:
			return ret
		return None

class Partition(set):
	def __init__(self, *args, **kwargs):
		self.item_mapping = {}
		super(Partition, self).__init__()
		if len(args):
			for x in args[0]:
				self.add(x)
	def add(self, item):
		assert(isinstance(item, Block))
		for x in item:
			assert(not self.item_mapping.has_key(x))
			self.item_mapping[x] = item
		super(Partition, self).add(item)
	def update(self, s):
		for item in s:
			self.add(item)
	def popitem(self):
		item = super(Partition, self).popitem()
		for x in item:
			assert(self.item_mapping.has_key(x))
			del self.item_mapping[x]
		return item
	def block_func(self, func, final):
		# re-write the function to indicate the block which the
		# item is bucketed in to
		f = {}
		for k,v in func.items():
			f[k] = frozenset(map(lambda (x,y):
					(x, self.item_mapping[y]),
					v.items()))

		# Any final blocks are given an outgoing edge to knowhere
		# keyed on the name of the accepting state
		for k,v in final.items():
			v = '|'.join(map(lambda x:x.rule_name, sorted(v)))
			f[k] = frozenset(set({(v,None)}).union(f.get(k, set({}))))
		return f
	def refine(self, func, final):
		# for each block in S
		ret = Partition()
		delta = False
		f = self.block_func(func, final)
		for b in self:
			new = b.stable_refinement(f)
			if new is None:
				ret.add(b)
				continue
			ret.update(new)
			delta = True
		if delta:
			return ret
		else:
			return None

class DFA(object):
	def __init__(self, r, tbl):
		# Check for cycles and resolve all production references
		r.root = r.root.resolve_links(tbl)

		#r.make_final()

		# Flatten the tree and add the end-of-pattern marker
		r.root = r.root.flatten()

		# Display the flattened parse tree
		#print 'Parse tree for: %s'%r.name
		#r.root.pretty_print()

		# Construct the position table
		postbl = []
		r.root.leaves(postbl)
		for (pos, x) in zip(xrange(len(postbl)), postbl):
			x.position = pos

		print 'NFA has %u positions'%len(postbl)

		# Calculate the followpos function
		r.root.calc_followpos(postbl)
		#self.graph_followpos(postbl, r.root.firstpos())

		initial = r.root.firstpos().union(frozenset({}))
		states = {}
		Dstate = set({initial})
		Dtrans = {}

		num_states = 0
		while len(Dstate):
			S = Dstate.pop()
			assert(S not in states)
			states[S] = num_states # mark
			num_states += 1

			#print 'S = %s'%S
			S2 = filter(lambda x:isinstance(postbl[x],
					AstLiteral), S)
			SS = map(lambda x:(postbl[x].literal, x), S2)
			s = {}
			for a, p in SS:
				s.setdefault(a, set()).add(p)

			for a, v in s.items():
				U = set()
				for p in v:
					U.update(postbl[p].followpos)
				U = frozenset(U)

				if U not in Dstate and U not in states:
					Dstate.add(U)

				Dtrans[S,a] = U

		# Re-number transitions
		trans = {}
		self.num_trans = 0
		while Dtrans:
			((pre,sym),post) = Dtrans.popitem()
			trans.setdefault(states[pre], {})[sym] = \
					states[post]
			self.num_trans += 1

		f = []
		r.root.finals(f)
		f = set(map(lambda x:x.position, f))

		# free up state sets and use the renumbering
		final = {}
		init = None
		while states:
			x, i = states.popitem()
			for fpos in f.intersection(x):
				final.setdefault(i,[]).append(\
					postbl[fpos])
			s[i] = None
			if x == initial:
				assert(init is None)
				init = i

		self.initial = init
		self.num_states = num_states
		self.final = final
		self.trans = trans

		print 'DFA has %u states and %u transitions'%(\
						self.num_states,
						self.num_trans)
		super(DFA, self).__init__()

	def shrink(self, obsolete):
		def new_number(v, o):
			ret = v
			for x in o:
				assert(v != x)
				if v < x:
					break
				if v > x:
					ret -= 1
			return ret

		def replace(v, o):
			return o.get(v, v)

		def renumber(r, o, s):
			ret = {}
			for k,v in r.items():
				assert(k not in obsolete)
				ret[k] = replace(v, o)
			r = ret
			for k,v in r.items():
				assert(k not in obsolete)
				ret[k] = new_number(v, s)
			return ret

		# renumber the states
		new = {}
		num_trans = 0
		s = sorted(obsolete.keys())
		for k, v in self.trans.items():
			v = renumber(v, obsolete, s)
			new[new_number(k, s)] = v
			num_trans += len(v)

		ni = new_number(self.initial, s)

		# now all final states in the group apply so we
		# need to do merge them in here as we renumber
		nf = {}
		for k,v in self.final.items():
			nk = obsolete.get(k, k)
			if nk != k:
				v = list(set(self.final.get(nk, []) + v))
			nk = new_number(nk, s)
			nf[nk] = v

		self.trans = new
		self.num_states -= len(obsolete)
		self.num_trans = num_trans
		self.initial = ni
		self.final = nf

	def optimize(self):
		# 1. partition in to final and non-final, S
		f = Block(self.final)
		nf = Block(set(xrange(self.num_states)).difference(f))
		S = Partition({f, nf})

		# 2. until fix-point
		while True:
			Snew = S.refine(self.trans, self.final)
			if Snew is None:
				break
			S = Snew

		obsolete = {}
		for b in S:
			if len(b) <= 1:
				continue
			i = iter(b)
			v = i.next()
			for k in i:
				obsolete[k] = v
				try:
					del self.trans[k]
				except KeyError:
					pass

		self.shrink(obsolete)
		print 'DFA has %d states and %d transitions (optimal)'%(\
			self.num_states, self.num_trans)

	def dump_graph(self, fn):
		g = Graph('DFA', fn)

		for i in xrange(self.num_states):
			kwargs = {'label': str(i + 1)}
			if i in self.final:
				kwargs['shape'] = 'doublecircle'
				kwargs['color'] = 'red'
				kwargs['label'] = '\\n'.join(\
					map(lambda x:x.rule_name,
						self.final[i]))
			if i == self.initial:
				kwargs['color'] = 'blue'
			g.add_node(str(i + 1), **kwargs)

		for pre, d in self.trans.items():
			for sym, post in sorted(d.items()):
				g.add_edge(pre + 1, post + 1, sym)

	def dump_c(self, base_name = 'lex', srcdir = '.',
				includedir = '.', table = True):

		cfn = base_name + '.c'
		hfn = base_name + '.h'
		c = CFile(cfn, incl = [join(includedir, hfn)], srcdir = srcdir)
		c.state_type(self.num_states)
		if table:
			c.transition_table(self)
		else:
			c.transition_func(self)
		c.accept_table(self)
		c.boilerplate(self)

		h = HFile(hfn, includedir = includedir)
		h.token_enum(self)
		h.decls()
