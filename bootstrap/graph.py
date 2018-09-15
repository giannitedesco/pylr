class Graph(object):
    def __init__(self, name, fn):
        f = open(fn, 'w')
        f.write('digraph %s {\n'%self.q(name))
        f.write('\tgraph[rankdir=LR]\n')
        f.write('\tnode [shape = circle];\n')
        f.write('\n')
        self.f = f
        super(Graph, self).__init__()
    def q(self, s):
        return '\"%s\"'%s
    def add_node(self, n, **kwargs):
        n = self.q(n)
        a = ' '.join(map(lambda (k,v):'%s=%s'%(k, self.q(v)),
                kwargs.items()))
        self.f.write('%s [%s];\n'%(n,a))
    def add_edge(self, pre, post, label):
        pre = self.q(pre)
        post = self.q(post)
        if label == ' ':
            self.f.write('%s -> %s [label="<space>" color=green];\n'%(pre, post))
            return
        if label == '#':
            self.f.write('%s -> %s [label="#" color=magenta];\n'%(pre, post))
            return
        if label == '\\n':
            self.f.write('%s -> %s [label="<LF>" color=orange];\n'%(pre, post))
            return
        if label == '"':
            label = '\\"'
        label = self.q(label)
        self.f.write('%s -> %s [label=%s];\n'%(pre, post, label))
    def __del__(self):
        #print 'finishing graph'
        self.f.write('}\n')
        self.f.close()

