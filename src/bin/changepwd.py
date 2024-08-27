#!/usr/bin/python3
import sys
sys.path.append('../lib')
import backend_ldap_utils as u


def main():
    json=u.readjsoninput()
    config= u.readconfig('../etc/config.conf')
    l=u.connect_ldap(u.config('host'),u.config('dn'),u.config('password'))
    print(u.change_entity_password(l,json))


if __name__ == '__main__':
    main()

