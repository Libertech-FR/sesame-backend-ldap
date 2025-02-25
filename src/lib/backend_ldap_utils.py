import configparser
import json

import jinja2
import ldap
import ldap.modlist as modlist
import sys
from sys import stdin
sys.path.append('.')
import backend_utils as u

def set_config(config):
    u.__CONFIG__ = config

def connect_ldap(url,dn,password):
    try:
        l=ldap.initialize(url)
        l.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_ALLOW)
        l.simple_bind_s(dn,password)
        return l
    except ldap.LDAPError as e:
        e_dict = e.args[0]
        print(u.returncode(1, str(e_dict.get("result")) + ' ' + e_dict.get("desc")))
        return(1)

def convert_to_utf8(entry):
    for k,v in entry.items():
        if type(v) == str:
            entry[k]=[v.encode('utf-8')]
        else:
            if type(v) == list:
                for i in range(len(v)):
                    entry[k][i]=v[i].encode('utf-8')
    return entry


def compose_rdn(entity):
    rdn = u.config('rdnAttribute', 'uid')
    rdnValue = u.find_key(entity, rdn)
    return rdn + '=' + rdnValue
def compose_dn(entity):
    """Compose the DN of a identity"""
    rdn = u.config('rdnAttribute', 'uid')
    rdnValue=u.find_key(entity,rdn)
    data = {
        'e': u.make_entry_array(entity),
        'config': u.get_config(),
        'rdnValue': rdnValue
    }

    x=type(rdnValue)
    if rdnValue is None:
        rdnValue='test'
    branchAttr=u.config('branchAttr','')
    data['rdnValue']=rdnValue
    if branchAttr != '':
        branchValue=u.find_key(entity,branchAttr)
        t=type(branchValue)
        if type(branchValue) == list:
            branchValue=branchValue[0]
        key_branch='branchFor' + branchValue
        branch=u.config(key_branch,'')
        data['branch']=branch
        if branch != '':
            template_string = '{{ config.rdnattribute}}={{rdnValue}},{{ branch }},{{ config.userbase }}'
        else:
            template_string = '{{config.rdnattribute}}={{ rdnValue}},{{ config.userbase }}'
    else:
        if u.config('userbase','') != '':
            template_string ='{{config.rdnattribute}}={{ rdnValue}},{{ config.userbase }}'
        else:
            template_string = '{{config.rdnattribute}}={{ rdnValue}},{{ config.base }}'
    template = jinja2.Environment(loader=jinja2.BaseLoader()).from_string(u.config('dnTemplate',template_string))
    content = template.render(data)
    return content
def dn_superior(dn):
   tab=dn.split(',')
   tab.pop(0)
   return ','.join(tab)


def search_entity(l,entity):
    uid=u.find_key(entity,'uid')
    employeeNumber=u.find_key(entity,'employeeNumber')
    employeeType=u.find_key(entity,'employeeType')
    base=u.config('base')
    if u.config('searchFilter',''):
        data = {
            'e': u.make_entry_array(entity),
        }
        template = jinja2.Environment(loader=jinja2.BaseLoader()).from_string(u.config('searchFilter'))
        filter = template.render(data)


    else:
        if type(employeeNumber) == list:
            number=employeeNumber[0]
        else:
            number=employeeNumber
        filter='(&(employeeNumber=' + number + ')(employeeType=' + employeeType + '))'
    try:
        r=l.search_s(base,ldap.SCOPE_SUBTREE,filter)
        return r
    except ldap.LDAPError as e:
        e_dict = e.args[0]
        print(u.returncode(1, str(e_dict.get("result")) + ' ' + e_dict.get("desc") + " " + e_dict.get("info")))
        exit(1)

def upsert_entry(l,entity):
    r=search_entity(l,entity)
    action=""
    if len(r) == 0:
        # lentree n existe pas
        #creation de la liste
        entry=u.make_entry_array_without_empty(entity)
        ## Ajout objectclass
        entry['objectclass']=u.make_objectclass(entity,r)
        dn=compose_dn(entity)
        ldif = modlist.addModlist(convert_to_utf8(entry))
        try:
            action="add"
            l.add_s(dn, ldif)
        except ldap.LDAPError as e:
            e_dict = e.args[0]
            print(u.returncode(1, "add " + str(e_dict.get("result")) + ' ' + e_dict.get("desc") + " "+ e_dict.get("info",'')))
            exit(1)
    else:
        if len(r) > 1:
            print(u.returncode(1,"many identities found"))
            exit(1)
        entry=u.make_entry_array_without_empty(entity);
        entry=complete_entry(entry,r);
        dn = compose_dn(entity)
        entry['objectclass'] = u.make_objectclass(entity,r)
        entry = convert_to_utf8(entry)
        old_entry=normalize_entry(r[0][1])
        ldif = modlist.modifyModlist(old_entry,entry)

        #dn= r[0][0]
        if dn_superior(dn) == dn_superior(r[0][0]):
            try:
                action="mod"
                l.modify_s(r[0][0],ldif)
            except ldap.LDAPError as e:
                e_dict = e.args[0]
                print(u.returncode(1, 'mod ' + str(e_dict.get("result")) + ' ' + e_dict.get("desc") + " "+ e_dict.get("info",'')))
                return(1)
        else:
            ## changement du DN
            oldDn=r[0][0]
            rdn=get_rdn_attribure(oldDn)
            rdnValue=entry[rdn][0].decode('UTF-8')
            new_rdn=rdn +"="+rdnValue
            newSuperior=dn_superior(dn)
            try:
                action="rename"
                l.rename_s(oldDn,new_rdn,newsuperior=newSuperior)
            except ldap.LDAPError as e:
                e_dict = e.args[0]
                print(u.returncode(1, 'rename ' + str(e_dict.get("result")) + ' ' + e_dict.get("desc") + " "+ e_dict.get("info")))
                exit(1)
    return u.returncode(0,"Entree " + dn + " " + action)

def change_password(l,uid,old,new):
    base = u.config('base')
    filter = 'uid=' +uid
    try:
        r = l.search_s(base, ldap.SCOPE_SUBTREE, filter)
        if len(r) == 0 :
            #print(u.returncode(1, "entity not found"))
            return(1)
    except ldap.LDAPError as e:
        e_dict = e.args[0]
        #print(u.returncode(1, str(e_dict.get("result")) + ' ' + e_dict.get("desc")))
        return(1)
    ## try to change the password
    if old != '':
        try:
            l.passwd_s(r[0][0],old,new)
            return(0)
        except ldap.LDAPError as e:
            e_dict = e.args[0]
            #print(u.returncode(1, str(e_dict.get("result")) + ' ' + e_dict.get("desc") + " "+ e_dict.get("info")))
            return(1)
    else:
        ldif=[(ldap.MOD_REPLACE, 'userPassword', [new.encode('utf-8')])]
        try:
            l.modify_s(r[0][0], ldif)
            return(0)
        except ldap.LDAPError as e:
            e_dict = e.args[0]
            #print(u.returncode(1, str(e_dict.get("result")) + ' ' + e_dict.get("desc") + " "+ e_dict.get("info")))
            return(1)

def change_entity_password(l,entity):
    if 'oldPassword' in entity['payload'] and 'newPassword' in entity['payload']:
        oldPassword=entity['payload']['oldPassword']
        newPassword = entity['payload']['newPassword']
        if oldPassword != '' and newPassword != '':
            uid=u.find_key(entity,'uid')
            l=change_password(l,uid,oldPassword,newPassword)
            if l==0:
                return u.returncode(0,"Password for " + uid + " changed")
    return(u.returncode(1,"Error entity_change_password"))

def reset_entity_password(l,entity):
    if 'newPassword' in entity['payload']:
        newPassword = entity['payload']['newPassword']
        if newPassword != '':
            uid = u.find_key(entity,'uid')
            change_password(l, uid, '', newPassword)
            return u.returncode(0, "Password for " + uid + " changed")

    print(u.returncode(1, "Error entity_change_password"))
    exit(1)


def delete_entity(l,entity):
    r=search_entity(l,entity)
    if len(r) > 0:
        # trouvé
        try:
            l.delete_s(r[0][0])
            return u.returncode(0, "user : " + r[0][0] + " deleted")
        except ldap.LDAPError as e:
            e_dict = e.args[0]
            print(u.returncode(1, str(e_dict.get("result")) + ' ' + e_dict.get("desc") + " "+ e_dict.get("info")))
            exit(1)
    else:
        print(u.returncode(1, "User not found"))
        exit(1)
def complete_entry(entry,r):
    entry=normalize_entry(entry)
    for cle,valeur in r[0][1].items():
       if cle.lower() != 'objectclass' and  cle.lower() != 'jpegphoto':
            if cle.lower() not in entry:
                if type(valeur) is list:
                    for i in valeur:
                        w=type(i)
                        x=i.decode('UTF-8')
                    if len(x) == 1:
                        v=x[0]
                    else:
                        v=x
                    entry[cle.lower()]=v
    return entry

def normalize_entry(entry):
    e={}
    for cle, valeur in entry.items():
        e[cle.lower()]=valeur
    return e
def get_rdn_attribure(dn):
    dnTab=dn.split(',')
    attr=dnTab[0].split('=')
    return attr[0]

def activate_entry(l,entity,activate):
    r = search_entity(l, entity)
    if len(r) == 1:
        #entree trouvée
        disable_flag=u.config('disabledAttribute','')
        if disable_flag == "":
            return (u.returncode(1, "Configuration error : no disanleAttribute"))
        value="0"
        message="Identity disabled"
        if (activate == True):
            value=u.config('enableValue',"1")
            message = "Identity enabled"
        ldif = [(ldap.MOD_REPLACE, disable_flag, [value.encode('utf-8')])]
        try:
            l.modify_s(r[0][0], ldif)
            return(u.returncode(0, message))
        except ldap.LDAPError as e:
            e_dict = e.args[0]
            return (u.returncode(1, str(e_dict.get("result")) + ' ' + e_dict.get("desc") + " " + e_dict.get("info")))

    else:
        return (u.returncode(1,"Not Found"))