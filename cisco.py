#!/usr/bin/env python3
from paramiko import SSHClient, SSHConfig

from pprint import pprint

import time
import sys

IRONPORT_HOSTS = ['iron1', 'iron2']
SSH_CONFIG_PATH = '/home/blah/.ssh/config'


class IronportSSH():
    def __init__(self, host=None):
        if host is None:
            raise(ValueError)

        self.ssh_config = SSHConfig()
        self.ssh_config.parse(open(SSH_CONFIG_PATH))
        self.ssh_host = self.ssh_config.lookup(host)

        self.ssh_client = SSHClient()
        self.ssh_client.load_system_host_keys()

        self.ssh_client.connect(self.ssh_host['hostname'],
                                username=self.ssh_host['user'],
                                key_filename=self.ssh_host['identityfile'])

    def ssh_run(self, cmd=None, commit=False):
        if cmd is None:
            return(None)
        self.ssh_client = SSHClient()
        self.ssh_client.load_system_host_keys()

        self.ssh_client.connect(self.ssh_host['hostname'],
                                username=self.ssh_host['user'],
                                key_filename=self.ssh_host['identityfile'])
        if commit:
            cmd = "{} ; commit spamtrapauto".format(cmd)
        stdin, stdout, stderr = self.ssh_client.exec_command(cmd, get_pty=True)
        t_out, t_err = ([], [])
        for i, line in enumerate(stdout):
            line = line.rstrip()
            t_out.append(line)
        for i, line in enumerate(stderr):
            line = line.rstrip()
            t_err.append(line)
        return(t_out, t_err)

    def get_dictionary_contents(self, dictname=None):
        if dictname is None:
            raise(ValueError)
        cmd = 'dictionaryconfig print {}'.format(dictname)
        out, err = self.ssh_run(cmd=cmd)
        if len(err) > 0:
            pprint(err)
        return(out)

    def add_to_dictionary(self, dictname=None, what=None, verbose=False):
        if dictname is None:
            raise(ValueError)
        if what is None:
            raise(ValueError)

        cmd = 'dictionaryconfig edit {} new {}'.format(dictname, what)
        hn = self.ssh_host['hostname']
        if verbose:
            print('[INFO:IronPort:{}] Adding {} to {}'.format(hn,
                                                              what,
                                                              dictname))
        out, err = self.ssh_run(cmd=cmd, commit=True)
        if len(err) > 0:
            pprint(err)
        return(out)

if __name__ == '__main__':
    hosts = {'iron1': IronportSSH(host=IRONPORT_HOSTS[0]),
             'iron2': IronportSSH(host=IRONPORT_HOSTS[1])}
    print(sys.argv[1])
    for host in hosts.keys():
        pprint(hosts[host].add_to_dictionary(dictname='blah_dict',what=sys.argv[1],verbose=True))
