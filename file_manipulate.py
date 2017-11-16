import os
import argparse

STARTS = '\tinvoke-static {'
CLASS = '.class'
POSTFIX = '.smali'

def get_to_path(d):
	for key in d.keys():
		return key

def write_instrument_file(from_, to_, cls_name):
	
	with open(from_, 'r') as infile, open(to_, 'w') as outfile:

		is_first_line = True

		for line in infile.readlines():

			if is_first_line:
				outfile.write('# ' + line)
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
				if line.lstrip()[0] == '#':
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

def main(cls_name, map_):

	for filename in map_.keys():

		rewrite(filename, map_[filename], 'Lpath/to/CheckUtil;->getText2()Landroid/text/Editable;')


if __name__ == '__main__':

	parser = argparse.ArgumentParser(description='Rewrite system')
	parser.add_argument('--dir', '-d', type=str, default='/Users/wangyi/Desktop/scripts/')
	parser.add_argument('--file', '-f', type=str, default='CheckUtil.smali')

	args = parser.parse_args()

	path, filename = args.dir, args.file
	assert(filename.endswith(POSTFIX))

	call_points = {'/Users/wangyi/Desktop/scripts/apks/tmp/geoquiz/': [432, 504, 1296, 1361]}

	default_path = get_to_path(call_points)
	default_path = default_path[:default_path.rfind('/')]
	cls_name = 'Lcom/liao/group/CreateGroupActivity;'
	package_name = cls_name[:cls_name.rfind('/')]

	write_instrument_file(path + '/' + filename, default_path + '/' + filename, package_name + '/' + filename[:-6] + ';')

	main('Landroid/widget/EditText;', call_points)