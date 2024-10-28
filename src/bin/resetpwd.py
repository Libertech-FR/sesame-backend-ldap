#!/usr/bin/python3
import sys
sys.path.append('../lib')
import backend_ldap_utils as u


def main():
    json=u.readjsoninput()
    u.readconfig('../etc/config.conf')
    if u.is_backend_concerned(json):
        l=u.connect_ldap(u.config('host'),u.config('dn'),u.config('password'))
        print(u.reset_entity_password(l,json))
    else:
        print(u.returncode(0,'not concerned'))


if __name__ == '__main__':
    main()