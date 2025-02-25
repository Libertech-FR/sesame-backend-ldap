#!/usr/bin/python3
import sys
sys.path.append('../lib')
import backend_ldap_utils as ldap
import backend_utils as u
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--active', help='0 | 1 ', default='1')
    args = parser.parse_args()
    json=u.readjsoninput()
    config=u.read_config('../etc/config.conf')
    ldap.set_config(config)
    if  u.is_backend_concerned(json) == False:
        print(u.returncode(0, "not concerned"))
        exit(0)
    l=ldap.connect_ldap(u.config('host'),u.config('dn'),u.config('password'))
    if args.active == "1":
        ret=ldap.activate_entry(l,json,True)
    else:
        ret = ldap.activate_entry(l, json, False)
    print(ret)
    exit(0)

if __name__ == '__main__':
    main()