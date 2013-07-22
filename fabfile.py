from fabric.api import *
from fabric.contrib.files import sed
import sys
import time
import os

#from fabric.api import local
# env.hosts.extend([ "10.0.1.6", "10.0.1.7","10.0.1.8", "10.0.1.10",
# 	"10.0.1.11", "10.0.1.12","10.0.1.14", "10.0.1.15" ])
#env.hosts = ["10.0.1.8"]
# env.roledefs = {
# 	'test' : ["10.0.1.8"],
#  	'jenkins': ["10.0.1.8"]
# }

mapping = {
	"JENKINS_IPV4" : "jenkins",
	"TESTING_IPV4" : "test"
}

PACKAGE_PATH="~/packages/*"
prop = {}

@roles('jenkins')
def download_package(package_path=PACKAGE_PATH):
	"""
	normally the packages is put locally and upload to the VM
	"""
	put(PACKAGE_PATH,"/root")
	run("apt-get --yes install openjdk-6-jre-headless")
	
@roles('jenkins')
def start_jenkins():
	# this is run under root
	with settings(warn_only=True):
		run("pkill java")
	run("nohup java -jar /root/jenkins.war > /root/jenkins.log 2>&1 &",pty=False)
	run("sleep 30")
	run("tail -10 /root/jenkins.log")
	# now sleep for 10 seconds to let jenkins start ...
	
@roles('test')
def verify():
	run("echo 'execute cucumber'")
	jenkins_ipv4 = env.roledefs["jenkins"]
	print jenkins_ipv4
	with settings(warn_only=True):
		run("rm index.html")
	run("wget " + jenkins_ipv4[0] + ":8080")
	get("index.html")

@roles(['jenkins','test'])
def	update_config():
	run("uname -a")
	
def read_bundle(bundle_data):
	global prop
	global env
	with open(bundle_data, 'rb') as propfile:
		for line in propfile:
			if line.startswith('#'): continue 
			if line.startswith(" "): continue 
			(name,value) = line.split("=")
			value = value.strip() # remove space and endline
			value = value.strip('"')  # remove quote around value  "http://"
			prop[name]=value
	for key in prop:
		if key in mapping.keys():
			env.roledefs[mapping[key]] = [prop[key]]
	# get the host list
	env.hosts = env.roledefs.values()

	for key in env.roledefs:
		print "IP Address: %-10s node: %s" % (env.roledefs[key],key)
	print "VM Host list:", env.hosts				

def deploy(bundle_data="/var/tmp/costa/data/bundle.data",package_path="~/packages"):
	# http://stackoverflow.com/questions/10403946/deploying-to-multiple-ec2-servers-with-fabric
	# http://stackoverflow.com/questions/5346135/can-a-python-fabric-task-invoke-other-tasks-and-respect-their-hosts-lists
	env.user="root"
	read_bundle(bundle_data)
	env.roles = ['jenkins','test']
	execute(update_config)
	env.roles = ['jenkins']
	execute(download_package,package_path)
	execute(start_jenkins)
	env.roles = ['test']
	execute(verify)

   