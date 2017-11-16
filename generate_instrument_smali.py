import subprocess
import os
import re
import sys
import argparse
from apj2j import AspectJ

''' commands
- javac -source 1.7 -target 1.7 -cp /path/to/android.jar Src.java
- dx --dex --output=classes.dex Src.class
- java -jar baksmali.jar d classes.dex
'''

import os

cwd = os.getcwd()  # Get the current working directory (cwd)
# files = os.listdir(cwd)  # Get all the files in that directory
scriptpath = os.path.dirname(__file__)
dx = os.path.join(scriptpath, 'dx.jar')
#print("this in '%s' "% (dx))



baksmali = '/Users/wangyi/Desktop/scripts/baksmali.jar'
# dx = '/Users/wangyi/Desktop/scripts/dx.jar'


def run(cmd, **keywords):
	cmd = ' '.join(cmd)

	env = os.environ

	proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, env=env, shell=True)	# return CompletedProcess object.
	
	outs, errs = proc.communicate(keywords.get('stdin'))

	proc.wait()

	return outs


def generate_smali(java_src_dir, class_path, out_dir):
	smalis = []
	for (dirpath, dirnames, filenames) in os.walk(java_src_dir):
		c = 0
		for filename in filenames:
			apj = AspectJ(java_src_dir+'/'+filename)
			apj.read_file_content()
			apj.parse()
			filename = apj.get_filename()
			filename = filename[0].upper() + filename[1:]
			apj.wirte_to_java(filename)
			java = './' + filename + '.java'
			class_ = './' + filename + '.class'
			smalis.append(apj.get_filename())
			main(java, class_path, out_dir)
			#os.remove(java)
			os.remove(class_)
			os.remove('classes.dex')
			c += 1
		return smalis


def main(java_src, class_path, out_dir):
	class_file_name = java_src[ : java_src.rfind('.')] + '.class'
	res = None
	try:
		res = run(['javac', '-source', '1.7', '-target', '1.7', '-cp', class_path, java_src])
		# res = run(['ls', dx])
		# print(res)
		res += run(['java', '-jar',  dx, '--dex', '--output=classes.dex', '--no-strict', class_file_name])
		res += run(['java', '-jar', baksmali, 'd', 'classes.dex', '-o', out_dir])
	except Exception as e:
		print('Exception')
		raise e


if __name__ == '__main__':

	parser = argparse.ArgumentParser("Generating the instrument smali file")
	parser.add_argument('--java', '-j', type=str, default='/Users/wangyi/Desktop/scripts/GetText.java')
	parser.add_argument('--classpath', '-cp', type=str, default='/Users/wangyi/Desktop/scripts/android.jar')
	parser.add_argument('--output', '-o', type=str, default='/Users/wangyi/Desktop/scripts/smali')

	args = parser.parse_args()

	java_src_code, classpath, output_dir = args.java, args.classpath, args.output

	try:
		main(java_src_code, classpath, output_dir)
	except Exception as e:
		pass