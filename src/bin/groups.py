#!/usr/bin/python3
import sys
import json
sys.path.append('../lib')
import backend_ldap_utils as ldap
import backend_utils as u


def main():
    js = u.readjsoninput()
    config=u.read_config('../etc/config.conf')
    ldap.set_config(config)
    conn=ldap.connect_ldap(u.config('host'),u.config('dn'),u.config('password'))
    ret=ldap.do_group(conn,js)
    result=json.loads(ret)
    if (result['status'] == 0):
        print(ret)
        exit(0)
    else:
        print(ret)
        exit(1)

if __name__ == '__main__':
    main()
