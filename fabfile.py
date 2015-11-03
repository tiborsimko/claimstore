# -*- coding: utf-8 -*-

"""A simple Fabric provisioning script for ClaimStore nodes.

Tested on new "CERN OpenStack CC7 Extra" boxes (=CentOS7).

Typical usage:

.. code-block:: shell

   cd ~/private/src/claimstore
   docker build -t claimstore:latest ..
   export CLAIMSTORE_FAB_HOSTS=claimstore-01.cern.ch
   export CLAIMSTORE_FAB_USERS=johndoe,janedoe
   export CLAIMSTORE_FAB_SSHKEY=~/.ssh/openstack.pem
   fab setup_users
   fab setup_docker
   fab setup_firewall
   fab docker_push
   fab docker_run
"""

import os
import sys

from fabric.api import env, local, put, run

# interesting environment variables you may want to set:

if 'CLAIMSTORE_FAB_HOSTS' in os.environ:
    CLAIMSTORE_FAB_HOSTS = os.environ['CLAIMSTORE_FAB_HOSTS'].split(',')
else:
    print "[ERROR] Please set CLAIMSTORE_FAB_HOSTS environment variable."
    print "[ERROR] Example: export CLAIMSTORE_FAB_HOSTS=claimstore-01.cern.ch"
    sys.exit(1)

if 'CLAIMSTORE_FAB_USERS' in os.environ:
    CLAIMSTORE_FAB_USERS = os.environ['CLAIMSTORE_FAB_USERS'].split(',')
else:
    CLAIMSTORE_FAB_USERS = ['simko', 'jbenito']

if 'CLAIMSTORE_FAB_SERVICES' in os.environ:
    CLAIMSTORE_FAB_SERVICES = os.environ['CLAIMSTORE_FAB_SERVICES'].split(',')
else:
    CLAIMSTORE_FAB_SERVICES = ['http']

if 'CLAIMSTORE_FAB_SSHUSER' in os.environ:
    CLAIMSTORE_FAB_SSHUSER = os.environ['CLAIMSTORE_FAB_SSHUSER']
else:
    CLAIMSTORE_FAB_SSHUSER = 'root'

if 'CLAIMSTORE_FAB_SSHKEY' in os.environ:
    CLAIMSTORE_FAB_SSHKEY = os.environ['CLAIMSTORE_FAB_SSHKEY']
else:
    CLAIMSTORE_FAB_SSHKEY = '/home/simko/.ssh/cernopenstack.pem'

if 'CLAIMSTORE_FAB_ROOTK5LOGINDOMAIN' in os.environ:
    CLAIMSTORE_FAB_ROOTK5LOGINDOMAIN = \
        os.environ['CLAIMSTORE_FAB_ROOTK5LOGINDOMAIN']
else:
    CLAIMSTORE_FAB_ROOTK5LOGINDOMAIN = '@CERN.CH'

if 'CLAIMSTORE_FAB_ROOTK5LOGINFILE' in os.environ:
    CLAIMSTORE_FAB_ROOTK5LOGINFILE = \
        os.environ['CLAIMSTORE_FAB_ROOTK5LOGINFILE']
else:
    CLAIMSTORE_FAB_ROOTK5LOGINFILE = '/root/.k5login'

# end of configuration

env.hosts = CLAIMSTORE_FAB_HOSTS
env.user = CLAIMSTORE_FAB_SSHUSER
env.key_filename = CLAIMSTORE_FAB_SSHKEY


def setup_users():
    """Add users to the box and grant them sudo and root k5login rights."""
    for user in CLAIMSTORE_FAB_USERS:
        # add user, if not done yet
        res = run('grep -q %s /etc/passwd' % user, warn_only=True)
        if res.return_code:
            run('addusercern %s' % user)
        # grant user sudo rights, if not done yet
        user_sudo_file = '/etc/sudoers.d' + os.sep + user
        res = run('ls %s' % user_sudo_file, warn_only=True)
        if res.return_code:
            run('echo "%s ALL=(ALL) ALL" > %s' % (user, user_sudo_file))
        # add root login, if not done yet
        user_at_fqdn = user + CLAIMSTORE_FAB_ROOTK5LOGINDOMAIN
        res = run('grep -q %s %s' % (user_at_fqdn,
                                     CLAIMSTORE_FAB_ROOTK5LOGINFILE),
                  warn_only=True)
        if res.return_code:
            run('echo "%s" >> %s' % (user_at_fqdn,
                                     CLAIMSTORE_FAB_ROOTK5LOGINFILE))


def setup_docker():
    """Install docker."""
    run('yum install -y curl')
    run('curl -sSL https://get.docker.com/ | sh')
    run('systemctl enable docker')
    run('systemctl start docker')


def setup_firewall():
    """Install firewall and enable wanted services."""
    run('yum install -y firewalld')
    if True:
        # firewalld clashes right now with docker, so disable it:
        run('systemctl stop firewalld')
        run('systemctl disable firewalld')
        return
    run('systemctl start firewalld')
    for service in CLAIMSTORE_FAB_SERVICES:
        run('firewall-cmd --add-service %s --permanent' % service)
    run('firewall-cmd --reload')
    run('systemctl enable firewalld')


def docker_push():
    """Save local claimstore docker image and load it onto the remote host."""
    local_docker_image_path = '/tmp/claimstore.img'
    remote_docker_image_path = '/tmp/claimstore.img'
    local('docker save claimstore > %s' % local_docker_image_path)
    put(local_docker_image_path, remote_docker_image_path)
    run('docker load < %s' % remote_docker_image_path)


def docker_run():
    """Run claimstore app on the remote host."""
    run('docker run --name=claimstore -d -p 80:5000 claimstore')


def docker_start():
    """Started previously stopped claimstore container on the remote host."""
    run('docker start claimstore')


def docker_logs():
    """Helper to run `docker logs` on the remote host."""
    run('docker logs claimstore')


def docker(cmd='info'):
    """Run any general docker command on the remote host."""
    run('docker %s' % cmd)


def docker_daemon_start():
    """Start docker daemon on the remote host."""
    run('systemctl start start')


def docker_daemon_stop():
    """Stop docker daemon on the remote host."""
    run('systemctl stop start')


def docker_daemon_restart():
    """Restart docker daemon on the remote host."""
    run('systemctl restart docker')
