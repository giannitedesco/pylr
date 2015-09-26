from symbol import *

def large_enough_type(x):
	if x <= 0xff:
		return 'uint8_t'
	elif x < 0xffff:
		return 'uint16_t'
	elif x < 0xffffffff:
		return 'uint32_t'
	else:
		return 'uint64_t'


def write_sym_defs(lr, f):
	f.write('#define SYM_EOF %d\n'%SymEof().val)
	f.write('#define SYM_EPSILON %d\n'%SymEpsilon().val)
	for nt in sorted(lr.lang.reachables):
		if not isinstance(nt, NonTerminal):
			continue
		f.write('#define %s %d\n'%(nt.cname(), nt.val))

def write_sym_names(lr, f):
	f.write('static inline const char *sym_name(int sym)\n')
	f.write('{\n')
	f.write('\tswitch(sym) {\n')
	for nt in sorted(lr.lang.reachables):
		f.write('\tcase %s:\n'%(nt.cname()))
		f.write('\t\treturn "%s";\n'%(nt.name))
	#f.write('\tcase SYM_EPSILON:\n')
	#f.write('\t\treturn "EPSILON";\n')
	f.write('\tdefault:\n')
	f.write('\t\treturn "<<UNKNOWN>>";\n')
	f.write('\t}\n')
	f.write('}\n')

def write_goto_table(lr, f):
	print >>f, 'static const struct {'
	print >>f, '\tunsigned int i;'
	print >>f, '\tint A;'
	print >>f, '\tunsigned int j;'
	print >>f, '}GOTO[] = {'
	for ((i, A), j) in sorted(lr.goto.items()):
		print >> f, '\t{ %d, %s, %d },'%(i, A.cname(), j)
	print >>f, '};'

def write_productions_enum(lr, f):
	print >>f, 'enum production_idx {'
	for k in sorted(lr.productions.keys()):
		print >>f, "\t%s,"%k
	print >>f, '\tNR_PRODUCTIONS,'
	print >>f, "};"

	t = large_enough_type(len(lr.productions.keys()))
	print >>f
	print >>f, 'typedef %s production_idx_t;'%t

def write_production_table(lr, f):
	print >>f, 'static const struct production {'
	print >>f, '\tunsigned int len;'
	print >>f, '\tint head;'
	print >>f, '\tproduction_idx_t action;'
	print >>f, '}productions[] = {'
	for v, k in sorted([(v, k) for (k, v) in \
				lr.productions.items()]):
		(index, plen, head) = v
		print >>f, '\t{'
		print >>f, '\t\t.action = %s,'%k
		print >>f, '\t\t.len = %d,'%plen
		print >>f, '\t\t.head = %s,'%head.cname()
		print >>f, '\t},'
	print >>f, '};'

def write_action_table(lr, f):
	print >>f, '#define ACTION_ERROR\t0'
	print >>f, '#define ACTION_ACCEPT\t1'
	print >>f, '#define ACTION_SHIFT\t2'
	print >>f, '#define ACTION_REDUCE\t3'
	print >>f
	print >>f, 'struct shift_move {'
	print >>f, '\tunsigned int t;'
	print >>f, '};'
	print >>f
	print >>f, 'struct reduce_move {'
	print >>f, '\tunsigned int index;'
	print >>f, '};'
	print >>f
	print >>f, 'static const struct action {'
	print >>f, '\tunsigned int i;'
	print >>f, '\tint a;'
	print >>f, '\tuint8_t action;;'
	print >>f, '\tunion {'
	print >>f, '\t\tstruct shift_move shift;'
	print >>f, '\t\tstruct reduce_move reduce;'
	print >>f, '\t}u;'
	print >>f, '}ACTION[] = {'
	for ((i,a), (c, v)) in sorted(lr.action.items()):
		print >>f, '\t{'
		print >>f, '\t\t.i = %d,'%i
		print >>f, '\t\t.a = %s,'%a.cname()
		print >>f, '\t\t.action = ACTION_%s,'%c.upper()
		if c == 'shift':
			print >>f, '\t\t.u.shift = { .t = %d },'%v
		elif c == 'reduce':
			index, r = v
			print >>f, '\t\t.u.reduce = {'
			print >>f, '\t\t\t.index = %d,'%index
			print >>f, '\t\t},'
		print >>f, '\t},'
	print >>f, '};'

# This should be the rule class, remove pos
def lrgen_c(lr, name, path):
	from os.path import join

	fn = join(path, name + '.h')
	print 'writing', fn

	f = open(fn, 'w')
	f.write('#ifndef _%s_H\n'%name.upper())
	f.write('#define _%s_H\n'%name.upper())
	f.write('\n')

	write_sym_defs(lr, f)
	f.write('\n')

	write_sym_names(lr, f)
	f.write('\n')

	f.write('#define INITIAL_STATE %d\n'%lr.initial)
	f.write('\n')

	write_productions_enum(lr, f)
	f.write('\n')

	write_production_table(lr, f)
	write_action_table(lr, f)
	f.write('\n')

	write_goto_table(lr, f)
	f.write('\n')

	f.write('#endif /* _%s_H */\n'%name.upper())
