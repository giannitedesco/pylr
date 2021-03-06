from os.path import splitext, basename, join
from io import FileIO, TextIOWrapper

class HFile(TextIOWrapper):
    def __include_guard_top(self):
        self.write('#ifndef %s\n'%self.inclguard)
        self.write('#define %s\n'%self.inclguard)

    def __include_guard_bottom(self):
        self.write('#endif /* %s */\n'%self.inclguard)

    def newline(self):
        self.write('\n')

    def __init__(self, fn, includedir = '.'):
        fn = join(includedir, fn)
        f = FileIO(fn, mode='w')
        super().__init__(f, encoding = 'utf-8')
        print((' [SCANGEN-H] %s'%(join(includedir, fn))))
        self.write('/* auto generated by scangen.py */\n')
        self.inclguard = '_%s_H'%basename(splitext(fn)[0]).upper()
        self.__include_guard_top()
        self.newline()

    def __del__(self):
        self.__include_guard_bottom()
        self.close()

    def token_enum(self, dfa):
        self.write('enum tok {\n')
        self.write('\tTOK_EOF = -1, /* force signed enum */\n')
        self.write('\tTOK_UNKNOWN,\n')
        s = set()
        for v in list(dfa.final.values()):
            s.update([x for x in v])
        s = sorted([(x.lineno, x.rule_name) for x in s])
        for (lineno,x) in s:
            tn = 'TOK_%s'%x.upper().replace(' ', '_')
            self.write('\t%s,\n'%tn)
        self.write('};\n\n')
        self.write('#define TOK_UNKNOWN TOK_UNKNOWN\n')
        for (lineno,x) in s:
            tn = 'TOK_%s'%x.upper().replace(' ', '_')
            self.write('#define %s %s\n'%(tn, tn))
        self.write('\n')
        return

    def decls(self):
        self.write(\
'''struct _tok {
	const char *t_file;
	unsigned int t_line;
	unsigned int t_col;
	enum tok t_type;
	union {
		const char *tu_str;
		unsigned long long tu_uint;
		long long int tu_int;
		double tu_float;
	}t_u;
};

typedef struct _tok *tok_t;
typedef int(*token_cb)(tok_t tok, void *priv);
typedef struct _lexer *lexer_t;

lexer_t lexer_new(const char *name, token_cb cb, void *priv);
int lexer_feed(lexer_t lex, char *buf, size_t len);
int lexer_eof(lexer_t lex);
void lexer_free(lexer_t lex);

''')

class CFile(TextIOWrapper):
    def sysinclude(self, path):
        self.write('#include <%s>\n'%path)

    def include(self, path):
        self.write('#include "%s"\n'%path)

    def newline(self):
        self.write('\n')

    def __init__(self, fn, incl=[], sysincl=[], srcdir='.'):
        fn = join(srcdir, fn)
        f = FileIO(fn, mode='w')
        super().__init__(f, encoding = 'utf-8')
        print((' [SCANGEN-C] %s'%(join(srcdir, fn))))
        self.__action = {
                'str': self.__action_str,
                'int': self.__action_int,
                'uint': self.__action_uint,
                'numeric': self.__action_float,
                'float': self.__action_float,
        }
        self.write('/* auto generated by scangen.py */\n')
        self.sysinclude('stdint.h')
        self.sysinclude('stdio.h')
        self.sysinclude('stdlib.h')
        self.sysinclude('errno.h')
        self.sysinclude('ctype.h')
        for x in sysincl:
            self.sysinclude(x)
        self.newline()
        for x in incl:
            self.include(x)
        if incl:
            self.newline()

    def __del__(self):
        self.close()

    def state_type(self, num_states):
        if num_states + 1 < 2**8:
            t = 'uint8_t'
        elif num_states + 1 < 2**16:
            t = 'uin16_t'
        elif num_states + 1 < 2**32:
            t = 'uint32_t'
        else:
            t = 'uint64_t'
        self.write('typedef %s dfa_state_t;\n\n'%t)

    def transition_table(self, dfa):
        self.write('static const dfa_state_t ')
        self.write('trans[%u][0x100] = {\n'%(dfa.num_states + 1))
        for pre, d in list(dfa.trans.items()):
            self.write('\t[ %u ] = {\n'%(pre + 1))
            for sym, post in sorted(d.items()):
                self.write('\t\t[\'%s\'] = %u,\n'%\
                        (sym, post + 1))
            self.write('\t},\n')
        self.write('};\n\n')
        self.write('static inline dfa_state_t next_state')
        self.write('(dfa_state_t state, char sym)\n')
        self.write('{\n')
        self.write('\treturn trans[state][(uint8_t)sym];\n')
        self.write('}\n\n')

    def transition_func(self, dfa):
        self.write('static inline dfa_state_t next_state')
        self.write('(dfa_state_t state, char sym)\n')
        self.write('{\n')
        self.write('\tswitch(state) {\n')
        for pre, d in list(dfa.trans.items()):
            self.write('\tcase %u:\n'%(pre + 1))
            self.write('\t\tswitch(sym) {\n')
            for sym, post in sorted(d.items()):
                self.write('\t\tcase \'%s\':\n'%sym)
                self.write('\t\t\treturn %u;\n'%(post + 1))
            self.write('\t\tdefault:\n')
            self.write('\t\t\treturn 0;\n')
            self.write('\t\t}\n')
        self.write('\tdefault:\n')
        self.write('\t\treturn 0;\n')
        self.write('\t}\n')
        self.write('}\n\n')

    def accept_table(self, dfa):
        self.write('static const dfa_state_t ')
        self.write('accept[%u] = {\n'%(dfa.num_states + 1))
        for i in range(dfa.num_states):
            if i in dfa.final:
                x = dfa.final[i][0]
                v = x.rule_name.upper().replace(' ', '_')
            else:
                continue
            self.write('\t[ %u ] = TOK_%s,\n'%(i + 1, v))
        self.write('};\n\n')

        self.write('static const dfa_state_t ')
        self.write('initial_state = %s;\n\n'%(dfa.initial + 1))
    
    def __action_str(self):
        self.write(\
'''		if ( !nul_terminate(l) )
			return 0;
		t->t_u.tu_str = l->l_buf;
		return 1;
''')

    def __action_uint(self):
        self.write(\
'''		if ( !nul_terminate(l) )
			return 0;
		t->t_u.tu_uint = strtoull(l->l_buf, NULL, 0);
		return 1;
''')

    def __action_int(self):
        self.write(\
'''		if ( !nul_terminate(l) )
			return 0;
		t->t_u.tu_int = strtoll(l->l_buf, NULL, 0);
		return 1;
''')

    def __action_float(self):
        self.write(\
'''		if ( !nul_terminate(l) )
			return 0;
		t->t_u.tu_float = strtod(l->l_buf, NULL);
		return 1;
''')

    def action_func(self, dfa):
        s = set()
        for v in list(dfa.final.values()):
            s.update([x for x in v])
        m = {}
        for a, l, n in sorted([(x.action,\
                    x.lineno,\
                    x.rule_name) for x in s]):
            if a == 'discard':
                continue
            s = 'TOK_%s'%(n.upper().replace(' ', '_'))
            m.setdefault(a, []).append(s)

        self.write('static int action(struct _lexer *l, ' +
                'struct _tok *t)\n')
        self.write('{\n')
        self.write('\tswitch(t->t_type) {\n')
        for k in sorted(m.keys()):
            for v in m[k]:
                self.write('\tcase %s:\n'%v)
            self.__action[k]()
        self.write('\tdefault:\n')
        self.write('\t\t/* do nothing */\n')
        self.write('\t\treturn 1;\n');
        self.write('\t}\n')
        self.write('}\n\n')

    def actions(self):
        self.write(\
'''
static int to_buf(struct _lexer *l, char sym)
{
	if ( l->l_len >= l->l_max ) {
		char *new;
		new = realloc(l->l_buf, l->l_len + BUF_INCREMENT);
		if ( NULL== new )
			return 0;
		l->l_buf = new;
		l->l_max = l->l_len + BUF_INCREMENT;
		//printf("upped buffer to %u bytes\\n",
		//	l->l_len + BUF_INCREMENT);
	}
	l->l_buf[l->l_len++] = sym;
	return 1;
}

static void clear_buf(struct _lexer *l)
{
	l->l_len = 0;
}

static inline int nul_terminate(struct _lexer *l)
{
	return to_buf(l, '\\0');
}

''')

    def define_struct(self):
        self.write(\
'''
#define BUF_INCREMENT 128
struct _lexer {
	const char *l_name;
	token_cb l_cb;
	void *l_priv;
	char *l_buf;
	unsigned int l_len;
	unsigned int l_max;
	unsigned int l_line;
	unsigned int l_col;
	dfa_state_t l_state;
};

''')
    def boilerplate(self, dfa):
        self.define_struct()
        self.actions()
        self.action_func(dfa)
        self.write(\
'''
lexer_t lexer_new(const char *name, token_cb cb, void *priv)
{
	struct _lexer *l;

	l = calloc(1, sizeof(*l));
	if ( NULL == l )
		goto out;

	l->l_name = name;
	l->l_cb = cb;
	l->l_priv = priv;
	l->l_state = initial_state;
	l->l_line++;
out:
	return l;
}

static int emit(struct _lexer *l, enum tok type)
{
	struct _tok tok;

	tok.t_file = l->l_name;
	tok.t_line = l->l_line;
	tok.t_col = l->l_col;
	tok.t_type = type;

	if ( !action(l, &tok) )
		return 0;

	return (*l->l_cb)(&tok, l->l_priv);
}

static int lexer_symbol(lexer_t l, char sym)
{
	unsigned int old, new;

	if ( sym == '\\n' ) {
		l->l_line++;
		l->l_col = 0;
	}else{
		l->l_col++;
	}

again:
	old = l->l_state;
	new = l->l_state = next_state(old, sym);

	/* if we move from an accepting state to a non-accepting state
	 * then emit a token. This implements the greedy match heuristic.
	*/
	if ( old && accept[old] && (!new /*|| !accept[new] */) ) {
		int ret;
		ret = emit(l, accept[old]);
		clear_buf(l);

		l->l_state = initial_state;
		if ( !to_buf(l, sym) )
			return 0;
		if ( !ret )
			return 0;
		goto again;
	}

	if ( new ) {
		/* if we move from initial state to a non rejecting state
		 * then this is the start of a new token.
		*/
		if ( old == initial_state ) {
			clear_buf(l);
		}

		/* buffer up every character so long as we're in a
		 * non-rejecting state
		*/
		if ( !to_buf(l, sym) )
			return 0;
	}else{
		if ( old == initial_state ) {
			fprintf(stderr, "%s: unexpected \\\\x%.2x(%c): "
				"line %u, col %u\\n",
				l->l_name, sym,
				isprint(sym) ? sym : '?',
				l->l_line, l->l_col);
			return 0;
		}else{
			/* we move from a non-accepting state to a rejecting
			 * state, so we encountered a valid token for which
			 * there was no action / discard action. So in this
			 * case we pretend we were in the initial state all
			 * along, to start on the next token.
			*/
			l->l_state = initial_state;
			goto again;
		}
	}

	return 1;
}

int lexer_feed(lexer_t l, char *buf, size_t len)
{
	size_t i;
	for(i = 0; i < len; i++) {
		if ( !lexer_symbol(l, buf[i]) )
			return 0;
	}
	return 1;
}

int lexer_eof(lexer_t l)
{
	return lexer_symbol(l, '\\n');
}

void lexer_free(lexer_t l)
{
	if ( l ) {
		free(l->l_buf);
		free(l);
	}
}
''')

def dfa_c(dfa, base_name, srcdir, includedir, table):
    cfn = base_name + '.c'
    hfn = base_name + '.h'
    c = CFile(cfn, incl = [hfn], srcdir = srcdir)
    c.state_type(dfa.num_states)
    if table:
        c.transition_table(dfa)
    else:
        c.transition_func(dfa)
    c.accept_table(dfa)
    c.boilerplate(dfa)

    h = HFile(hfn, includedir = includedir)
    h.token_enum(dfa)
    h.decls()
