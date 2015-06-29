"""
Auxiliary functions for xml_to_yaml_converter.py

isAllWhiteSpace checks to see if there is really text
covertXml2Yaml creates a dirty dictionary of the yaml file
create_yaml_file modifies the dirty dictionary to fit the format of TopoFlow parameter files

perignon@colorado.edu
June 8, 2015
"""

import yaml
import string, re
from xml.dom import minidom
from xml.dom import Node
import numpy as np
from collections import OrderedDict

class UnsortableList(list):
    def sort(self, *args, **kwargs):
        pass
    
class UnsortableOrderedDict(OrderedDict):
    def items(self, *args, **kwargs):
        return UnsortableList(OrderedDict.items(self, *args, **kwargs))
    
yaml.add_representer(UnsortableOrderedDict, yaml.representer.SafeRepresenter.represent_dict)


NonWhiteSpacePattern = re.compile('\S')
def isAllWhiteSpace(text):
    if NonWhiteSpacePattern.search(text):
        return 0
    return 1


def convertXml2Yaml(obj, objL):
    objDict = {}
    
    attrs = obj.attributes
    if attrs.length > 0:
        attrDict = {}
        for idx in range(attrs.length):
            attr = attrs.item(idx)
            attrDict[attr.name] = attr.value
        objL.append(attrDict)
        
    text = []
    for child in obj.childNodes:
        if child.nodeType == Node.TEXT_NODE and not isAllWhiteSpace(child.nodeValue):
            text.append(child.nodeValue)
    if text:
        textStr = "".join(text)
        objDict[obj.nodeName] = textStr
        
    children = []
    for child in obj.childNodes:
        if child.nodeType == Node.ELEMENT_NODE:
            obj, ls = convertXml2Yaml(child, objL)
            if obj:
                children.append(obj)
    if children:
        objL.append(children)
        
    return objDict, objL



def expand_list(obj):
    obj[0] = [obj[0]]
    ext_obj = []
    extend = ext_obj.extend
    for l in obj: extend(l)
    vals = dict([(str(item.keys()[0]),str(item.values()[0])) for item in ext_obj])
    
    return vals


def check_for_units(obj):
    ''' checks for units and multiple-choice options in the description'''

    ## units
    units_regx = "\[.*\]"
    units_s = re.search(units_regx, obj)
    
    
    if units_s:
        # clean up units
        units = (units_s.group())[1:-1]
        
        cite = re.search('\D\s\d',units)
        met = re.search('.*\[.*',units)
              
        if cite: # Could it be a citation?
        
        	print 'Found something funny:', units_s.group(), 'Check units!'
        	obj = obj.replace(units_s.group(),'(' + units + ')')
        	units = None
        
        elif met: # weird meteorology format
        	
        	met = re.search('\[.*',units)
        	units = (met.group())[1:]
        	obj = obj.replace(units_s.group(),'')
        	
        else:
        
        	units = re.sub('\s+', '', units).strip()
        	obj = obj.replace(units_s.group(),'')
            
        if units == 'none':
            units = None
    else:
        units = None
    
    ## boolean / multiple choices
    bool_regx = "\{.*\}"
    bool_s = re.search(bool_regx, obj)
    
    if bool_s:
        # clean up units
        bools = (bool_s.group())[1:-1]
        bools = string.split(bools,'; ')
        obj = obj.replace(bool_s.group(),'')
    else:
        bools = None
        
    obj = re.sub('\s+', ' ', obj).strip()
    
    return obj, units, bools
    

def create_yaml_file(inFileName):

    doc = minidom.parse(inFileName)
    root = doc.childNodes[0]
    [objD, objL] = convertXml2Yaml(root,[])

    # remove the structures that are too broad and leave only the ones that relate specifically to parameters

    flags = np.diff([len(item) for item in objL] + [1]) # the zeros are the bad entries
    objList = [objL[i] for i,j in enumerate(flags) if j != 0]

    # turn all lists in the list to individual dictionaries, clean the formatting

    ind_dict = [i for i,j in enumerate(objList) if type(j) is dict] + [len(objList) + 1]

    allParams = []
    for i,ind_list in enumerate(ind_dict[:-1]):
        obj = objList[ind_list:ind_dict[i+1]]

        objDict = expand_list(obj)

        param = UnsortableOrderedDict()
        vals = UnsortableOrderedDict()
        range_vals = UnsortableOrderedDict()

        try: param['key'] = string.rsplit(objDict.pop('name'),'/')[-1]
        except: pass
        try: param['name'] = string.rsplit(objDict.pop('label'),':')[0]
        except: pass
        try:
            [objDict['help_brief'], units, bools] = check_for_units(objDict['help_brief'])
            param['description'] = string.capitalize(objDict.pop('help_brief'))
            
            if units and not objDict.has_key('units'):
                objDict['units'] = units
            elif units and objDict.has_key('units'):
                print param['key'], 'has two sets of units:', units, objDict['units']
                print 'Not replacing the units. Check by hand.'
            else: pass
            
            if bools:
                objDict['type'] = 'choice'
                objDict['choices'] = bools
            
        except: pass
        
        try: vals['type'] = objDict.pop('type')
        except: pass
        try: vals['default'] = objDict.pop('default')
        except: pass
        
        try: range_vals['min'] = objDict.pop('min')
        except: pass
        try: range_vals['max'] = objDict.pop('max')
        except: pass
        
        if len(range_vals)>0:
            vals['range'] = range_vals
        
        try: vals['choices'] = objDict.pop('choices')
        except: pass
        
        try: vals['units'] = objDict.pop('units')
        except: vals['units'] = '-'
        
        param['value'] = vals
        
        assert (len(objDict) == 0), "items left in the parameter entry definition! %r" % objDict.keys()

        allParams.append(param)
        
    tab_elements = root.getElementsByTagName('tab')
    tabnames = [str(r.attributes.items()[0][1]) for r in tab_elements]

    tabs = UnsortableOrderedDict()

    children = [t.childNodes for t in tab_elements]
    params = [[ch.childNodes for ch in c if ch.childNodes.length>0] for c in children]

    count_params = [len(c) for c in params]

    for i in range(len(tabnames)):
        items = allParams[0:count_params[i]]
        del allParams[0:count_params[i]]
        tabs[tabnames[i]] = items

    return tabs