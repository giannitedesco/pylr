from os.path import splitext, basename

class HFile(file):
	def __include_guard_top(self):
		self.write('#ifndef %s\n'%self.inclguard)
		self.write('#define %s\n'%self.inclguard)

	def __include_guard_bottom(self):
		self.write('#endif /* %s */\n'%self.inclguard)

	def newline(self):
		self.write('\n')

	def __init__(self, fn):
		super(HFile, self).__init__(fn, 'w')
		self.write('/* auto generated by scangen.py */\n')
		self.inclguard = '_%s_H'%basename(splitext(fn)[0]).upper()
		self.__include_guard_top()
		self.newline()

	def __del__(self):
		self.__include_guard_bottom()
		self.close()

	def token_enum(self, dfa):
		self.write('enum tok {\n')
		self.write('\tTOK_UNKNOWN,\n')
		s = set()
		for v in dfa.final.values():
			s.update([x for x in v])
		s = sorted([(x.lineno, x.rule_name) for x in s])
		for (lineno,x) in s:
			self.write('\tTOK_%s,\n'%\
					x.upper().replace(' ', '_'))
		self.write('};\n\n')
		return
	def decls(self):
		self.write(\
'''typedef struct _tok *tok_t;
typedef int(*token_cb)(tok_t tok, void *priv);
typedef struct _lexer *lexer_t;

lexer_t lexer_new(const char *name, token_cb cb, void *priv);
int lexer_feed(lexer_t lex, char *buf, size_t len);
int lexer_eof(lexer_t lex);
void lexer_free(lexer_t lex);

''')

class CFile(file):
	def sysinclude(self, path):
		self.write('#include <%s>\n'%path)

	def include(self, path):
		self.write('#include "%s"\n'%path)

	def newline(self):
		self.write('\n')

	def __init__(self, fn, incl=[], sysincl=[]):
		super(CFile, self).__init__(fn, 'w')
		self.write('/* auto generated by scangen.py */\n')
		self.sysinclude('stdint.h')
		for x in sysincl:
			self.sysinclude(x)
		self.newline()
		for x in incl:
			self.include(x)
		if incl:
			self.newline()

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
		for pre, d in dfa.trans.items():
			self.write('\t[ %u ] = {\n'%(pre + 1))
			for sym, post in sorted(d.items()):
				self.write('\t\t[\'%s\'] = %u,\n'%\
						(sym, post + 1))
			self.write('\t},\n')
		self.write('};\n\n')
		self.write('static inline dfa_state_t next_symbol')
		self.write('(dfa_state_t state, char sym)\n')
		self.write('{\n')
		self.write('\treturn trans[state][(uint8_t)sym];\n')
		self.write('}\n\n')

	def transition_func(self, dfa):
		self.write('static inline dfa_state_t next_symbol')
		self.write('(dfa_state_t state, char sym)\n')
		self.write('{\n')
		self.write('\tswitch(state) {\n')
		for pre, d in dfa.trans.items():
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
		for i in xrange(dfa.num_states):
			if i in dfa.final:
				x = dfa.final[i][0]
				v = x.rule_name.upper().replace(' ', '_')
			else:
				continue
			self.write('\t[ %u ] = TOK_%s,\n'%(i + 1, v))
		self.write('};\n\n')

		self.write('static const dfa_state_t ')
		self.write('initial_state = %s;\n\n'%(dfa.initial + 1))

	def __del__(self):
		self.close()

