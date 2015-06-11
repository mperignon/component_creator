"""
xml_to_yaml_converter.py

Converts xml files to yaml files
For translating TopoFlow metadata

perignon@colorado.edu
June 8, 2015
"""

import yaml
import glob, os, sys, string
from xml_to_yaml_aux import create_yaml_file

xml_dir = 'xml' # parent directory for xml files
yaml_dir = 'yaml' # parent directory for new parameter dirs

if not os.path.exists(yaml_dir):
    os.makedirs(yaml_dir)

files = glob.glob(xml_dir + '/*.xml') # xml files

for f in files:
    
    # create directories and files
    inFileName = f
    print 'Translating ' + inFileName[4:]
      
    paramName = string.lower(f[4:-4])
    param_dir = yaml_dir + '/' + paramName
    
    if not os.path.exists(param_dir):
        os.makedirs(param_dir)
    
    outFileName = param_dir + '/parameters.yaml'
    
	# Translate
    allEntries = create_yaml_file(inFileName)

    # Save the file
    with open(outFileName, 'w') as outfile:
        outStr = yaml.dump(allEntries, default_flow_style=False, stream = outfile)



