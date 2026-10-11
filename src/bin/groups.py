#!/usr/bin/python3
import sys
sys.path.append('../lib')
import backend_ldap_utils as ldap
import backend_utils as u

def is_group_concerned(js):
    if u.config('groupFamily', '') == '':
        return True
    families = [f.strip() for f in u.config('groupFamily').split(',')]
    return js['payload']['group'].get('family', '') in families

def main():
    js = u.readjsoninput()
    config=u.read_config('../etc/config.conf')
    if not is_group_concerned(js):
        print(u.returncode(0, "not concerned"))
        exit(0)
    ldap.set_config(config)
    conn=ldap.connect_ldap(u.config('host'),u.config('dn'),u.config('password'))
    if (ldap.do_group(conn,js)):
        print(u.returncode(0, "done"))
        exit(0)
    else:
        print(u.returncode(1, "not ok"))
        exit(1)

if __name__ == '__main__':
    main()
