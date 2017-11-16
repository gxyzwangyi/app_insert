# -*- coding: utf-8 -*-  

import os
import argparse
import hashlib
import json
from class_relation import ClassSearcher, ClassRelations
from sig_converter import Converter, Signature
from callpoint_analyzer import Config, CallPointAnalyzer
from generate_instrument_smali import generate_smali
from rewrite import write_instrument_file, rewrite, rewrite_ctor
from cancel import undo


base_dir = os.getcwd()


# 校验policy文件
def get_type(line):
	if line[-2] == '-' and line[-1] == '}':
		return line[2:-2].strip()
	else:
		print('policy file syntax error')
		exit(1)


# 从policy获取具体的配置文件信息并且对其进行解析，生成config类
def get_config(policy):
	config = Config()
	lines = []
	with open(policy, 'r') as pfile:
		for line in pfile.readlines():
			lines.append(line.strip())
	
	i = 0
	type_ = None
	while i < len(lines):
		if lines[i].startswith('{-'):
			type_ = get_type(lines[i])
		c = i + 1
		while c < len(lines) and not lines[c].startswith('{-'):
			if type_ == 'relations':
				if lines[c].startswith('dir:'):
					config.set_dir(lines[c][4:].strip())
				elif lines[c].startswith('prototype:'):
					config.set_prototype(lines[c][10:].strip())
				elif lines[c].startswith('descendantable:'):
					if lines[c][15:].strip() == 'true':
						config.set_descendantable(True)
					else:
						config.set_descendantable(False)
				elif lines[c].startswith('package'):
					package = lines[c][8:].strip()
					if package.find('.') != -1:
						package = package.replace('.', '/')
					config.set_package(package)
				elif lines[c].startswith('type:'):
					if lines[c].strip().endswith('instance'):
						config.set_invokation_type('invoke-virtual')
					elif lines[c].strip().endswith('static'):
						config.set_invokation_type('invoke-static')
					elif lines[c].strip().endswith('constructor'):
						config.set_invokation_type('new-instance')
					else:
						print('invoke type: ' + lines[c] + ' have not been supported yet')
						exit(1)
				else:
					pass
			elif type_ == 'generate':
				if lines[c].startswith('aspect:'):
					config.set_aspect(lines[c][7:].strip())
				elif lines[c].startswith('aspect_dir:'):
					config.set_src_dir(lines[c][11:].strip())
				elif lines[c].startswith('classpath:'):
					config.set_classpath(lines[c][10:].strip())
				else:
					pass
			else:
				pass

			c += 1

		i = c

	return config


def debug(config):
	print(config.get_dir())
	print(config.get_prototype())
	print(config.get_descendantable())
	print(config.get_package())
	print(config.get_src_dir())
	print(config.get_classpath())
	print(config.get_out_dir())
	# exit(1)

#计算函数的hash
def calchash(config):
	md = hashlib.sha1()
	flag = None
	if config.get_descendantable() == True:
		flag = 'true'
	else:
		flag = 'false'
	message = config.get_dir() + config.get_prototype() + flag
	md.update(message.encode('utf-8'))

	return md


#写入cache
def write2cache(result, fn):
	config = Config()
	# filename = calchash(config).hexdigest()

	if not os.path.exists('./cache'):
		os.makedirs('./cache')
	with open('./cache/' + fn, 'w+') as json_output:
		json_output.write(json.dumps(result))


def read_cache(config):
	filename = config.get_cache_dir() + '/' + calchash(config).hexdigest()
	if os.path.exists(filename):
		with open(filename) as data_file:
			try:
				data = json.load(data_file)
			except Exception as e:
				raise e
		return data
	return False


def set_signature2config(config):
	#if config.get_invokation_type() != 'new-instance':
	smali_prototype = Converter(config.get_prototype()).convert()
	signature = Signature(smali_prototype)
	method_ = smali_prototype[smali_prototype.find('->') :]
	method_name = method_[2 : method_.find('(')].strip()
	config.set_func_name(method_name)
	config.set_signature(signature)
	#else:
	#	print('ctor prototype: ' + config.get_prototype())
	#	config.set_func_name(config.get_prototype())





def analyze(config):

	debug(config)
	set_signature2config(config)
	signature = config.get_signature()
	method_name = config.get_func_name()

	filename = calchash(config).hexdigest()
	data = read_cache(config)
	if data != False:
		return data, method_name
	
	searcher = ClassSearcher(config.get_dir())
	relationer = ClassRelations(searcher.get_classes())
	relationer.extract_relation()

	relations = relationer.get_relations()

	
	cls_ = signature.get_reciver()
	descendants = relationer.get_all_descendants(cls_)

	analyzer = CallPointAnalyzer(config, signature, cls_, descendants)
	result = analyzer.analyze()
	write2cache(result, filename)

	return (result, method_name)


def extract_invoke_statement(config):
	cls_name = config.get_cls_name()
	func_name = config.get_func_name()
	reciver = config.get_signature().get_reciver()
	args = config.get_signature().get_args()
	ret_type = config.get_signature().get_ret_type()
	print('extract invoke statement')
	print(cls_name)
	print(func_name)
	print(reciver)
	print(args)
	print(ret_type)

	# TODO add invoke type to constants pool
	if config.get_invokation_type() == 'invoke-virtual':
		print('i.')
		invoke_statement = cls_name + '->' + func_name + '(' + reciver + ''.join(args) + ')' + ret_type
	elif config.get_invokation_type() == 'invoke-static':
		invoke_statement = cls_name + '->' + func_name + '(' + ''.join(args) + ')' + ret_type 
		print('s.')
	elif config.get_invokation_type() == 'new-instance':
		invoke_statement = cls_name + '->' + func_name + '(' + ''.join(args) + ')' + ret_type
		print('c.')
	else:
		invoke_statement = None
		print('u.')

	print('invoke statement: ' + invoke_statement)

	return invoke_statement



def get_rewrite_point(result):
	for cls_name in result:
		for path in result[cls_name]:
			return path[ : path.rfind('/')]


# 插入过程
def weavein(result, config):
	# print(config.get_func_name())
	for cls_name in result:
		print(cls_name)

	rewrite_point = get_rewrite_point(result)

	src = config.get_src_smali()
	if config.get_invokation_type() == 'new-instance':
		# src = src.replace('\\', '/')
		last_slash = src.rfind('/')
		src = src[ : last_slash+1] + 'New' + src[last_slash+1 : ]

	rewrite_dir = config.get_dir()
	print(rewrite_dir)
	smali = '/smali/'
	smali_index = rewrite_dir.find(smali) 
	smali_len = len(smali)
	root_dir = rewrite_dir[ : smali_index]
	#dest_dir = root_dir + smali + config.get_package().replace('/', '\\')
	dest_dir = root_dir + smali + config.get_package()
	print(dest_dir)
	if not os.path.exists(dest_dir):
		os.mkdir(dest_dir)


	func_name = config.get_func_name()
	rewrite_point = dest_dir
	if config.get_invokation_type() != 'new-instance':
		rewrite_point += '/' + func_name[0].upper() + func_name[1:] + '.smali'
	else:
		rewrite_point += '/' + 'New' + func_name[0].upper() + func_name[1:] + '.smali'
	if os.path.exists(rewrite_point):
		print('Have been rewriten')
		return
		
	cls_name = config.get_cls_name()
	# print('rewrite point: ' + rewrite_point)
	# print('class name: ' + cls_name)
	# print('src: ' + src)
	write_instrument_file(src, rewrite_point, cls_name)

	invoke_statement = extract_invoke_statement(config)
	print(invoke_statement)

	print('------------------------------')
	if config.get_invokation_type() != 'new-instance':
		for descendant in result:
			for filename in result[descendant].keys():
				rewrite(filename, result[descendant][filename], invoke_statement)
	else:
		for descendant in result:
			for filename in result[descendant].keys():
				rewrite_ctor(filename, result[descendant][filename], invoke_statement)
	

# TODO 还原用的
def uninvoke():
	parser = argparse.ArgumentParser(description='Read policy file')
	parser.add_argument('--policy', '-p', type=str, default=base_dir+'/policy')
	config = get_config(parser.parse_args().policy)
	set_signature2config(config)
	debug(config)
	result = read_cache(config)

	if result == False:
		print('Cache was deleted')
		# TODO: redo analyze
		exit(1)

	rewrite_point = get_rewrite_point(result)
	func_name = config.get_func_name()
	rewrite_point += '/' + func_name[0].upper() + func_name[1:] + '.smali'
	print(rewrite_point)
	if not os.path.exists(rewrite_point):
		print('Have not do rewriting yet')
		exit(1)
	os.remove(rewrite_point)

	undo(result, config)


def main():
	parser = argparse.ArgumentParser(description='Read policy file')
	parser.add_argument('--policy', '-p', type=str, default=base_dir+'/policy')

	config = get_config(parser.parse_args().policy)
	(result, method_name) = analyze(config)
	print('call point: ')
	print(result)
	smali = generate_smali(config.get_src_dir(), config.get_classpath(), config.get_out_dir())

	# TODO: relation bewteen config and generated smali file
	if config.get_invokation_type() == 'new-instance':
		method_name = 'new' + method_name
	if method_name not in smali:
		print('Cant find smali method')
		print(smali)
		exit(1)

	weavein(result, config)

if __name__ == '__main__':
	main()
	# uninvoke()