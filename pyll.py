#!/usr/bin/python3

from bootstrap import *

def read_file(fn):
    f = open(fn)
    while True:
        l = f.readline()
        if l == '':
            break
        l = l.rstrip('\r\n')
        yield l

def read_terminals(fn):
    state = 0
    for l in read_file(fn):
        if not l:
            continue
        if state == 0:
            if l == 'enum tok {':
                state = 1
        elif state == 1:
            if l == '};':
                break
            l = l.split(',', 1)
            yield Terminal(l[0].strip())

def read_productions(g, fn):
    for l in read_file(fn):
        if not l or l[0] == '#':
            continue
        l = l.split()
        assert(l[1] == '->')
        pnt = g.get(l[0])
        if not l[2:]:
            r = [SymEpsilon]
        else:
            r = list(map(g.get, l[2:]))
        p = Production(pnt, r)
        yield p

def main(argv):
    EXIT_SUCCESS = 0
    EXIT_FAILURE = 1

    g = Grammar()
    for t in read_terminals(argv[1]):
        g.symbol(t)

    start_sym = None
    for p in read_productions(g, argv[2]):
        if start_sym is None:
            start_sym = p.nt.name
        g.production(p)

    # Add start symbol as RealStart then EOF
    print('Taking %s as start symbol'%start_sym)
    g.augment(start_sym)

    g.construct_markers()
    g.eliminate_left_recursion()

    p = LLGen(g, 'S')

    p.write_tables('grammar', path='./include')

    return EXIT_SUCCESS

if __name__ == '__main__':
    from sys import argv
    raise SystemExit(main(argv))
