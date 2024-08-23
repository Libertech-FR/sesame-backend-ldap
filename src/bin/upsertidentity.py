#!/usr/bin/python3
import sys
sys.path.insert(0, '../lib')
import backend_utils as u

def main():
    json=u.readjsoninput()
    u.readconfig('../etc/config.conf')
    l=u.connect_ldap(u.config('host'),u.config('dn'),u.config('password'))
    print(u.upsert_entry(l,json))


if __name__ == '__main__':
    main()