from .symbol import *

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
    f.write('#define SYM_EOF %d\n'%SymEof.val)
    f.write('#define SYM_EPSILON %d\n'%SymEpsilon.val)
    for nt in sorted(lr.lang.reachables):
        if not isinstance(nt, NonTerminal):
            continue
        f.write('#define %s %d\n'%(nt.cname, nt.val))

def write_sym_names(lr, f):
    f.write('static inline const char *sym_name(int sym)\n')
    f.write('{\n')
    f.write('\tswitch(sym) {\n')
    for nt in sorted(lr.lang.reachables):
        f.write('\tcase %s:\n'%(nt.cname))
        f.write('\t\treturn "%s";\n'%(nt.name))
    #f.write('\tcase SYM_EPSILON:\n')
    #f.write('\t\treturn "EPSILON";\n')
    f.write('\tdefault:\n')
    f.write('\t\treturn "<<UNKNOWN>>";\n')
    f.write('\t}\n')
    f.write('}\n')

def write_goto_table(lr, f):
    print('static const struct {', file=f)
    print('\tunsigned int i;', file=f)
    print('\tint A;', file=f)
    print('\tunsigned int j;', file=f)
    print('}GOTO[] = {', file=f)
    for ((i, A), j) in sorted(lr.goto.items()):
        print('\t{ %d, %s, %d },'%(i, A.cname, j), file=f)
    print('};', file=f)

def write_productions_enum(lr, f):
    print('enum production_idx {', file=f)
    for k in sorted(lr.productions.keys()):
        print("\t%s,"%k, file=f)
    print('\tNR_PRODUCTIONS,', file=f)
    print("};", file=f)

    t = large_enough_type(len(list(lr.productions.keys())))
    print(file=f)
    print('typedef %s production_idx_t;'%t, file=f)

def write_production_table(lr, f):
    print('static const struct production {', file=f)
    print('\tunsigned int len;', file=f)
    print('\tint head;', file=f)
    print('\tproduction_idx_t action;', file=f)
    print('}productions[] = {', file=f)
    for v, k in sorted([(v, k) for (k, v) in \
                list(lr.productions.items())]):
        (index, plen, head) = v
        print('\t{', file=f)
        print('\t\t.action = %s,'%k, file=f)
        print('\t\t.len = %d,'%plen, file=f)
        print('\t\t.head = %s,'%head.cname, file=f)
        print('\t},', file=f)
    print('};', file=f)

def write_action_table(lr, f):
    print('#define ACTION_ERROR\t0', file=f)
    print('#define ACTION_ACCEPT\t1', file=f)
    print('#define ACTION_SHIFT\t2', file=f)
    print('#define ACTION_REDUCE\t3', file=f)
    print(file=f)
    print('struct shift_move {', file=f)
    print('\tunsigned int t;', file=f)
    print('};', file=f)
    print(file=f)
    print('struct reduce_move {', file=f)
    print('\tunsigned int index;', file=f)
    print('};', file=f)
    print(file=f)
    print('static const struct action {', file=f)
    print('\tunsigned int i;', file=f)
    print('\tint a;', file=f)
    print('\tuint8_t action;;', file=f)
    print('\tunion {', file=f)
    print('\t\tstruct shift_move shift;', file=f)
    print('\t\tstruct reduce_move reduce;', file=f)
    print('\t}u;', file=f)
    print('}ACTION[] = {', file=f)
    for ((i,a), (c, v)) in sorted(lr.action.items()):
        print('\t{', file=f)
        print('\t\t.i = %d,'%i, file=f)
        print('\t\t.a = %s,'%a.cname, file=f)
        print('\t\t.action = ACTION_%s,'%c.upper(), file=f)
        if c == 'shift':
            print('\t\t.u.shift = { .t = %d },'%v, file=f)
        elif c == 'reduce':
            index, r = v
            print('\t\t.u.reduce = {', file=f)
            print('\t\t\t.index = %d,'%index, file=f)
            print('\t\t},', file=f)
        print('\t},', file=f)
    print('};', file=f)

# This should be the rule class, remove pos
def lrgen_c(lr, name, srcdir, incdir):
    from os.path import join

    fn = join(incdir, name + '.h')
    print('writing', fn)

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
