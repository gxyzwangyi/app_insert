import finder
import class_relation

import os
import re
import argparse

INSTRUMENT_CLASS = ''

STARTS = '\tinvoke-static {'
CLASS = '.class'
POSTFIX = '.smali'

def get_to_path(d):
	for key in d.keys():
		return key

def get_package_name(file):

	with open(file, 'r') as infile:

		line = infile.readline()
		assert(line.lstrip().startswith(CLASS))

		return line[line.find('L') : line.rfind('/')]


def write_instrument_file(from_, to_, cls_name):
	
	with open(from_, 'r') as infile, open(to_, 'w') as outfile:

		is_first_line = True

		for line in infile.readlines():

			if is_first_line:
				# outfile.write('# ' + line)
				assert(line.strip().startswith(CLASS))
				outfile.write(line[:line.find('L')] + cls_name + '\n')
				is_first_line = False
			else:
				outfile.write(line)


def rewrite(filename, map_, to_):

	with open(filename, 'r') as infile, open(filename+'.tmp', 'w') as outfile:
		count = 1
		i = 0
		is_finished = False

		for line in infile.readlines():

			if (not is_finished) and count == map_[i]:
				# already rewrited
				if line.strip() != '' and line.lstrip()[0] == '#':
					outfile.close()
					os.remove(filename + '.tmp')
					return

				outfile.write('\t# ' + line.lstrip())
				para_name = line[line.find('{')+1 : line.rfind('}')]
				outfile.write(STARTS+para_name+'}, ' + to_ + '\n')
				i += 1
				if i == len(map_): is_finished = True
			else:
				outfile.write(line)

			count += 1

	os.remove(filename)
	os.rename(filename+'.tmp', filename)


def rewrite_ctor(filename, map_, to_):
	print('wori: ' + to_)
	class_name = to_[to_.rfind(')')+1 : ].strip()
	with open(filename, 'r') as infile, open(filename+'.tmp', 'w') as outfile:
		count = 1
		i = 0
		is_finished = False
		target_lines = []
		wight_line = 0

		for line in infile.readlines():
			if (not is_finished) and count == map_[i]:
				line = line.strip()
				# already rewrited
				if line != '' and line[0] == '#':
					outfile.close()
					os.remove(filename + '.tmp')
					return

				# new-instance ...
				# ...
				# invoke-direct ...
				if line != '':
					target_lines.append(line)
					if map_[i] == 2596:
						print('fucked: ' + line)
						print('count: ' + str(count))
				else:
					wight_line += 1

				if not (line.startswith('invoke-direct') and ((class_name + '->' + '<init>') in line)):
					count -= 1
				else:
					print('number of statements: ' + str(len(target_lines)) + ' ' + str(map_[i]))
					new_statement = target_lines[0]
					invoke_statement = target_lines[-1]
					print(filename + ': ' + str(count) +'\n\t' + new_statement + '\n\t' + invoke_statement)
					assert new_statement.startswith('new-instance')
					assert invoke_statement.startswith('invoke-direct')
					outfile.write('\t# ' + new_statement + '\n')
					outfile.write('\t# ' + invoke_statement + '\n')

					for x in range(1, len(target_lines)-1):
						outfile.write('\t' + target_lines[x] + '\n')

					obj_register = new_statement[new_statement.find(' ')+1 : new_statement.find(',')]
					print('to register: ' + obj_register)

					para_name = invoke_statement[invoke_statement.find(',')+1 : invoke_statement.find('}')].strip()
					outfile.write(STARTS+para_name+'}, ' + to_ + '\n')
					outfile.write('\tmove-result-object ' + obj_register + '\n')
					i += 1
					if i == len(map_): is_finished = True
					count += len(target_lines) + wight_line - 1
					target_lines = []
			else:
				outfile.write(line)

			count += 1

	os.remove(filename)
	os.rename(filename+'.tmp', filename)



def main(cls_name, map_):

	for filename in map_.keys():
		print('Rewriting file: ' + filename)
		rewrite(filename, map_[filename], cls_name + '->getText2(Landroid/widget/EditText;)Landroid/text/Editable;')


if __name__ == '__main__':
	
	parser = argparse.ArgumentParser(description='Rewrite system')

	parser.add_argument('--recv', '-r', type=str, default='Landroid/widget/EditText;')
	parser.add_argument('--fun', '-f', type=str, default='->getText()Landroid/text/Editable;')
	parser.add_argument('--dir', '-d', type=str, default='/Users/wangyi/Desktop/scripts/apks/tmp/geoquiz')
	parser.add_argument('--input', '-i', type=str, default='/Users/wangyi/Desktop/scripts/smali/CheckUtil.smali')

	args = parser.parse_args()
	reciver_cls, func, dir_name, in_file = args.recv, args.fun, args.dir, args.input

	searcher = class_relation.ClassSearcher(dir_name)
	searcher.search()
	class_relation.extract_relations(class_relation.classes)
	descendants = class_relation.get_all_descendants(reciver_cls)


	my_finder = finder.Finder(reciver_cls+func, dir_name)
	call_points = dict()
	call_points.update({ reciver_cls+func : my_finder.find() })

	for descendant in descendants:
		my_finder.set_fun_name(descendant+func)
		call_points.update({ descendant : my_finder.find() })


	tmp_file = get_to_path(call_points[descendant])
	to_dir = tmp_file[: tmp_file.rfind('/')+1]
	instrument_file_name = in_file[in_file.rfind('/')+1 :]
	assert(instrument_file_name.endswith(POSTFIX))
	package_name = get_package_name(tmp_file)
	instrument_class_name = instrument_file_name[: instrument_file_name.rfind('.')]
	INSTRUMENT_CLASS = package_name + '/' + instrument_class_name + ';'
	write_instrument_file(in_file, to_dir+instrument_file_name, INSTRUMENT_CLASS)


	print('------------------------------')
	for cls_name in call_points:
		print(cls_name)
		print(call_points[cls_name])
		main(INSTRUMENT_CLASS, call_points[cls_name])


