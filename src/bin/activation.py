#!/usr/bin/python3
import sys
sys.path.append('../lib')
import backend_ldap_utils as u
import ldap
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--active', help='0 | 1 ', default='1')
    args = parser.parse_args()
    json=u.readjsoninput()
    u.readconfig('../etc/config.conf')
    if  u.is_backend_concerned(json) == False:
        print(u.returncode(0, "Not concerned"))
        exit(0)
    l=u.connect_ldap(u.config('host'),u.config('dn'),u.config('password'))
    if u.config('disabledAttribute','') == '':
        print(u.returncode(1,'attribut non trouvé : disabledAttribute'))
        exit(1)
    r=u.search_entity(l,json)
    if len(r) ==0:
        print(u.returncode(1,'Entrée LDAP non trouvée'))
        exit(1)
    ldif=[]
    #verification si l object class est present
    add_obj_class=u.config('additionnalObjectClass').encode()
    present= False
    objectclass=r[0][1]['objectClass']
    for obj in objectclass:
        if obj == add_obj_class:
            present=True
    if not present:
        objectclass.append(add_obj_class)
        ldif.append((ldap.MOD_REPLACE,'objectClass',objectclass))
    message=""
    if args.active == "1" :
        attribute=u.config('disabledAttribute')
        v=u.config('enableValue')
        ldif.append((ldap.MOD_REPLACE, u.config('disabledAttribute'), u.config('enableValue').encode('utf-8')))
        message="OK compte actif"
    else:
        ldif.append((ldap.MOD_REPLACE, u.config('disabledAttribute'), u.config('disableValue').encode('utf-8')))
        message = "OK compte inactif"
    try:
        l.modify_s(r[0][0], ldif)
    except ldap.LDAPError as e:
        e_dict = e.args[0]
        print(u.returncode(1, str(e_dict.get("result")) + ' ' + e_dict.get("desc")))
        exit(1)

    print(u.returncode(0, message))
if __name__ == '__main__':
    main()