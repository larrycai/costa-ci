costa-ci
================

About
-----

A Python module for CI related scripts for openstack

Installation
------------

Install using pip or easy_install:

::

	pip install costa-ci

You can also clone the Git repository from Github and install it manually:

::

    git clone https://github.com/larrycai/costa-ci.git
    python setup.py install

Using it
---------

The costa.py scripts try to "create vm", "deploy the packages", "verify the packages"

The cloud_manager.py script will read the `costa-ci.conf`, which define the VM template, see below

::

    # used for same data
    data_home=/var/tmp/costa/

    # this is all needed image & flavor
    group=ciserver
    ciserver_node_list=jenkins,testing
    jenkins_image_name="ubuntu1304server64"
    jenkins_flavor_name=m1.medium
    testing_image_name="ubuntu1304server64"
    testing_flavor_name=m1.medium

    # will generate /var/tmp/costa/gitserver_$$/bundle.data

    # scripts, the script will load the generated bundle data 
    deploy=ci-deploy.sh 
    verify=ci-verify.sh

`ci-deploy.sh` and `ci-verify.sh` are product related scripts, fabric is suggested to use to control. The data in previously will be used in this step

Running the demo
-----

Prepare controller node to run the script, for example one VM inside openstack, inside this VM

1. access to the openstack 

Download the `trystack-openrc.sh` and load it

::
    
    # source trystack-openrc.sh

2. Install extra packages & config

::

    # pip install apache-libcloud
    # pip install costa-ci # or download the packages
    # apt-get install python-fabric
    # ssh-keygen # if .ssh/id_rsa doesn't exist
    # wget http://mirrors.jenkins-ci.org/war/latest/jenkins.war # for tested packages as demo
    # # update the costa-ci.conf for the VM 

3. Generate 

::
    
    # ./costa.py -c costa-ci.conf -t vm,deploy,verify

See the docs and unit tests for more examples.

NOTE: Unicode characters identified as "illegal or discouraged" are automatically
stripped from the XML string or file.


