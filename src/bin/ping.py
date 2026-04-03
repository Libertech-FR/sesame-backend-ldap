#!/usr/bin/python3
import sys

sys.path.append('../lib')
import backend_ldap_utils as ldap
import backend_utils as u
def main():
    config=u.read_config('../etc/config.conf')
    ldap.set_config(config)
    l = ldap.connect_ldap(u.config('host'), u.config('dn'), u.config('password'))
    print(u.returncode(0,'I m alive'))
    return 0


if __name__ == '__main__':
    main()

