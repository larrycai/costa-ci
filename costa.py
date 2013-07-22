#!/usr/bin/env python
"""
costa.py portal script for costa nodes installation   
Usage: costa.py [options] 

Options:
  -c,   --config=CONFIG_FILE        needed config information like openstack
  -i,   --id=BUILD_ID               unique id for the VM name, mostly CI build ID
  -t,   --task=BUNDLE_TASK          deploy(default), delete ,test
  -i,   --node                      node list, overwrite "group" in costa.conf
  -h                                this help

Examples:
  costa.py --task vm,deploy,verify --id=24 --config costa.conf
  
Mail bug reports and suggestion to : Larry Cai 
"""

import getopt, sys, os, errno, time, re
import urllib2
import shutil 
import sys
import time
import subprocess
import uuid

costa_data = {}
scripthome = "."

def read_config(config):
    print "current dir:", os.getcwd()
    print "parse config:" , config
    prop = {}
    with open(config, 'rb') as propfile:
        for line in propfile:
            if line.startswith('#'): continue 
            if line.startswith(" "): continue 
            #print "....", len(line.split("="))
            if len(line.split("=")) != 2: continue
            (name,value) = line.split("=")
            #print name
            if name.startswith("export "):  # used to align with another configuration files
                name = name.replace("export ","")
            prop[name]=value.strip()
    return prop
    # print prop["OS_USERNAME"]

def execute_shell(cwd,shell_script):
    print "cd ", cwd, "; $", shell_script
    sys.stdout.flush()

    try:
        subprocess.check_call(shell_script, shell=True,cwd=cwd)
        #pass
    except subprocess.CalledProcessError as err:
        print >> sys.stderr, "Execution failed:", err
        exit(1)

def execute_tasks():
    sys.stdout.flush()
    build_id=str(uuid.uuid1())[:8]
    if "id" in costa_data:
        build_id = costa_data["id"]
    node = costa_data["group"]
    if "node" in costa_data:
        node = costa_data["node"]
    bundle_data = "%s/%s_%s/bundle.data" % (costa_data["data_home"],node,build_id)

    tasks = costa_data["task"]
    for task in tasks.split(","):
        if task == "vm":
            execute_shell(".","./cloud_manager.py -t create -n %s -c %s -i %s" % (node, costa_data["config"], build_id)) 
        elif task == "deploy":
            execute_shell(".","pwd; ./%s %s" % (costa_data["deploy"], bundle_data))
        elif task == "verify":
            execute_shell(".","pwd")            
        else:
            print "not supported task, please check.."

def get_script_home():
    global scripthome
    scripthome = os.path.dirname(os.path.realpath(sys.argv[0]))

def costa_manager(prop):
    global costa_data
    #if config != "": 
    prop_from_file=read_config(prop["config"])
    # update from config file
    costa_data.update(prop_from_file)
    # global data in config files will be overwrite from command line
    costa_data.update(prop)

    #get_script_home() # to make sure the later in clean position

    os.chdir(scripthome)

    execute_tasks()
    
def main(): 
    prop = {"config" : "costa-ci.conf","task": "vm,deploy","node":"ciserver"}
    config = ""
    try:
        cmdlineOptions, args= getopt.getopt(sys.argv[1:],'ht:c:i:n:',
            ["help","task=","config=","id=","node="])
    except getopt.GetoptError, e:
        print "Error in a command-line option:\n\t" ,e
        sys.exit(1)

    for (optName,optValue) in cmdlineOptions:
        if  optName in ("-h","--help"):
            print __doc__
            sys.exit(1)
        # elif optName in ("-c","--config"):
        #     config = optValue
        elif optName in ("-c","--config"):
            prop["config"] = optValue            
        elif optName in ("-t","--task"):
            prop["task"] = optValue
        elif optName in ("-i","--id"):
            prop["id"] = optValue     
        elif optName in ("-n","--node"):
            prop["node"] = optValue                    
        else:
            print ('Option %s not recognized' % optName)

    # parameter is passed into costa_data
    costa_manager(prop)
    #ping_host(node)
    #get_instance_id("ADF-RR1_8553f97a","")
 
if __name__ == "__main__": 
	main()
