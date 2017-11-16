import os
import sys
import argparse
import io

grammer_stack = []

class CallPoint(object):
	COLON = ':'
	OPEN_PRAN = '('
	CLOSE_PRAN = ')'
	TARGET = 'target'
	ARGS = 'args'
	WITHIN = 'within'
	UNWITHIN = '!within'
	CALL = 'call'

	def __init__(self, expr):
		self.expr = expr.strip()
		self.ret = None
		self.func = None
		self.parameters = []
		self.descs = dict()

	def parse(self):
		colon = self.expr.find(CallPoint.COLON)
		self._signature(self.expr[ : colon])
		self._desc(self.expr[colon+1 : ])

	def _signature(self, sig):
		open_pran = sig.find(CallPoint.OPEN_PRAN)
		two = [item for item in sig[ : open_pran].split(' ') if item != '']
		assert len(two) == 2
		self.ret = two[0]
		self.func = two[1]
		close_pran = sig.rfind(CallPoint.CLOSE_PRAN)
		paras = sig[open_pran+1 : close_pran].strip()
		plst = [item for item in paras.split(',') if item != '']
		for parameter in plst:
			two = [item for item in parameter.split(' ') if item != '']
			# print('hehe ' + two[0] + ' ' + two[1])
			assert len(two) == 2
			# self.parameters.update({ two[0] : two[1] })
			self.parameters.append((two[0], two[1]))

	def _desc(self, desc):
		desc = desc.lstrip()
		lst = [item.strip() for item in desc.split('&&') if item != '']
		for item in lst:
			if item.startswith(CallPoint.TARGET):
				self.descs.update({ CallPoint.TARGET : item[item.find('(')+1 : item.rfind(')')].strip() })
			elif item.startswith(CallPoint.ARGS):
				self.descs.update({ CallPoint.ARGS : item[item.find('(')+1 : item.rfind(')')].strip() })
			elif item.startswith(CallPoint.WITHIN):
				self.descs.update({ CallPoint.WITHIN : item[item.find('(')+1 : item.rfind(')')].strip() })
			elif item.startswith(CallPoint.UNWITHIN):
				self.descs.update({ CallPoint.UNWITHIN : item[item.find('(')+1 : item.rfind(')')].strip() })
			elif item.startswith(CallPoint.CALL):
				call_to = item[item.find('(')+1 : item.rfind(')')].strip()
				self.descs.update({ CallPoint.CALL : call_to })
				self.call_type = self.analyze_call_type(call_to)
			else:
				continue	# TODO add more

	def analyze_call_type(self, call_to):
		call_list = call_to.split(' ')
		assert len(call_list) >= 2
		if call_list[1] == 'static':
			return 'static'
		elif call_list[1] == 'ctor':
			return 'ctor'
		else:
			return 'instance'

	def get_call_type(self):
		return self.call_type

	def get_call(self):
		return self.descs[CallPoint.CALL]

	def get_return(self):
		return self.ret

	def get_parameters(self):
		return self.parameters

	def __str__(self):
		return "\nCallPoint:\n" + self.expr + \
			   "\nReturn:\n" + self.ret + \
			   "\nName:\n" + self.func + \
			   "\nDescriptor:\n" + str(self.descs)
			   # "\nParameters:\n" + str(self.parameters) + \ 
			   # "\nDescriptor:\n" + str(self.descs)

class AspectJ(object):
	COMMA = ';'
	OPEN_BRACE = '{'
	CLOSE_BRACE = '}'
	COLON = ':'
	PROCEED = 'proceed'
	SEMI_COLON = ','
	OPEN_PRAN = '('
	CLOSE_PRAN = ')'

	JAVA = '.java'
	PUBLIC = 'public'
	NEWLINE = '\n'
	WHITESPACE = ' '
	CLASS = 'class'
	STATIC = 'static'

	def __init__(self, fname):
		self.fname = fname
		self.content = ''
		self.imports = []
		self.aspect = None
		self.bodys = dict()

	def read_file_content(self):
		with io.open(self.fname, 'r', encoding='utf-8') as file:
			for line in file.readlines():
				line = line.strip()
				if line.startswith('/*'):
					line = line[line.find('*/') + 2 : ]
					line = line.lstrip()
				if line != '' and not line.startswith('//'):	# only support comment with double slash
					self.content += line

	def parse(self):
		self._imports()
		self._aspect()
		self._body()

		for call_point in self.bodys:
			signature = call_point.get_call()
			func_name = signature[signature.rfind('.') + 1 : signature.rfind('(')]
			# print(func_name)
			# print(self.bodys[call_point])
			body = self.bodys[call_point]
			proceed = body.find(AspectJ.PROCEED)
			while proceed != -1:
				i = proceed + len(AspectJ.PROCEED)
				while body[i] != ',' and body[i] != ')':
					i += 1
				if body[i] != ')':
					body = body.replace(body[proceed : i+1], 'target.' + func_name + '(')
				else:
					body = body.replace(body[proceed : i+1], 'target.' + func_name + '()')
				proceed = body.find(AspectJ.PROCEED)
			self.bodys[call_point] = body
			# print(func_name)
			# print(self.bodys[call_point])

	def _imports(self):
		comma = 0
		while not self.content.startswith('aspect'):
			comma = self.content.find(AspectJ.COMMA)
			if self.content.startswith('import'):
				self.imports.append(self.content[ : comma])
			self.content = self.content[comma+1 :].lstrip()

	def _aspect(self):
		assert self.content.startswith('aspect')
		open_brace = self.content.find(AspectJ.OPEN_BRACE)
		lst = [item for item in self.content[ : open_brace].strip().split(' ') if item != '']
		self.aspect = lst[-1]
		self.content = self.content[open_brace : ]

	def _body(self):
		assert self.content.startswith(AspectJ.OPEN_BRACE)
		grammer_stack.append(AspectJ.OPEN_BRACE)
		self.content = self.content[1 : ]	# skip the open brace
		while len(grammer_stack) > 0:
			cut_point = self.content.find(AspectJ.OPEN_BRACE)
			call_point = self.content[ : cut_point].strip()
			tcallp = CallPoint(call_point)
			tcallp.parse()
			# print(tcallp)
			self.content = self.content[cut_point : ]
			(i, body) = self._extract_body()	# according to CallPoint info to extract the right java body.
			self.bodys.update({ tcallp : body })
			self.content = self.content[i :].lstrip()
			if len(self.content) == 0:
				print("Aspect syntax error")
				exit(1)
			if self.content[0] == AspectJ.CLOSE_BRACE:
				grammer_stack.pop()

		if len(self.content) != 1:	# only '}'
			print("Aspect syntax error")
			exit(1)

	def _extract_body(self):
		assert self.content[0] == AspectJ.OPEN_BRACE
		stack = ['{']
		i = 1
		while len(stack) > 0:
			if self.content[i] == AspectJ.OPEN_BRACE:
				stack.append(AspectJ.OPEN_BRACE)
			elif self.content[i] == AspectJ.CLOSE_BRACE:
				stack.pop()
			i += 1
		self.body = self.content[ : i].strip()
		return (i, self.content[ : i].strip())


	def get_imports(self):
		return self.imports

	def get_filename(self):
		return self.aspect

	def wirte_to_java(self, fn):
		with open(fn + AspectJ.JAVA, 'w') as file:
			for imp in self.imports:
				file.write(imp + AspectJ.COMMA + AspectJ.NEWLINE)
			file.write(AspectJ.PUBLIC + AspectJ.WHITESPACE + AspectJ.CLASS + AspectJ.WHITESPACE)
			file.write(fn)
			file.write(AspectJ.OPEN_BRACE + AspectJ.NEWLINE)

			for call_point in self.bodys:
				file.write(AspectJ.PUBLIC + AspectJ.WHITESPACE + AspectJ.STATIC + AspectJ.WHITESPACE)
				file.write(call_point.get_return() + AspectJ.WHITESPACE)
				signature = call_point.get_call()
				func_name = signature[: signature.rfind('(')]
				func_name = func_name[func_name.rfind('.')+1 : ]
				# print('where is function name: ' + func_name)
				# print('signature: ' + signature)
				file.write(func_name + AspectJ.OPEN_PRAN)
				parameters = call_point.get_parameters()
				s = ''
				for type_ in parameters:
					s += type_[0] + AspectJ.WHITESPACE + type_[1] + AspectJ.SEMI_COLON
				file.write(s[:-1] + AspectJ.CLOSE_PRAN + AspectJ.NEWLINE)
				file.write(self.bodys[call_point])
				file.write(AspectJ.NEWLINE)

			file.write(AspectJ.CLOSE_BRACE + AspectJ.NEWLINE)

	def __str__(self):
		return '\nContent:\n' + self.content + \
			   '\nImports:\n' + '\n'.join(self.imports) + \
			   '\nAspectJ:\n' + self.aspect + \
			   "\nBody:\n" + str(self.bodys) + '\n'


def test_imports(aj):
	aj._imports()

def test(aj):
	test_imports(aj)
	print(aj.get_imports())

def main():
	parser = argparse.ArgumentParser("AspectJ to JAVA")
	parser.add_argument('--apj', '-a', type=str, default='./aspect/androidAppActivityPolicy.aj')
	args = parser.parse_args()
	fname = args.apj
	apj = AspectJ(fname)
	apj.read_file_content()
	apj.parse()
	# print(apj)
	# test(apj)
	apj.wirte_to_java()

if __name__ == '__main__':
	main()