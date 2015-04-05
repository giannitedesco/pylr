#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <errno.h>
#include <ctype.h>
#include <stdint.h>
#include <assert.h>

#include "lex.h"
#include "grammar.h"

#if 0
#define dprintf(...) printf(__VA_ARGS__)
#else
#define dprintf(x...) do { } while(0);
#endif

#ifndef ARRAY_SIZE
#define ARRAY_SIZE(x) (sizeof(x)/sizeof(x[0]))
#endif

#define STACK_INCREMENT		32

#define PARSE_ERR(_tok, fmt, x...) \
	fprintf(stderr, "Parse Error: %s:%u: " fmt, \
		(_tok)->t_file, (_tok)->t_line, ##x)
#define PARSE_WARN(_tok, fmt, x...) \
	fprintf(stderr, "Warning: %s:%u: " fmt, \
		(_tok)->t_file, (_tok)->t_line, ##x)

struct _parser {
	unsigned int *stack;
	unsigned int stack_top;
	unsigned int stack_max;

};

static const struct action *action_lookup(unsigned int s,
						int a)
{
	unsigned int i;

	for(i = 0; i < ARRAY_SIZE(ACTION); i++) {
		if ( ACTION[i].i == s && ACTION[i].a == a) {
			return &ACTION[i];
		}
	}

	return NULL;
}

static const int goto_lookup(unsigned int s, int A, unsigned int *res)
{
	unsigned int i;

	for(i = 0; i < ARRAY_SIZE(GOTO); i++) {
		if ( GOTO[i].i == s && GOTO[i].A == A) {
			dprintf(" - GOTO[%u,%s] = %u\n",
				s, sym_name(A), GOTO[i].j);
			*res = GOTO[i].j;
			return 1;
		}
	}

	return 0;
}

static int stack_push(struct _parser *p, unsigned int state)
{
	if ( p->stack_top >= p->stack_max ) {
		void *new;
		size_t sz;

		sz = (p->stack_max + STACK_INCREMENT) * sizeof(int);
		new = realloc(p->stack, sz);
		if ( NULL == new ) {
			fprintf(stderr, "%s\n", strerror(errno));
			return 0;
		}
		p->stack = new;
		p->stack_max += STACK_INCREMENT;
	}
	p->stack[p->stack_top++] = state;
	return 1;
}

static unsigned int stack_pop(struct _parser *p)
{
	assert(p->stack_top);
	return p->stack[--p->stack_top];
}

static unsigned int stack_top(struct _parser *p)
{
	assert(p->stack_top);
	return p->stack[p->stack_top - 1];
}

static int parser_token(struct _parser *p, tok_t tok)
{
	const struct action *a;
	unsigned int i, j;
	unsigned int s;

	//printf("token: %s\n", sym_name(tok->t_type));

again:
	s = stack_top(p);
	dprintf("Lookup ACTION[%u,%s]\n", stack_top(p), sym_name(tok->t_type));
	a = action_lookup(stack_top(p), tok->t_type);
	if ( NULL == a ) {
		printf("Parse error\n");
		return 0;
	}

	switch(a->action) {
	case ACTION_ACCEPT:
		dprintf("accept\n");
		break;
	case ACTION_SHIFT:
		dprintf("shift\n");
		stack_push(p, a->u.shift.t);
		dprintf(" - state now %u\n", stack_top(p));
		if ( tok->t_type == SYM_EOF ) {
			goto again;
		}
		break;
	case ACTION_REDUCE:
		dprintf("reduce (len %u)\n", a->u.reduce.len);
		for(i = 0; i < a->u.reduce.len; i++) {
			dprintf(" - pop %u\n", stack_top(p));
			stack_pop(p);
		}
		dprintf(" - state now %u\n", stack_top(p));
		if ( !goto_lookup(stack_top(p), a->u.reduce.head, &j) ) {
			return 0;
		}
		stack_push(p, j);
		dprintf(" - state now %u\n", stack_top(p));
		printf(" - reduce: %s\n", a->u.reduce.reduction);
		goto again;
	}
	printf("\n");
	return 1;
}

static int parser_eof(struct _parser *p)
{
	struct _tok tok;

	tok.t_type = SYM_EOF;

	if ( !parser_token(p, &tok) ) {
		return 0;
	}
}

static struct _parser *parser_new(void)
{
	struct _parser *p;

	p = calloc(1, sizeof(*p));
	if ( NULL == p ) {
		fprintf(stderr, "%s\n", strerror(errno));
		goto out;
	}

	if ( !stack_push(p, INITIAL_STATE) )
		goto out_free;

	/* success */
	goto out;

out_free:
	free(p);
	p = NULL;
out:
	return p;
}

static int tok_cb(tok_t tok, void *priv)
{
	struct _parser *p = priv;

	return parser_token(priv, tok);
}

static int lex_file(const char *fn)
{
	struct _parser *p;
	lexer_t lex;
	char buf[8192];
	FILE *f;
	size_t sz;
	int ret = 0;

	printf("opening %s\n", fn);

	p = parser_new();
	if ( NULL == p )
		goto out;

	lex = lexer_new(fn, tok_cb, p);
	if ( NULL == lex )
		goto out_free_parser;

	f = fopen(fn, "r");
	if ( NULL == f ) {
		fprintf(stderr, "open: %s: %s\n", fn, strerror(errno));
		goto out_free;
	}

	while((sz = fread(buf, 1, sizeof(buf), f))) {
		if  (!lexer_feed(lex, buf, sz)) {
			goto out_close;
		}
	}

	if ( ferror(f) || !lexer_eof(lex) || !parser_eof(p) ) {
		fprintf(stderr, "parse: %s: %s\n", fn, strerror(errno));
		goto out_close;
	}

	/* success */
	printf("OK\n");
	ret = 1;

out_close:
	fclose(f);
out_free:
	lexer_free(lex);
out_free_parser:
out:
	return ret;
}

int main(int argc, char **argv)
{
	int i;

	printf("Start:\n\n");
	for(i = 1; i < argc; i++) {
		if ( !lex_file(argv[i]) )
			printf("%s: parse: fucked\n", argv[i]);
	}
	return 0;
}
