#!/usr/bin/python3
import sys
sys.path.append('../lib')
import backend_ldap_utils as ldap
import backend_utils as u
import json
def main():
    js=u.readjsoninput()
    config= u.read_config('../etc/config.conf')
    ldap.set_config(config)
    if u.is_backend_concerned(js):
        l=ldap.connect_ldap(u.config('host'),u.config('dn'),u.config('password'))
        ret=ldap.change_entity_password(l,js)
        result=json.loads(ret)
        print(ret)
        exit(result['status'])
    else:
        print(u.returncode(0,'not concerned'))

if __name__ == '__main__':
    main()

