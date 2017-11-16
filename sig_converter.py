# -*- coding: utf-8 -*-

import argparse
import re

# types
VOID, BYTE, SHORT, INT, LONG, FLOAT, DOUBLE, BOOLEAN, CHAR, OBJECT, ARRAY = 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10

TYPES = { 'B', 'S', 'I', 'J', 'F', 'D', 'Z', 'V', 'L' }

TYPE_MAP = {'byte'		: 'B',
			'short'		: 'S',
			'int'		: 'I',
			'long'		: 'J',
			'float'		: 'F',
			'double'	: 'D',
			'boolean'	: 'Z',
			'void'		: 'V'}

# convert java prototype to smali form
class Converter(object):
	
	def __init__(self, sig):
		self.sig = sig
		if self.split() < 0:
			exit(1)

	def __str__(self):
		return ' '.join([self.ret, self.reciver, self.func])

	# TODO: syntax definition.
	def split(self):

		delim_space = self.sig.find(' ')
		if delim_space == -1:
			return -1
		self.ret = self.sig[ : delim_space].strip()
		
		delim_colon = self.sig.find(':')
		if delim_colon == -1:
			return -1
		self.reciver = self.sig[delim_space+1 : delim_colon].strip()
		
		self.func = self.sig[delim_colon+2 : self.sig.rfind(')')+1].strip()

		return 1

	def _primitive(self, t):
		return TYPE_MAP[t]

	def _object(self, obj):
		parts = obj.split('.')
		return 'L' + '/'.join(parts) + ';'

	def _array(self, brackets):
		n = len(brackets)
		if n % 2 != 0:
			return -1
		return '['*(n/2)

	def parse(self, s):

		if s.find('[') == -1:
			if 	s == 'byte' or	\
				s == 'short' or	\
				s == 'int' or	\
				s == 'long' or	\
				s == 'double' or	\
				s == 'boolean' or\
				s == 'char':
				return self._primitive(s)
			else:
				return self._object(s)
		else: # array
			index = s.find('[')
			brackets = s[index : ]
			ret = self._array(brackets)
			if ret < 0:
				print('syntax error!')
				exit(1)
			if 	s.startswith('byte') or		\
				s.startswith('short') or	\
				s.startswith('int') or		\
				s.startswith('long') or		\
				s.startswith('double') or	\
				s.startswith('boolean') or	\
				s.startswith('char'):
				return ret + self._primitive(s[ : index])
			else:
				return ret + self._object(s[ : index])

	def parse_reciver(self):
		return self._object(self.reciver)

	def parse_func(self):
		print('cao: ' + self.func)
		pran1 = self.func.find('(')
		pran2 = self.func.find(')')
		if pran1 == -1 or pran2 == -1:
			print('when convert signature/prototype : syntax error!')
			exit(1)

		func_name = self.func[ : pran1]
		arg_str = self.func[pran1+1 : pran2].strip()
		if arg_str == '':
			return func_name + '()'
		else:
			args = [ arg.strip() for arg in self.func[pran1+1 : pran2].split(',') ]
			parsed_args = [ self.parse(arg) for arg in args ]
			return func_name + '(' + ''.join(parsed_args) + ')'

		
	def convert(self):
		ret_s = self.parse(self.ret)
		# print(ret_s)
		reciver_s = self.parse(self.reciver)
		# print(reciver_s)
		func_s = self.parse_func()
		# print(func_s)

		return reciver_s + '->' + func_s + ret_s;


class Signature(object):

	def __init__(self, sig):
		self.sig = sig
		self.ret_type = None
		self.reciver = None
		self.func_name = None
		self.args = None

		if self.split() < 0:
			print('syntax error!')
			exit(1)

	def split(self):
		first_comma = self.sig.find(';')
		pran1 = self.sig.find('(')
		pran2 = self.sig.rfind(')')

		if self.sig[first_comma+1] == '-' and self.sig[first_comma+2] == '>':
			self.reciver = self.sig[ : first_comma+1]
		else:
			return -1

		if pran1 == -1 or pran2 == -1:
			return -1
		else:
			self.ret_type = self.sig[pran2+1 : ]

		self.func_name = self.sig[first_comma+3 : pran1]

		self.args = self._parse_args(self.sig[pran1+1 : pran2].strip())

		return 1

	def _parse_args(self, s):
		print(s)
		ret = []
		start = 0
		end = 0
		while end < len(s):
			if s[end] in TYPES:
				if s[end] == 'L':
					start = end
					end = s.find(';', start)
					ret.append(s[start : end+1])
				else:
					ret.append(s[start : end+1])
				start = end
			end += 1

		return ret

	def get_signature(self):
		return self.sig

	def get_func_name(self):
		return self.func_name

	def get_ret_type(self):
		return self.ret_type

	def get_reciver(self):
		return self.reciver

	def get_args(self):
		return self.args

	def get_arg_num(self):
		return len(self.args)

	def get_arg(self, index):
		if index >= len(self.args):
			print('out of range')
			exit(1)
		return self.args[index]

if __name__ == '__main__':

	parser = argparse.ArgumentParser(description='converts java prototype to smali form')
	parser.add_argument('--sig', '-s', type=str, default='android.text.Editable android.widget.EditText::getText(int[][], java.lang.String);')
	# Landroid/text/EditText;->getText()Landroid/text/Editable;

	args = parser.parse_args()

	c = Converter(args.sig)
	res = c.convert()
	print(res)

	sig = Signature(res)
	print(sig.get_reciver() + '->' + sig.get_func_name())
	for i in range(0, sig.get_arg_num()):
		print(sig.get_arg(i))
	print(sig.get_ret_type())
