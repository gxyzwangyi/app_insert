import os
import sys
import argparse
import zipfile
import subprocess

SHA1_LENGTH = 65
SHA256_LENGTH = 103
base_dir = os.getcwd()

def run(cmd, **keywords):
	env = os.environ
	proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, env=env)
	outs, errs = proc.communicate(keywords.get('stdin'))
	proc.wait()
	return outs

def get_signature_from_apk(apk):
	if os.path.exists('./java/Main.class') and os.path.isfile('./java/Main.class'):
		os.chdir('./java/')
		return run(['java', 'Main', apk])
	else:
		if not os.path.exists('./java/'):
			os.mkdir('./java/')
		run(['javac', 'Main.java', '-d', './java/'])
		os.chdir('./java/')
		return run(['java', 'Main', apk])

def unzip(from_, to_):
	zip_ = zipfile.ZipFile(from_, 'r')
	zip_.extractall(to_)
	zip_.close()

def extract_signature(meta_inf):
	path_to_meta_inf = meta_inf
	file = None
	for (_, _, filenames) in os.walk(meta_inf):
		for filename in filenames:
			if filename.endswith('.RSA'):
				file = filename
	file = path_to_meta_inf + file
	outs = run(['keytool', '-printcert', '-file', file])
	if outs.find(b'SHA1withRSA') != -1:
		sha1_index = outs.find(b'SHA1: ')
		sha1 = outs[sha1_index + 6 : sha1_index + SHA1_LENGTH]
		hexs = sha1.decode('utf-8').split(':')
	elif outs.find(b'SHA256withRSA') != -1:
		sha256_index = outs.find(b'SHA256: ')
		sha256 = outs[sha256_index + 8 : sha256_index + SHA256_LENGTH]
		hexs = sha256.decode('utf-8').split(':')

	return hexs

def get_dexs(root_path):
	res = []
	for (_, _, filenames) in os.walk(root_path):
		for filename in filenames:
			if filename.endswith('.dex'):
				res.append(root_path + filename)
	return res

def search_signature(path_to_dexs, hexs):
	str_form = bytes(''.join(hexs).encode('utf-8'))
	print(str_form)
	hex_decimal = bytes.fromhex(''.join(hexs))
	print(hex_decimal)
	for dex in path_to_dexs:
		with open(dex, 'rb') as file:
			file_content = file.read()
			if file_content.find(str_form) != -1:
				print(dex)
				return True
			if file_content.find(str_form[::-1]) != -1:
				print(hex)
				return True

			if file_content.find(hex_decimal) != -1:
				print(hex)
				return True
			if file_content.find(hex_decimal[::-1]) != -1:
				print(hex)
				return True

def search(apk, str_form):
	print(str_form)
	hex_decimal = bytes.fromhex(str_form.decode('utf-8'))
	print(hex_decimal)
	
	with open(apk, 'rb') as file:
		file_content = file.read()
		index = file_content.find(str_form)
		if index != -1:
			print('bytes form')
			print(index)
			return True
		index = file_content.find(str_form[::-1])
		if index != -1:
			print('bytes form[::-1]')
			print(index)
			return True
		index = file_content.find(hex_decimal)
		if index != -1:
			print('hex decimal form')
			print(index)
			return True
		index = file_content.find(hex_decimal[::-1])
		if index != -1:
			print('hex decimal form[::-1]')
			print(index)
			return True


def main():
	parser = argparse.ArgumentParser('APK Signature seacher')
	parser.add_argument('--apk', '-a', type=str, default=base_dir+'/apk/app-debug.apk')
	# parser.add_argument('--out', '-o', type=str, default='../dex/app-debug/')

	args = parser.parse_args()
	# unzip(args.path, args.out)

	# path_to_meta_inf = args.out + 'META-INF/'
	hexs = get_signature_from_apk(args.apk)
	hexs = hexs[hexs.find(b'To char: ') + 9 : ].strip()
	print(hexs)
	# path_to_dexs = get_dexs(args.out)
	# print(path_to_dexs)

	if search(args.apk, hexs):
		print('Found')
	else:
		print('Not Found')


if __name__ == '__main__':
	main()
