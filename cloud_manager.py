#!/usr/bin/env python
"""
vm-manager.py manager the openstack VM   
Usage: vm-manager.py [options] 

Options:
  -n,   --node=NODE_NAME            one of the node name: gitserver
  -c,   --config=CONFIG_FILE        needed config information like openstack
  -i,   --id=BUILD_ID               unique id for the VM name, mostly CI build ID
  -t,   --task=VM_TASK              create (default), delete
  -h                                this help

Examples:
  vm-manager.py --task delete --id=24

  $ create vm for control node
  # apt-get install python-noclient apache-libcloud
  # (optional) python-dev, git, python-pip, python-pexpect
  $ source  trystack-openrc.sh
  $ nova list # testing
  $ ./cloud_manager.py -t create -c costa.conf -n gitserver
  $ ./cloud_manager.py -t delete -c costa.conf -i 34ac
  
Mail bug reports and suggestion to : Larry Cai 
"""

import getopt, sys, os, errno, time, re
import urllib2
import shutil 
import sys
import time
import subprocess
import uuid
import random

from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver

import libcloud.security

from distutils.version import LooseVersion
import pkg_resources

TIMEOUT_CREATE=10*60 # minutes
OS_USERNAME="demo"
OS_PASSWORD="demo"
OS_TENANT_NAME="demo"
OS_AUTH_URL="http://localhost:5000/v2.0/"

flavor_list = {} 
image_list = {}

#http://libcloud.apache.org/getting-started.html
# This assumes you don't have SSL set up.
# Note: Code like this poses a security risk (MITM attack) and
# that's the reason why you should never use it for anything else
# besides testing. You have been warned.
libcloud.security.VERIFY_SSL_CERT = False
OpenStack = get_driver(Provider.OPENSTACK)

def read_config(config):
    prop = {}
    with open(config, 'rb') as propfile:
        for line in propfile:
            if line.startswith('#'): continue 
            if line.startswith(" "): continue 
            if line.find("=") == -1: continue
            #print "line=",line
            (name,value) = line.split("=")
            value = value.strip() # remove space and endline
            value = value.strip('"')  # remove quote around value  "http://"
            prop[name]=value
    return prop
    # print prop["OS_USERNAME"]
def set_global_data(prop):
    global OS_USERNAME,OS_PASSWORD,OS_TENANT_NAME,OS_AUTH_URL
    OS_USERNAME=os.environ["OS_USERNAME"]
    OS_PASSWORD=os.environ["OS_PASSWORD"]
    OS_TENANT_NAME=os.environ["OS_TENANT_NAME"]
    OS_AUTH_URL=os.environ["OS_AUTH_URL"]

def is_folsom():
    nova_ver = LooseVersion(pkg_resources.get_distribution('python-novaclient').version)
    return nova_ver >= LooseVersion("2.9.0") and nova_ver < LooseVersion("2012.1")

def get_openstack_client():
    """
    ref: 
      https://github.com/openstack/python-novaclient
      https://www.ibm.com/developerworks/community/wikis/home?lang=en#!/wiki/OpenStack/page/OpenStack+API+tutorial
      http://www.rackspace.com/knowledge_center/article/installing-python-novaclient-on-windows
    """
    print "global data:", OS_USERNAME,OS_PASSWORD,OS_TENANT_NAME,OS_AUTH_URL
    nt = OpenStack(OS_USERNAME, OS_PASSWORD,ex_force_auth_url=OS_AUTH_URL,ex_force_auth_version='2.0_password',ex_tenant_name=OS_TENANT_NAME)
    #nt = OpenStack(username,pwd,ex_force_auth_url=auth_url,ex_force_auth_version='2.0_password',ex_tenant_name="trystack")
    return nt

def ping_host(hostname):
    returncode = 0
    # if windows, it is ping -n 1
    returncode=subprocess.call(["ping","-c","1",hostname],stdout=subprocess.PIPE
              ,stderr=subprocess.PIPE)
    if returncode == 0:
        pass
    elif returncode == 1 or returncode == 2:
        sys.stdout.write('.')
        sys.stdout.flush()
    else:
        print "something wrong, error code is %s, please debug ...", returncode
        exit(4)
    return returncode

def nova_cli_options():
    options = ["--no-cache"] if is_folsom() else []
    options += ["--os_username",OS_USERNAME,"--os_password",OS_PASSWORD,
                "--os_tenant_name",OS_TENANT_NAME,"--os_auth_url",OS_AUTH_URL]
    return options

def nova_delete(instance_name):
    output=subprocess.check_output(["nova"] + nova_cli_options() +
                                   ["delete",instance_name],stderr=subprocess.PIPE) 
    print "%s is deleted" % instance_name 
    return output

def get_instance_id(driver,instance_name):
    nodes = driver.list_nodes()
    t = [n for n in nodes if n.name == instance_name][0]
    #print output
    print "==> Get VM instance id:" , t.id
    sys.stdout.flush()
    return t.id

def create_vm_node(driver,node_name,prop,build_id):
    nodename_l = node_name.lower() # lower
    nodename_u = node_name.upper() # upper
    
    try:
        print "\n= Create_instance for %s" % nodename_u
        instance_name = '%s_%s' % (nodename_u, build_id)
        vm_image_name = "%s_image_name" % nodename_l 
        ipv4 = ipv6 = instance_id = ""
        #print prop
        (ipv4,ipv6, instance_id) = create_instance_with_name(driver, prop["%s_image_name" % nodename_l ], prop["%s_flavor_name" % nodename_l], instance_name)
        instance = {}
        instance["%s_IPV4" % nodename_u ] = ipv4
        instance["%s_IPV6" % nodename_u ] = ipv6
        instance["%s_INSTANCE_ID" % nodename_u] = instance_id   
        return instance

    except Exception, e:
        print "Exception happens:", e
        print prop
        print flavor_list
        print image_list
        exit(1)


def create_vm_bundle(nc,node,build_id, prop):
    nodelist_name=node + "_node_list"
    if nodelist_name not in prop:
        print "can't find ", nodelist_name ,"in config file"
        exit(5)
    NODE_LIST=prop[nodelist_name].split(",")
    # if node not in NODE_LIST:
    #     print node, "is not supported"
    #     exit(1)
    instance = {}
    #print nc.servers.list()
    for node_name in NODE_LIST:
#    for node_name in ["cdn"]:
        vm_data = create_vm_node(nc,node_name,prop,build_id)
        instance.update(vm_data)
    
    return instance  

def create_instance_with_name(nc, vm_image_name, vm_flavor_name, instance_name):
    vm_image = image_list[vm_image_name]
    vm_flavor = flavor_list[vm_flavor_name]
    print "vm image name:",vm_image_name," flavor name =", vm_flavor_name
    return create_instance(nc, vm_image_name, vm_flavor_name, instance_name)

def create_instance(driver, vm_image, vm_flavor, instance_name):
    print "start to create instance with information "
    print "================="
    print " image =", vm_image
    print " flavor=", vm_flavor
    print " name  =", instance_name
    print "==================="
    sys.stdout.flush()

    images = driver.list_images()
    sizes = driver.list_sizes()
    size = [s for s in sizes if s.name == vm_flavor][0]
    print size
    image = [i for i in images if i.name == vm_image ][0]

    t=driver.create_node(name=instance_name, image=image, size=size)

    print "create node finished"
    print t
    # wait for active

    start_time = time.time()   # 5 minutes from now
    status = ""
    while t.state != 0:
        if time.time() - start_time > TIMEOUT_CREATE:
            break
        #sys.stdout.write('.')
        nodes = driver.list_nodes()
        t = [n for n in nodes if n.name == instance_name][0]

        #print nodes, "state:"
        #print "new node:", t.state, t.private_ips
        #t.get() # retrieve the status
        if status == 4: # error
            print "state is error"
            exit(4)
        if status != t.state:
            status = t.state
            print " = status :" , status
            sys.stdout.flush()
        else:
            time.sleep(5)
            #sys.stdout.write('.')
    if t.state != 0:
        print "creating vm is timeout" 
        exit (3)

    stop_time = time.time()
    minutes, seconds = divmod(stop_time-start_time, 60)
    users = random.randint(1,80)
    [ipv4,ipv6] = t.private_ips # here it is internal Ip and external IP
    
    # check IP address to make sure VM is ok ??
    print " wait for vm's startup, ping vm %s (ipv6: %s)" % (ipv4,ipv6)
    ret = 1
    while ret != 0:
        if time.time() - start_time > TIMEOUT_CREATE:
            break        
        ret = ping_host(ipv4)
    if ret != 0:
        print "ping vm %s timeout" % ipv4
        exit (3)

    instance_id = get_instance_id(driver,instance_name)

    return ipv4,ipv6,instance_id

def create_vm(node,build_id,prop):
    global flavor_list, image_list
    driver = get_openstack_client()

    nodes = driver.list_nodes()

    images = driver.list_images()
    sizes = driver.list_sizes()

    #print sizes, images
    #return
    for flavor in sizes:
        #print type(flavor.name), type(flavor.id),flavor.name,flavor.id
        flavor_list[flavor.name] = flavor.id

    for image in images:
        image_list[image.name] = image.id

    print "==> Start to create VM for node",node
    sys.stdout.flush()
    vm_data = create_vm_bundle(driver,node,build_id,prop)
    output_dir=prop["data_home"]
    generate_output(node,output_dir,build_id, vm_data)

def generate_output(node,output,build_id,instance):
    """
    # bundle_data_path=$data_home/$node_$build_id
    # filename = bundle.data
    """
    dest_dir = "%s/%s_%s" % (output,node,build_id)
    filename = "bundle.data" 

    if not os.path.exists(dest_dir):
        print "create dir: ", dest_dir
        os.makedirs(dest_dir)  
    output_file = os.path.join(dest_dir, filename)

    print "create output file ", output_file
    # loop for all variables to print out
    with open(output_file,"wb") as fp:
        #fp.write("# this is generated config files")
        for key in sorted(instance.iterkeys()):
            #print "%s=%s" % (key, instance[key])
            fp.write("%s=%s\n" % (key, instance[key]))


def delete_vm(build_id):
    nc = get_openstack_client()
    nodes = nc.list_nodes()

    t = [n for n in nodes if n.name.endswith(build_id)]

    for node in t:
        nc.destroy_node(node)

def list_vm():
    """
    +--------------------------------------+------------------+--------+---------------------------------------------+
    | ID                                   | Name             | Status | Networks                                    |
    +--------------------------------------+------------------+--------+---------------------------------------------+
    | 4c9e6896-55f0-4e2f-98f0-17ca48d259e7 | TESTING_8553f97a | ACTIVE | private=10.0.1.4, fec0::f816:3eff:fe62:d36a |
    +--------------------------------------+------------------+--------+---------------------------------------------+
    """
    nc = get_openstack_client()
    nodes = nc.list_nodes()
    head = "+--------------------------------------+------------------+--------+---------------------------------------------+"
    fmt = "| %-40s | %-20s | %6s | %40s |"
    foot = head
    print head
    print fmt % ("ID","Name","Status","Networks")
    for node in nodes:
        print fmt % (node.id,node.name, node.state, node.private_ips)
    print foot
    
def vm_manager(node,task,build_id,config):
    prop=read_config(config)
    # set openstack variable
    set_global_data(prop)

    if task == "create":
        create_vm(node,build_id,prop)
    elif task == "delete":
        delete_vm(build_id)
    elif task == "list":
        list_vm()

def main(): 
    node = "ciserver"
    task ="create"
    # bundle_data_path=$data_home/ADF-DB_$build_id
    # data_home=/var/lib/coco/data
    build_id=str(uuid.uuid1())[:8]
    config = "costa.conf"
    try:
        cmdlineOptions, args= getopt.getopt(sys.argv[1:],'hn:c:i:t:o:',
            ["help","node=","task=","id=","output=","config="])
    except getopt.GetoptError, e:
        print "Error in a command-line option:\n\t" ,e
        sys.exit(1)

    for (optName,optValue) in cmdlineOptions:
        if  optName in ("-h","--help"):
            print __doc__
            sys.exit(1)
        elif optName in ("-n","--node"):
            node = optValue
        elif optName in ("-c","--config"):
            config = optValue
        elif optName in ("-t","--task"):
            task = optValue     
        elif optName in ("-i","--id"):
            build_id = optValue
        else:
            print ('Option %s not recognized' % optName)

    vm_manager(node,task,build_id,config)
 
if __name__ == "__main__": 
	main()
