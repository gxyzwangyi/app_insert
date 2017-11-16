import os
import argparse


class Finder(object):

    def __init__(self, fun_name, dir_name):
        self.fun_name = fun_name
        self.dir_name = dir_name

    def set_fun_name(self, fn):
        self.fun_name = fn

    def set_dir_name(self, dn):
        self.dir_name = dn

    def find(self):
        dirs = []
        dirs.append(self.dir_name)
        return self.run(dirs)

    def run(self, dirs):
        res = {}
        for dir in dirs:
            for (dirpath, dirnames, filenames) in os.walk(dir):
                for filename in filenames:
                    file = dirpath + '/' + filename
                    lines = self._search_current_file(file)
                    # print(file)
                    if len(lines) != 0 : res[file] = lines
                # print(dirpath)

        return res

    # return list, [line, ...]
    def _search_current_file(self, file_name):
        with open(file_name, 'r') as file:
            lines = []
            count = 0;
            for line in file.readlines():
                count += 1
                if self.fun_name in line:
                    lines.append(count)

            return lines


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--fun', '-f', type=str)
    parser.add_argument('--dir', '-d', type=str)

    args = parser.parse_args()

    fun_name, dir_name = args.fun, args.dir

    finder = Finder(fun_name, dir_name)

    res = finder.find()

    for key in res:
        if len(res[key]) != 0:
            # i = key.rfind('\\')
            # filename = key[i+1:]
            print(key)#+ ': ' + '[' + ', '.join(res[key]) + ']')
            print(res[key])