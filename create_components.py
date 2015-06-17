import os, sys, glob, string, shutil, re
import yaml, json
from collections import OrderedDict



class UnsortableList(list):
    def sort(self, *args, **kwargs):
        pass
    
class UnsortableOrderedDict(OrderedDict):
    def items(self, *args, **kwargs):
        return UnsortableList(OrderedDict.items(self, *args, **kwargs))


class OrderedDictYAMLLoader(yaml.Loader):
    """
    A YAML loader that loads mappings into ordered dictionaries.
    """
 
    def __init__(self, *args, **kwargs):
        yaml.Loader.__init__(self, *args, **kwargs)
 
        self.add_constructor(u'tag:yaml.org,2002:map', type(self).construct_yaml_map)
        self.add_constructor(u'tag:yaml.org,2002:omap', type(self).construct_yaml_map)
 
    def construct_yaml_map(self, node):
        data = OrderedDict()
        yield data
        value = self.construct_mapping(node)
        data.update(value)
 
    def construct_mapping(self, node, deep=False):
        if isinstance(node, yaml.MappingNode):
            self.flatten_mapping(node)
        else:
            raise yaml.constructor.ConstructorError(None, None,
                'expected a mapping node, but found %s' % node.id, node.start_mark)
 
        mapping = OrderedDict()
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            try:
                hash(key)
            except TypeError, exc:
                raise yaml.constructor.ConstructorError('while constructing a mapping',
                    node.start_mark, 'found unacceptable key (%s)' % exc, key_node.start_mark)
            value = self.construct_object(value_node, deep=deep)
            mapping[key] = value
        return mapping



def yaml_to_json(comp_dir):
    
    inFile = comp_dir + '/db/parameters.yaml'
    outFile = comp_dir + '/db/parameters.json'

    with open(inFile) as f:
        yaml_in = yaml.load(f,OrderedDictYAMLLoader)
        json_out = open(outFile,'w')

        json.dump(yaml_in, json_out, indent = 4)

        f.close()
        json_out.close()


def create_cfg_file(comp_dir):

	comp_name = string.split(comp_dir,'/')[-1]
	cfg_name = comp_name.title() + '.cfg.in'
	cfg_file = comp_dir + '/files/' + cfg_name

	# open parameters.json
	p = open(comp_dir + '/db/parameters.json')
	allparams = json.load(p, object_pairs_hook = OrderedDict)

	# header
	head = ['#' + 79*'=', '# Topoflow Config File for: ' + comp_name]

	tablestr = head

	for k in allparams.keys():
	
		header = ['#' + 79*'=', '# ' + str(k)]
	
		params = allparams[k]

		# table
		col1 = [str(obj['key']) for obj in params]
		col2 = [str('{' + obj['key'] + '}') for obj in params]
		col3 = [str(obj['value']['type']) for obj in params]
		col4 = [str(obj['description']) + ' [' + str(obj['value']['units']) + ']' for obj in params]
		col5 = [str(' {' + '; '.join(obj['value']['choices']) + '}') if obj['value'].has_key('choices') else '' for obj in params]

		table = ['{0:20}| {1:20}| {2:10}| {3}{4}'.format(col1[i],col2[i],col3[i],col4[i],col5[i]) for i in range(len(col1))]
		tablestr = tablestr + header + table

	
	tablestr = '\n'.join(tablestr)

	cfgfile_out = open(cfg_file, 'w')
	cfgfile_out.write(tablestr)
	cfgfile_out.close()


def create_files_dot_json(comp_dir):
    
    comp_name = string.split(comp_dir,'/')[-1]
    cfg_name = comp_name.title() + '.cfg.in'

    filesjson_out = open(comp_dir + '/db/files.json','w')
    json.dump([cfg_name], filesjson_out)
    filesjson_out.close()


def create_argv_dot_json(comp_dir):
    
    comp_name = string.split(comp_dir,'/')[-1]
    argv = '["' + comp_name + '"]'
    o = open(comp_dir + '/db/argv.json', 'w')
    o.write(argv)
    o.close()


def create_provides_dot_json(comp_dir, prov):
    # where prov is a list of dictionaries of the connections it provides
    
    o = open(comp_dir + '/db/provides.json', 'w')
    json.dump(prov, o, indent = 2, sort_keys = True)
    o.close()
    

def create_uses_dot_json(comp_dir, uses):
    # where uses is a list of dictionaries of the connections it needs
    
    o = open(comp_dir + '/db/uses.json', 'w')
    json.dump(uses, o, indent = 2, sort_keys = True)
    o.close()


def create_info_dot_json(comp_dir):
    
    comp_name = string.split(comp_dir,'/')[-1]

    # open parameters.json
    p = open(comp_dir + '/db/parameters.json')
    params = json.load(p)
    params = [item for it in params.values() for item in it]

    info = UnsortableOrderedDict()

    info['id'] = comp_name
    info['name'] = [str(i['value']['default']) for i in params if i['key'] == 'ModelName'][0]
    info['class'] = comp_name.title()
    info['initialize_args'] = comp_name.title() + '.cfg'
    try: info['time_step'] = [str(i['value']['default']) for i in params if i['key'] == 'dt'][0]
    except: info['time_step'] = ''
    info['summary'] = ''
    info['url'] = [str(i['value']['default']) for i in params if i['key'] == 'HTML_HELP_FILE'][0]
    info['author'] = [str(i['value']['default']) for i in params if i['key'] == 'ModelAuthor'][0]
    info['email'] = ''
    info['version'] = ''
    info['doi'] = ''
    info['license'] = ''
    
    try:
        extra = read_extra_info()
        if len(extra)>0:
            for k in extra.keys():
                info[k] = extra[k]
    except: pass
    
    o = open(comp_dir + '/db/info.json', 'w')
    json.dump(info, o, indent = 2)
    o.close()



def read_extra_info():

    itemFile = 'info.txt'
    extra_info = UnsortableOrderedDict()

    o = open(itemFile, mode = 'r')    
    for line in o:
        line = re.sub('\n$','',line)
        ln = re.split('\s*[\:\=]\s*', line)

        error_message = 'The file ' + itemFile + ' cannot be read. Please use the format key : value'
        assert len(ln) == 2, error_message

        extra_info[str(ln[0])] = str(ln[1])
        
    o.close()

    return extra_info
    


yaml_root = 'yaml/'
components_root = 'components/'

yaml_dirs = glob.iglob(yaml_root + '*') # xml files

for comp in yaml_dirs:
    
    comp_name = string.split(comp,'/')[-1]
    
    print 'Creating component for ' + comp_name
    
    # make new dirs
    comp_dir = components_root + string.lower(comp_name)
    if not os.path.exists(comp_dir):
        os.makedirs(comp_dir)
        os.makedirs(comp_dir + '/db')
        os.makedirs(comp_dir + '/files')
    
    # copy yaml file to new component dir structure
    shutil.copyfile(comp + '/parameters.yaml', comp_dir + '/db/parameters.yaml')
    
    # make a json parameter file
    yaml_to_json(comp_dir)
    
    # files.json
    create_files_dot_json(comp_dir)
    
    # argv.json -> name of the component
    create_argv_dot_json(comp_dir)
    
    # info.json
    create_info_dot_json(comp_dir)
    
    # provides.json
    provides = [{'id':str(comp_name),'required':False}]
    create_provides_dot_json(comp_dir, provides)
    
    # uses.json
    uses = [{'id':'----','required':False}]
    create_uses_dot_json(comp_dir, uses)
    
    # cfg.in file
    create_cfg_file(comp_dir)



