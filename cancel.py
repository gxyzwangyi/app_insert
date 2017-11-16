import os
from callpoint_analyzer import Config

def undo(result, config):
	for cls_name in result:
		for filename in result[cls_name]:
			line_numbers = result[cls_name][filename]
			for i in range(len(line_numbers)):
				line_numbers[i] += i
			with open(filename, 'r') as infile, open(filename+'.tmp', 'w') as outfile:
				c, i = 1, 0
				skip_next_line, is_finished = False, False
				for line in infile.readlines():
					if (not is_finished) and c == line_numbers[i]:
						
						# print(str(c) + ': ' + line)
						if line.lstrip()[0] == '#':
							outfile.write('\t' + line.lstrip()[1:].lstrip())
							skip_next_line = True
						else:
							print('error')
							exit(1)
						i += 1
						if i == len(line_numbers): is_finished = True
					elif skip_next_line != True:
						outfile.write(line)
					else:
						skip_next_line = False

					c += 1

			os.remove(filename)
			os.rename(filename+'.tmp', filename)

