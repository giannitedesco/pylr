from tokens import *

def read_file(fn):
	f = open(fn)
	while True:
		l = f.readline()
		if l == '':
			break
		l = l.rstrip('\r\n')
		yield l

def lexemes(fn):
	for l in read_file(fn):
		if l == '':
			yield ''
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
				yield x[0]
			else:
				yield x[0]
				l = ''
				continue

def tokenize(fn):
	def is_id(l):
		return len(l) > 2 and l[0] == '<' and l[-1:] == '>'
	state = 0
	for l in lexemes(fn):
		if l == '':
			state = 0
			continue
		if state == 0:
			if is_id(l):
				state = 1
				yield TokHead(l[1:-1])
			else:
				raise Exception("expected identifier")
		elif state == 1:
			if l == '::=':
				state = 2
				yield TokOpRewrite()
			else:
				raise Exception("expected ::=")
		elif state == 2:
			if is_id(l):
				yield TokIdentifier(l[1:-1])
			elif l == '|':
				yield TokOpChoice()
			elif l == '[':
				yield TokOpLSquare()
			elif l == ']':
				yield TokOpRSquare()
			elif l == '{':
				yield TokOpLBrace()
			elif l == '}':
				yield TokOpRBrace()
			elif l == '...':
				yield TokOpEllipsis()
			else:
				yield TokLiteral(l)
