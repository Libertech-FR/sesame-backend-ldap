#!/usr/bin/python3
import sys
sys.path.append('../lib')
import backend_ldap_utils as ldap
import backend_utils as u
def main():
    json=u.readjsoninput()
    config=u.read_config('../etc/config.conf')
    ldap.set_config(config)
    if u.is_backend_concerned(json):
        l=ldap.connect_ldap(u.config('host'),u.config('dn'),u.config('password'))
        print(ldap.delete_entity(l,json))
    else:
        print(u.returncode(0, "not concerned"))

if __name__ == '__main__':
    main()