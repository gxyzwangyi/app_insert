import os
import argparse

class Config(object):

    def __init__(self):
        self.descendantable = False
        self.dir_ = None
        self.prototype = None
        self.invokation_type = None
        self.package = None
        self.sig = None
        self.src_dir = None
        self.classpath = None
        self.out_dir = './smali'
        self.fn = None
        self.cache = './cache'
        self.aspect = None

    def enable_descendantable(self):
        self.descendantable = True

    def is_descendantable(self):
        return self.descendantable

    def set_descendantable(self, a):
        self.descendantable = a

    def get_descendantable(self):
        return self.descendantable

    def set_dir(self, dir_):
        self.dir_ = dir_

    def get_dir(self):
        return self.dir_

    def set_prototype(self, p):
        self.prototype = p

    def get_prototype(self):
        return self.prototype

    def set_package(self, p):
        self.package = p

    def get_package(self):
        return self.package

    def set_invokation_type(self, type):
        self.invokation_type = type

    def get_invokation_type(self):
        return self.invokation_type;

    def set_signature(self, sig):
        self.sig = sig

    def get_signature(self):
        return self.sig

    def set_cache_dir(self, d):
        self.cache = d

    def get_cache_dir(self):
        return self.cache

    def set_src_dir(self, d):
        self.apj_dir = d

    def get_src_dir(self):
        return self.apj_dir

    def set_aspect(self, aspect):
        self.aspect = aspect

    def get_aspect(self):
        return self.aspect

    def set_classpath(self, cp):
        self.classpath = cp

    def get_classpath(self):
        return self.classpath

    def set_out_dir(self, od):
        self.out_dir = od

    def get_out_dir(self):
        return self.out_dir

    def set_func_name(self, n):
        self.fn = n

    def get_func_name(self):
        return self.fn

    def get_src_smali(self):
        filename = self.fn[0].upper() + self.fn[1:]
        return self.out_dir + '/' + filename + '.smali'

    def get_cls_name(self):
        if self.invokation_type != 'new-instance':
            filename = self.fn[0].upper() + self.fn[1:]
            return 'L' + self.package + '/' + filename + ';'
        else:
            filename = 'New' + self.fn[0].upper() + self.fn[1:]
            return 'L' + self.package + '/' + filename + ';'



class CallPointAnalyzer(object):
    INVOKE_VIRTUAL = 'invoke-virtual'

    def __init__(self, config, signature, parent, descendants):
        self.config = config
        self.signature = signature
        self.parent = parent
        self.descendants = descendants

    def analyze(self):
        dirs = []
        dirs.append(self.config.get_dir())
        return self.run(dirs)

    def run(self, dirs):
        res = dict()
        res[self.parent] = dict()
        if self.config.is_descendantable():
            for cls_ in self.descendants:
                res[cls_] = dict()
        for dir in dirs:
            for (dirpath, dirnames, filenames) in os.walk(dir):
                for filename in filenames:
                    file = dirpath + '/' + filename
                    tmp = self._search_current_file(file)
                    for cls_ in tmp:
                        if len(tmp[cls_]) != 0:
                            res[cls_].update( { file : tmp[cls_] })

        return res

    def _within_class_file(self, filename):
        cls_name = filename[filename.rfind('/') + 1 : filename.rfind('.')]
        if cls_name in self.parent:
            return True
        elif self.config.is_descendantable():
            for cls_ in self.descendants:
                if cls_name in cls_:
                    return True
        return False

    def _skip_class_file(self, filename):
        with open(filename, 'r') as infile:
            index = self.signature.get_signature().find('->')
            method_ = self.signature.get_signature()[index+2 :]
            for line in infile.readlines():
                if line.lstrip().startswith('.method') and method_ in line:
                    return True
        return False


    # return { cls_ : { file : [lines...] } }
    def _search_current_file(self, file_name):
        cls_name = file_name[file_name.rfind('/') + 1: file_name.rfind('.')]

        if self._within_class_file(file_name) and self._skip_class_file(file_name):
            return dict()

        with open(file_name, 'r') as file:
            lines = dict()
            lines[self.parent] = []
            if self.config.is_descendantable():
                for cls_ in self.descendants:
                    lines[cls_] = []

            count = 0
            index = self.signature.get_signature().find('->')
            method_ = self.signature.get_signature()[index :]
            if self.config.get_invokation_type() == 'new-instance':
                method_ = self.signature.get_ret_type()

            invokation_type = self.config.get_invokation_type()
            for line in file.readlines():
                count += 1
                # if line.lstrip().startswith(CallPointAnalyzer.INVOKE_VIRTUAL) and method_ in line:
                if line.lstrip().startswith(invokation_type) and method_ in line:
                    if invokation_type != 'new-instance':
                        if (self.parent + method_) in line:
                            lines[self.parent].append(count)
                        elif self.config.is_descendantable():
                            for cls_ in self.descendants:
                                if (cls_ + method_) in line:
                                    lines[cls_].append(count)
                                    break
                    else:
                        lines[method_].append(count)    # constructor

            return lines


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--fun', '-f', type=str)
    parser.add_argument('--dir', '-d', type=str)

    args = parser.parse_args()

    fun_name, dir_name = args.fun, args.dir

    finder = Finder(fun_name, dir_name)

    res = finder.find()

    for key in res:
        if len(res[key]) != 0:
            print(key)
            print(res[key])


if __name__ == '__main__':
    main()
    