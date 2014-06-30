from tokens import *

def read_file(fn):
	f = open(fn)
	lno = 1
	while True:
		l = f.readline()
		if l == '':
			break
		l = l.rstrip('\r\n')
		yield (lno, l)
		lno += 1

def lexemes(fn):
	for (lno, l) in read_file(fn):
		if l == '':
			yield (lno, l)
			continue
		elif l[0] == '#':
			continue
		while l:
			l = l.lstrip()
			if not l:
				continue
			if len(l) > 1 and l[0] == '<':
				x = l.split('>', 1)
				if len(x) > 1:
					x[0] = x[0] + '>'
			else:
				x = l.split(None, 1)
				x2 = l.split('<', 1)

				if len(x2[0]) < len(x[0]) and len(x2[0]):
					x = x2
					x[1] = '<' + x[1]

			if len(x) == 2:
				if len(x[0]) > 3 and x[0][-3:] == '...':
					x[0] = x[0][0:-3]
					x[1] = '... ' + x[1]
				l = x[1]
				yield (lno, x[0])
			else:
				yield (lno, x[0])
				l = ''
				continue

def tokenize(fn):
	def is_id(l):
		return len(l) > 2 and l[0] == '<' and l[-1:] == '>'
	state = 0
	for (lno, l) in lexemes(fn):
		if l == '':
			state = 0
			continue
		if state == 0:
			if is_id(l):
				state = 1
				yield TokHead(l[1:-1], lno)
			else:
				raise Exception("expected identifier")
		elif state == 1:
			if l == '::=':
				state = 2
				yield TokOpRewrite(lno)
			else:
				raise Exception("expected ::=")
		elif state == 2:
			if is_id(l):
				yield TokIdentifier(l[1:-1], lno)
			elif l == '|':
				yield TokOpChoice(lno)
			elif l == '[':
				yield TokOpLSquare(lno)
			elif l == ']':
				yield TokOpRSquare(lno)
			elif l == '{':
				yield TokOpLBrace(lno)
			elif l == '}':
				yield TokOpRBrace(lno)
			elif l == '...':
				yield TokOpEllipsis(lno)
			else:
				yield TokLiteral(l, lno)
