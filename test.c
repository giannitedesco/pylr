#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <errno.h>
#include <ctype.h>

#include "lex.h"

static int tok_cb(tok_t tok, void *priv)
{
	switch(tok->t_type) {
#ifdef TOK_LITERAL
	case TOK_LITERAL:
		printf("TOK_LITERAL: %s\n", tok->t_u.tu_str);
		break;
#endif
#ifdef TOK_IDENTIFIER
	case TOK_IDENTIFIER:
		printf("TOK_IDENTIFIER: %s\n", tok->t_u.tu_str);
		break;
#endif
	default:
		printf("tok type %u\n", tok->t_type);
		break;
	}
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
