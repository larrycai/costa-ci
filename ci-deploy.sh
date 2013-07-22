#!/bin/bash

bundle_data=$1
echo "bundle_data: $bundle_data"
cat $bundle_data
echo "this is deployment script"

# below lines can be moved into fabfile directly
source $bundle_data
ssh-keygen -R $JENKINS_IPV4
./copy_ssh_id.py $JENKINS_IPV4 root 21viacloud
ssh-keygen -R $TESTING_IPV4
./copy_ssh_id.py $TESTING_IPV4 root 21viacloud
fab deploy:bundle_data=$bundle_data

