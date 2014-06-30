#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <errno.h>
#include <ctype.h>

#include "lex.h"
#include "lex.c"

struct _tok {
	const char *t_file;
	unsigned int t_line;
	unsigned int t_col;
	enum tok t_type;
	union {
		const char *tu_identifier;
		unsigned long long tu_int;
		double tu_float;
	}t_u;
};

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

static int to_buf(struct _lexer *l, char sym)
{
	if ( l->l_len >= l->l_max ) {
		char *new;
		new = realloc(l->l_buf, l->l_len + BUF_INCREMENT);
		if ( NULL== new )
			return 0;
		l->l_buf = new;
		l->l_max = l->l_len + BUF_INCREMENT;
		//printf("upped buffer to %u bytes\n", l->l_len + BUF_INCREMENT);
	}
	l->l_buf[l->l_len++] = sym;
	return 1;
}

static void clear_buf(struct _lexer *l)
{
	l->l_len = 0;
}

static int nul_terminate(struct _lexer *l)
{
	return to_buf(l, '\0');
}

static int emit(struct _lexer *l)
{
	struct _tok tok;

	if ( !nul_terminate(l) )
		return 0;

	tok.t_file = l->l_name;
	tok.t_line = l->l_line;
	tok.t_col = l->l_col;

	tok.t_u.tu_identifier = l->l_buf;

	return (*l->l_cb)(&tok, l->l_priv);
}

#define DEBUG 0
static int lexer_symbol(lexer_t l, char sym)
{
	unsigned int old, new;

	if ( sym == '\n' ) {
		l->l_line++;
		l->l_col = 0;
	}else{
		l->l_col++;
	}

again:
	old = l->l_state;
	new = l->l_state = next_symbol(old, sym);
	if ( old && accept[old] && (!new || !accept[new]) ) {
#if DEBUG
		printf("END TOKEN: %s '%.*s'\n\n",
			action[old], (int)l->l_len, l->l_buf);
#else
//		if ( strcmp(action[old], "comment") &&
//				strcmp(action[old], "whitespace"))
#endif
		if ( !emit(l) )
			return 9;
		clear_buf(l);
	}

	if ( !new ) {
		if ( old == initial_state ) {
			fprintf(stderr, "%s: unexpected \\x%.2x(%c): "
				"line %u, col %u\n",
				l->l_name, sym,
				isprint(sym) ? sym : sym,
				l->l_line, l->l_col);
		}else{
			l->l_state = initial_state;
			goto again;
		}
		return 0;
	}
	if ( old == initial_state && new ) {
#if DEBUG
		printf("BEGIN TOKEN\n");
#endif
		clear_buf(l);
	}
	to_buf(l, sym);

#if DEBUG
	if ( sym == '\n' ) {
		printf("symbol is '\\n' : ");
	}else if ( sym == '\t' ) {
		printf("symbol is '\\t' : ");
	}else{
		printf("symbol is '%c'  : ", sym);
	}

	printf("%u (accept=%u reject=%u) -> "
		"%u (accept=%u reject=%u)\n",
		old, accept[old], old == 0,
		new, accept[new], new == 0);
#endif

	if ( !l->l_state )
		l->l_state = initial_state;

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
	return lexer_symbol(l, '\n');
}

void lexer_free(lexer_t l)
{
	if ( l ) {
		free(l->l_buf);
		free(l);
	}
}

static int tok_cb(tok_t tok, void *priv)
{
	printf("%s\n", tok->t_u.tu_identifier);
	return 1;
}

static int lex_file(const char *fn)
{
	lexer_t lex;
	char buf[8192];
	FILE *f;
	size_t sz;
	int ret = 0;

	printf("opening %s\n", fn);

	lex = lexer_new(fn, tok_cb, NULL);
	if ( NULL == lex )
		goto out;

	f = fopen(fn, "r");
	if ( NULL == f ) {
		fprintf(stderr, "open: %s: %s", fn, strerror(errno));
		goto out_free;
	}

	while((sz = fread(buf, 1, sizeof(buf), f))) {
		if  (!lexer_feed(lex, buf, sz)) {
			goto out_close;
		}
	}

	if ( ferror(f) || !lexer_eof(lex) ) {
		fprintf(stderr, "lex: %s: %s", fn, strerror(errno));
		goto out_close;
	}

	/* success */
	printf("OK\n");
	ret = 1;

out_close:
	fclose(f);
out_free:
	lexer_free(lex);
out:
	return ret;
}
int main(int argc, char **argv)
{
	int i;

	for(i = 1; i < argc; i++) {
		if ( !lex_file(argv[i]) )
			printf("%s: fucked\n", argv[i]);
	}
	return 0;
}
