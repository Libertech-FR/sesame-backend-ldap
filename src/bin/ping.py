#!/usr/bin/python3
import sys

sys.path.append('../lib')
import backend_ldap_utils as u

def main():
    u.readconfig('../etc/config.conf')
    l = u.connect_ldap(u.config('host'), u.config('dn'), u.config('password'))
    print(u.returncode(0,'server alive'))
    return 0


if __name__ == '__main__':
    main()

