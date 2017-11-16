import os
import argparse
import subprocess
import re

base_dir = os.getcwd()
# apks_dir = 'D:\\files\\android\decompilers\\apks\\00\\small\\'
# key_file_dir = 'D:\\files\\android\decompilers\\apks\\'
# output_dir = 'D:\\files\\android\\decompilers\\apks\\a-output\\'
# tmp_dir = 'D:\\files\\android\\decompilers\\apks\\tmp\\'
# apktool = 'D:\\files\\android\\decompilers\\apktool.jar'
apks_dir=base_dir+'/apks/'
key_file_dir=base_dir+'/apks/key/'
output_dir=base_dir+'/apks/output/'
tmp_dir=base_dir+'/apks/tmp/'
apktool=base_dir+'/apktool.jar'

collections = []


#没用到
def run_for_output(cmd):
	env = os.environ
	return subprocess.check_output(cmd, env=env, shell=True)


# 跑命令行的命令
def run(cmd, **keywords):
	env = os.environ

	proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, env=env)	# return CompletedProcess object.
	
	outs, errs = proc.communicate(keywords.get('stdin'))

	proc.wait()

	# print(proc.returncode)
	# # stdout pipe to CompletedProcess object
	# output = proc.stdout.decode('utf-8')	# stdout default to binary stream, decode it to string.
	# lines = output.split('\n')
	# for item in lines:
	# 	print(item)

	return outs

# 解包再重新装
def process(apk, pack_name, launchable_activity):
	
	run(['java', '-jar', apktool, 'd', '-r', apks_dir+apk, '-f', '-o', tmp_dir+apk[:-4]])
	run(['java', '-jar', apktool, 'b', tmp_dir+apk[:-4], '-f', '-o', output_dir+apk])
	run(['jarsigner', '-verbose', '-sigalg', 'SHA1withRSA', '-digestalg', 'SHA1',
		'-keystore', key_file_dir+'wangyi.keystore', output_dir+apk, 'andriod'], stdin=b'123456\n')

	res = run(['adb', 'install', '-r', output_dir+apk])
	if res.rfind(b'Success') or res.rfind(b'success'):
		print("Installed successfully")
		run(['adb', 'shell', 'am', 'start', '-n', pack_name + '/' + launchable_activity])

		res = run(['adb', 'shell', 'ps'])

		if res.find(bytes(pack_name, 'UTF-8')):	# or pack_name.encode('UTF-8')
			print("Running")
			run(['adb', 'shell', 'am', 'force-stop', pack_name])
			run(['adb', 'uninstall', pack_name])
			collections.append(apk)
		else:
			print("Failed to start this app: " + pack_name)
	else:
		print("Install failed")


# 获取包名和activity
def collect_info(apks):
	info = {}
	for apk in apks:
		res = run(['aapt', 'dump', 'badging', apks_dir+apk])

		if res != None:

			res = res.decode('UTF-8')
			c = re.search(r'native-code: \'(.*?)\'', res)
			if c != None: continue	# contain native code, skip it.

			a = re.search(r'package: name=\'(.*?)\'', res)
			b = re.search(r'launchable-activity: name=\'(.*?)\'', res)
			#print(a.group()[15:-1])
			
			pack_name = a.group() if a != None else None
			launchable_activity = b.group() if b != None else None
			if pack_name != None and launchable_activity != None:
				info[apk] = [pack_name[15:-1], launchable_activity[27:-1]]

	return info



#获取全部的apk跑一遍
def main():
	apks = [f for f in os.listdir(apks_dir) if f.endswith('.apk')
				and os.path.isfile(os.path.join(apks_dir, f))]
	print(apks)
	info = collect_info(apks)


	print(info)

	# for key in info:
	# 	print('APK: ' + key + ': ')
	# 	print('package name: ' + info[key][0])
	# 	print('launchable activity: ' + info[key][1])

	progress = 0
	for apk in info:
		progress += 1
		print(apk)
		process(apk, info[apk][0], info[apk][1])

def test():
    pass

class Foo(object):
    pass

if __name__ == '__main__':
	
	parser = argparse.ArgumentParser(description='Decompiling and recompiling...')
	parser.add_argument('-i', '--input', type=str, default=apks_dir)	# default as str
	parser.add_argument('-k', '--key', type=str, default=key_file_dir)
	parser.add_argument('-o', '--output', type=str, default=output_dir)
	args = parser.parse_args()
	args = vars(args)	# convert it to dict, or directly access to args through dot (.) operator
	apks_dir, key_file_dir, output_dir = args['input'], args['key'], args['output']
		
	main()
