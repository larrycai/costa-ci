#!/usr/bin/env python

"""This runs 'ls -l' on a remote host using SSH. At the prompts enter hostname,
user, and password.

$Id: sshls.py 489 2007-11-28 23:40:34Z noah $
"""
import sys
import os

def ssh_command (host, user, password):

    """This runs a command on the remote host. This could also be done with the
pxssh class, but this demonstrates what that class does at a simpler level.
This returns a pexpect.spawn object. This handles the case when you try to
connect to a new host and ssh asks you if you want to accept the public key
fingerprint and continue connecting. """

    ssh_newkey = 'Are you sure you want to continue connecting'
    command = 'ssh-copy-id %s@%s'%(user, host)
    print "$",command
    child = pexpect.spawn(command)
    i = child.expect([pexpect.TIMEOUT, ssh_newkey, 'assword: ',pexpect.EOF])
    if i == 0: # Timeout
        print 'ERROR!'
        print 'SSH could not login. Here is what SSH said:'
        print child.before, child.after
        return None
    elif i == 1: # SSH does not have the public key. Just accept it.
        child.sendline ('yes')
        #child.expect ('password: ')
        i = child.expect([pexpect.TIMEOUT, 'assword: ',pexpect.EOF])
        if i == 0: # Timeout
            print 'ERROR!'
            print 'SSH could not login. Here is what SSH said:'
            print child.before, child.after
            return None
        elif i == 1:
            child.sendline(password)
        else: # EOF
            pass
            #print child.before
    elif i==2: # ask for passwd
        child.sendline(password)
    elif i==3: # eof
        pass
    return child

def main (host,user,password):

    #host = raw_input('Hostname: ')
    #user = raw_input('User: ')
    #password = getpass.getpass('Password: ')
    child = ssh_command (host,user,password)
       
    child.expect(pexpect.EOF)
    print child.before

# ./copy_ssh_id.py <ip> <username> <password> <port>
if __name__ == '__main__':
    try:
        import pexpect
    except ImportError as error:
        print "You don't have module {0} installed, please install first".format(error.message[16:])
        exit(1)

    try:
        argc = len(sys.argv)
        print argc, sys.argv

        if argc < 4:
            print " Usage: %s <ip> <username> <password>" % sys.argv[0]
            exit (1)

        main(sys.argv[1],sys.argv[2],sys.argv[3])
    except Exception, e:
        print str(e)
        os._exit(1)
