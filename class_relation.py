import os
import argparse
import hashlib
import json
# import finder
from sig_converter import Converter, Signature
from callpoint_analyzer import Config, CallPointAnalyzer

classes = dict()    # store global classes object, {name: class}, contained with child->parent relation in it.

relations = dict()      # {parent:[children], ...}, only store string

class Class(object):

    def __init__(self, m_name, m_modifier, m_parent, m_source):
        self.m_name = m_name
        self.m_modifier = m_modifier
        self.m_parent = m_parent
        self.m_source = m_source
        self.children = []

    def __str__(self):
        return '{ ' + self.m_modifier + ' ' + self.m_name + ' < ' + self.m_parent + ' }'

    def add(self, m_child):
        self.children.append(m_child)

    def get_name(self):
        return self.m_name

    def get_parent(self):
        return self.m_parent


class ClassRelations(object):

    def __init__(self, classes):
        self.classes = classes
        self.relations = dict()
        self.parent2children = dict()

    def extract_relation(self):

        for cls_name in self.classes:

            parent = self.classes[cls_name].get_parent()
            if parent in self.relations.keys():
                self.relations[parent].append(cls_name)
            else:
                self.relations.update({parent: [cls_name]})

    def get_all_descendants(self, cls_name):

        # recursive function
        def BFS(name, res):
            if name not in self.relations.keys():
                return
            current_generation = self.relations[name]
            res.extend(current_generation)
            for item in current_generation:
                BFS(item, res)

        if cls_name not in self.parent2children.keys(): # Check if has been calced out yet.
            result = []
            BFS(cls_name, result)
            self.parent2children.update({ cls_name : result })

        return self.parent2children[cls_name]


    def get_relations(self):
        return self.relations



class ClassSearcher(object):

    CLASS = '.class'
    SUPER = '.super'
    SOURCE = '.source'

    def __init__(self, dir_name):
        self.dir_name = dir_name;
        self.classes = dict()

    def search(self):
        
        for (dirpath, dirnames, filenames) in os.walk(self.dir_name):
            for filename in filenames:
                file = dirpath + '/' + filename
                t_cls = self._extract_relation(file)
                self.classes.update({ t_cls.get_name(): t_cls })


    def get_classes(self):
        if len(self.classes.keys()) == 0:
            self.search()

        return self.classes

    def _extract_relation(self, file):
        with open(file, 'r') as file:
            cls_name, cls_modifier, cls_parent, cls_source = None, None, None, None
            # the first line
            line = file.readline().lstrip()[:-1]
            print(line)
            assert(line.startswith(ClassSearcher.CLASS))
            a = line.split(' ')
            i = 0
            if a[1] == 'public' or a[1] == 'private':
                cls_modifier = a[1]
                i += 1
                if a[2] == 'abstract':
                    cls_modifier += ' abstract'
                    i += 1
                elif a[2] == 'final':
                    cls_modifier += ' final'
                    i += 1
                elif a[2] == 'interface':
                    cls_modifier += ' interface'
                    i += 1
                    if a[3] == 'abstract':
                        cls_modifier += ' abstract'
                        i += 1
            else:
                cls_modifier = 'package'
                if a[1] == 'abstract':
                    cls_modifier += ' abstract'
                    i += 1
            cls_name = a[1+i]
            # the second line
            line = file.readline().lstrip()[:-1]
            assert(line.startswith(ClassSearcher.SUPER))
            a = line.split(' ')
            cls_parent = a[1]

            # the third line, may not exist, if existed, stands for source file
            line = file.readline().lstrip()[:-1]
            if line.startswith(ClassSearcher.SOURCE):
                cls_source = a[1]

            return Class(cls_name,cls_modifier,cls_parent,cls_source)


def main():
    parser = argparse.ArgumentParser(description='Analyze Class Relation')
    parser.add_argument('--dir', '-d', type=str, default='/Users/wangyi/Desktop/scripts/apks/tmp/geoquiz')
    parser.add_argument('--prototype', '-p', type=str, default='android.text.Editable android.widget.EditText::getText();')
    args = parser.parse_args()

    dir_ = args.dir
    prototype = args.prototype

    searcher = ClassSearcher(dir_)
    relationer = ClassRelations(searcher.get_classes())
    relationer.extract_relation()

    relations = relationer.get_relations()

    smali_prototype = Converter(prototype).convert()
    signature = Signature(smali_prototype)
    cls_ = signature.get_reciver()
    descendants = relationer.get_all_descendants(cls_)

    method_ = smali_prototype[smali_prototype.find('->') :]

    # Using CallPointAnalyzer, more efficient
    config = Config()
    config.set_dir(dir_)
    config.enable_descendantable()
    analyzer = CallPointAnalyzer(config, signature, cls_, descendants)
    result = analyzer.analyze()

    for cls_ in result:
        print(cls_)
        print(result[cls_])

    md = hashlib.sha1()
    message = dir_ + prototype + 'true'
    md.update(message.encode('utf-8'))
    with open('../cache/' + md.hexdigest(), 'w+') as json_output:
        json_output.write(json.dumps(result))

    exit(0)

    # Only using Finder
    # call_points = dict()
    # finder_ = finder.Finder(cls_ + method_, dir_)
    # call_points.update({ cls_ : finder_.find() })

    # for descendant in descendants:
    #     print(descendant)
    #     finder_.set_fun_name(descendant + method_)
    #     call_points.update({ descendant : finder_.find() })

    # # print(str(call_points))
    # for cls_ in call_points:
    #     print(cls_)
    #     print(call_points[cls_])

    # exit(0)

if __name__ == '__main__':
    main()
