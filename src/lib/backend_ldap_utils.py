import configparser
import json

import jinja2
import ldap
import ldap.modlist as modlist
from sys import stdin

__CONFIG__=configparser.RawConfigParser()


def readconfig(file):
    with open(file) as f:
        file_content = '[config]\n' + f.read()
    __CONFIG__.read_string(file_content)

def config(key,default=''):
    c=__CONFIG__['config']
    return c.get(key,default)

def get_config():
    items=__CONFIG__.items('config')
    data = {}
    for k, v in items:
        data[k] = v
    return data
def connect_ldap(url,dn,password):
    try:
        l=ldap.initialize(url)
        l.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_ALLOW)
        l.simple_bind_s(dn,password)
        return l
    except ldap.LDAPError as e:
        e_dict = e.args[0]
        print(returncode(1, str(e_dict.get("result")) + ' ' + e_dict.get("desc")))
        exit(1)

def readjsoninput():
    input = stdin.read()
    return json.loads(input)

def returncode(code,message):
    '''
        Retourne le code au format json pour le backend
    '''
    data={}
    data['status']=code
    data['message']=message
    return json.dumps(data)

def is_backend_concerned(entity):
    peopleType=find_key(entity,config('branchAttr'))
    if type(peopleType) is list:
        listBackend=config('backendFor')
        for v in peopleType:
          peopleType=v
          if (listBackend.find(peopleType) == -1):
             return False
    return True
def find_key(element, key):
    '''
    Check if *keys (nested) exists in `element` (dict).
    '''
    return _finditem(element,key)

def _finditem(obj, key):
    if key in obj: return obj[key]
    for k, v in obj.items():
        if isinstance(v,dict):
            item = _finditem(v, key)
            if item is not None:
                return item

def make_entry_array(entity):
    data={}
    if "identity" in entity['payload']:
        objectclasses = entity['payload']['identity']['identity']['additionalFields']['objectClasses']
        inetOrgPerson=entity['payload']['identity']['identity']['inetOrgPerson']
        addFieldsDict=entity['payload']['identity']['identity']['additionalFields']
        if 'attributes' in addFieldsDict:
            additionalFields=entity['payload']['identity']['identity']['additionalFields']['attributes']
        else:
            additionalFields={}

    else:
        objectclasses=entity['payload']['additionalFields']['objectClasses']
        inetOrgPerson = entity['payload']['inetOrgPerson']
        additionalFields = entity['payload']['additionalFields']['attributes']
    #inetOrgPerson
    for k,v in inetOrgPerson.items():
        if type(v) is int:
            v=str(v)
        data[k.lower()]=v

    for obj in objectclasses:
        #recherche si l objectclass est exclu
        exclusions=config('excludedObjectclasses').lower()
        if exclusions.find(obj.lower()) == -1:
            if obj in additionalFields.keys():
                for k,v in additionalFields[obj].items():
                    if type(v) is int:
                        v = str(v)
                    data[k.lower()]=v
    return data


def make_objectclass(entity,entry):
    data = {}
    objectclasses=[]
    if entry:
        current=entry[0][1]['objectClass']
        for k in current:
            x=k.decode('UTF-8').lower()
            objectclasses.append(x)
    else:
        objectclasses.append('top')
        objectclasses.append('inetOrgPerson')
    if "identity" in entity['payload']:
        new_objectclasses = entity['payload']['identity']['identity']['additionalFields']['objectClasses']
    else:
        new_objectclasses = entity['payload']['additionalFields']['objectClasses']

    for k in new_objectclasses:
        if k.lower() not in objectclasses:
            objectclasses.append(k)

    return objectclasses


def make_entry_array_without_empty(entity):
    data={}
    data1=make_entry_array(entity)
    for k,v in data1.items():
        if type(v) is list and len(k) > 0:
            l=[]
            for i in v:
                if i != '':
                    l.append(i)
            if len(l)>0:
                data[k.lower()] = l
        if type(v) is int:
            v=str(v)
        if type(v) is str and str(v) != "":
            data[k.lower()]=v
    return data

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
    rdn = config('rdnAttribute', 'uid')
    rdnValue = find_key(entity, rdn)
    return rdn + '=' + rdnValue
def compose_dn(entity):
    """Compose the DN of a identity"""
    rdn = config('rdnAttribute', 'uid')
    rdnValue=find_key(entity,rdn)
    data = {
        'e': make_entry_array(entity),
        'config': get_config(),
        'rdnValue': rdnValue
    }

    x=type(rdnValue)
    if rdnValue is None:
        rdnValue='test'
    branchAttr=config('branchAttr','')
    data['rdnValue']=rdnValue
    if branchAttr != '':
        branchValue=find_key(entity,branchAttr)
        t=type(branchValue)
        if type(branchValue) == list:
            branchValue=branchValue[0]
        key_branch='branchFor' + branchValue
        branch=config(key_branch,'')
        data['branch']=branch
        if branch != '':
            template_string = '{{ config.rdnattribute}}={{rdnValue}},{{ branch }},{{ config.userbase }}'
        else:
            template_string = '{{config.rdnattribute}}={{ rdnValue}},{{ config.userbase }}'
    else:
        if config('userbase','') != '':
            template_string ='{{config.rdnattribute}}={{ rdnValue}},{{ config.userbase }}'
        else:
            template_string = '{{config.rdnattribute}}={{ rdnValue}},{{ config.base }}'
    template = jinja2.Environment(loader=jinja2.BaseLoader()).from_string(config('dnTemplate',template_string))
    content = template.render(data)
    return content
def dn_superior(dn):
   tab=dn.split(',')
   tab.pop(0)
   return ','.join(tab)


def search_entity(l,entity):
    uid=find_key(entity,'uid')
    employeeNumber=find_key(entity,'employeeNumber')
    employeeType=find_key(entity,'employeeType')
    base=config('base')
    if config('searchFilter',''):
        data = {
            'e': make_entry_array(entity),
        }
        template = jinja2.Environment(loader=jinja2.BaseLoader()).from_string(config('searchFilter'))
        filter = template.render(data)


    else:
        filter='(&(employeeNumber=' + employeeNumber + ')(employeeType=' + employeeType + '))'
    try:
        r=l.search_s(base,ldap.SCOPE_SUBTREE,filter)
        return r
    except ldap.LDAPError as e:
        e_dict = e.args[0]
        print(returncode(1, str(e_dict.get("result")) + ' ' + e_dict.get("desc") + " " + e_dict.get("info")))
        exit(1)

def upsert_entry(l,entity):
    r=search_entity(l,entity)
    action=""
    if len(r) == 0:
        # lentree n existe pas
        #creation de la liste
        entry=make_entry_array_without_empty(entity)
        ## Ajout objectclass
        entry['objectclass']=make_objectclass(entity,r)
        dn=compose_dn(entity)
        ldif = modlist.addModlist(convert_to_utf8(entry))
        try:
            action="add"
            l.add_s(dn, ldif)
        except ldap.LDAPError as e:
            e_dict = e.args[0]
            print(returncode(1, "add " + str(e_dict.get("result")) + ' ' + e_dict.get("desc") + " "+ e_dict.get("info",'')))
            exit(1)
    else:
        if len(r) > 1:
            print(returncode(1,"many identities found"))
            exit(1)
        entry=make_entry_array_without_empty(entity);
        entry=complete_entry(entry,r);

        entry['objectclass'] = make_objectclass(entity,r)
        entry = convert_to_utf8(entry)
        old_entry=normalize_entry(r[0][1])
        ldif = modlist.modifyModlist(old_entry,entry)
        dn = compose_dn(entity)
        #dn= r[0][0]
        if dn_superior(dn) == dn_superior(r[0][0]):
            try:
                action="mod"
                l.modify_s(r[0][0],ldif)
            except ldap.LDAPError as e:
                e_dict = e.args[0]
                print(returncode(1, 'mod ' + str(e_dict.get("result")) + ' ' + e_dict.get("desc") + " "+ e_dict.get("info",'')))
                exit(1)
        else:
            ## changement du DN
            oldDn=r[0][0]
            rdn=get_rdn_attribure(oldDn)
            rdnValue=entry[rdn][0].decode('UTF-8')
            new_rdn=rdn +"="+rdnValue

            newSuperior=dn_superior(compose_dn(entity))
            try:
                action="rename"
                l.rename_s(oldDn,new_rdn,newsuperior=newSuperior)
            except ldap.LDAPError as e:
                e_dict = e.args[0]
                print(returncode(1, 'rename ' + str(e_dict.get("result")) + ' ' + e_dict.get("desc") + " "+ e_dict.get("info")))
                exit(1)
    return returncode(0,"Entree " + dn + " " + action)

def change_password(l,uid,old,new):
    base = config('base')
    filter = 'uid=' +uid
    try:
        r = l.search_s(base, ldap.SCOPE_SUBTREE, filter)
    except ldap.LDAPError as e:
        e_dict = e.args[0]
        print(returncode(1, str(e_dict.get("result")) + ' ' + e_dict.get("desc")))
        exit(1)
    ## try to change the password
    if old != '':
        try:
            l.passwd_s(r[0][0],old,new)
        except ldap.LDAPError as e:
            e_dict = e.args[0]
            print(returncode(1, str(e_dict.get("result")) + ' ' + e_dict.get("desc") + " "+ e_dict.get("info")))
            exit(1)
    else:
        ldif=[(ldap.MOD_REPLACE, 'userPassword', [new.encode('utf-8')])]
        try:
            l.modify_s(r[0][0], ldif)
        except ldap.LDAPError as e:
            e_dict = e.args[0]
            print(returncode(1, str(e_dict.get("result")) + ' ' + e_dict.get("desc") + " "+ e_dict.get("info")))
            exit(1)

def change_entity_password(l,entity):
    if 'oldPassword' in entity['payload'] and 'newPassword' in entity['payload']:
        oldPassword=entity['payload']['oldPassword']
        newPassword = entity['payload']['newPassword']
        if oldPassword != '' and newPassword != '':
            uid=find_key(entity,'uid')
            change_password(l,uid,oldPassword,newPassword)
            return returncode(0,"Password for " + uid + "changed")

    print(returncode(1,'Error entity_change_password'))
    exit(1)


def reset_entity_password(l,entity):
    if 'newPassword' in entity['payload']:
        newPassword = entity['payload']['newPassword']
        if newPassword != '':
            uid = find_key(entity,'uid')
            change_password(l, uid, '', newPassword)
            return returncode(0, "Password for " + uid + "changed")

    print(returncode(1, 'Error entity_change_password'))
    exit(1)


def delete_entity(l,entity):
    r=search_entity(l,entity)
    if len(r) > 0:
        # trouvé
        try:
            l.delete_s(r[0][0])
            return returncode(0, "user : " + r[0][0] + " deleted")
        except ldap.LDAPError as e:
            e_dict = e.args[0]
            print(returncode(1, str(e_dict.get("result")) + ' ' + e_dict.get("desc") + " "+ e_dict.get("info")))
            exit(1)
    else:
        print(returncode(1, "User not found"))
        exit(1)
def complete_entry(entry,r):
    for cle,valeur in r[0][1].items():
       if cle.lower() != 'objectclass' and  cle.lower() != 'jpegphoto':
            if cle not in entry:
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