#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <errno.h>
#include <ctype.h>

#include "lex.h"
#include "lex.c"

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

static int emit(struct _lexer *l, enum tok type)
{
	struct _tok tok;

	if ( !nul_terminate(l) )
		return 0;

	tok.t_file = l->l_name;
	tok.t_line = l->l_line;
	tok.t_col = l->l_col;
	tok.t_type = type;

	tok.t_u.tu_str = l->l_buf;

	return (*l->l_cb)(&tok, l->l_priv);
}

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
	new = l->l_state = next_state(old, sym);

	/* if we move from an accepting state to a non-accepting state
	 * then emit a token. This implements the greedy match heuristic.
	*/
	if ( old && accept[old] && (!new || !accept[new]) ) {
		int ret;
		ret = emit(l, accept[old]);
		clear_buf(l);
		l->l_state = initial_state;
		return ret;
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
		to_buf(l, sym);
	}else{
		if ( old == initial_state ) {
			fprintf(stderr, "%s: unexpected \\x%.2x(%c): "
				"line %u, col %u\n",
				l->l_name, sym,
				isprint(sym) ? sym : sym,
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
	printf("%u: %s\n", tok->t_type, tok->t_u.tu_str);
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
