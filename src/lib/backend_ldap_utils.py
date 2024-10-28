import configparser
import json
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
        additionalFields=entity['payload']['identity']['identity']['additionalFields']['attributes']

    else:
        objectclasses=entity['payload']['additionalFields']['objectClasses']
        inetOrgPerson = entity['payload']['inetOrgPerson']
        additionalFields = entity['payload']['additionalFields']['attributes']
    #inetOrgPerson
    for k,v in inetOrgPerson.items():
        data[k]=str(v)

    for obj in objectclasses:
        #recherche si l objectclass est exclu
        exclusions=config('excludedObjectclasses').lower()
        if exclusions.find(obj.lower()) == -1:
            for k,v in additionalFields[obj].items():
                data[k]=str(v)
    return data


def make_objectclass(entity):
    data = {}
    if "identity" in entity['payload']:
        objectclasses = entity['payload']['identity']['identity']['additionalFields']['objectClasses']
    else:
        objectclasses = entity['payload']['additionalFields']['objectClasses']

    return ['top', 'inetOrgPerson'] + objectclasses


def make_entry_array_without_empty(entity):
    data={}
    data1=make_entry_array(entity)
    for k,v in data1.items():
        if str(v) != "":
            data[k]=v
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
    return rdn +'=' + rdnValue

def compose_dn(entity):
    rdn=config('rdnAttribute','uid')
    rdnValue=find_key(entity,rdn)
    branchAttr=config('branchAttr','')
    branch  = ''
    if branchAttr != '':
        branchValue=find_key(entity,branchAttr)

        match branchValue:
            case 'etd':
                branch=config('branchForEtd','')
            case 'esn':
                branch = config('branchForEsn', '')
            case 'adm':
                branch = config('branchForAdm', '')
    if branch != '':
        return rdn+ '=' + rdnValue+ ',' + branch + "," + config('userbase')
    else:
        return rdn+ '=' + rdnValue+  "," + config('userbase')

def dn_superior(dn):
   tab=dn.split(',')
   tab.pop(0)
   return ','.join(tab)


def search_entity(l,entity):
    uid=find_key(entity,'uid')
    employeeNumber=find_key(entity,'employeeNumber')
    employeeType=find_key(entity,'employeeType')
    base=config('base')
    filter='(&(employeeNumber=' + employeeNumber + ')(employeeType=' + employeeType + '))'
    try:
        r=l.search_s(base,ldap.SCOPE_SUBTREE,filter)
        return r
    except ldap.LDAPError as e:
        e_dict = e.args[0]
        print(returncode(1, str(e_dict.get("result")) + ' ' + e_dict.get("desc")))
        exit(1)

def upsert_entry(l,entity):
    r=search_entity(l,entity)
    action=""
    if len(r) == 0:
        # lentree n existe pas
        #creation de la liste
        entry=make_entry_array_without_empty(entity)
        ## Ajout objectclass
        entry['objectclass']=make_objectclass(entity)
        dn=compose_dn(entity)
        ldif = modlist.addModlist(convert_to_utf8(entry))
        try:
            action="add"
            l.add_s(dn, ldif)
        except ldap.LDAPError as e:
            e_dict = e.args[0]
            print(returncode(1, str(e_dict.get("result")) + ' ' + e_dict.get("desc")))
            exit(1)
    else:
        if len(r) > 1:
            print(returncode(1,"many identities found"))
            exit(1)
        entry=make_entry_array_without_empty(entity);
        entry['objectclass'] = make_objectclass(entity)
        entry = convert_to_utf8(entry)
        ldif = modlist.modifyModlist(r[0][1],entry)
        dn = compose_dn(entity)
        if dn == r[0][0]:
            try:
                action="mod"
                l.modify_s(dn,ldif)
            except ldap.LDAPError as e:
                e_dict = e.args[0]
                print(returncode(1, str(e_dict.get("result")) + ' ' + e_dict.get("desc")))
                exit(1)
        else:
            ## changement du DN
            oldDn=r[0][0]
            rdn=compose_rdn(entity)
            newSuperior=dn_superior(compose_dn(entity))
            try:
                action="rename"
                l.rename_s(oldDn,rdn,newSuperior)
            except ldap.LDAPError as e:
                e_dict = e.args[0]
                print(returncode(1, str(e_dict.get("result")) + ' ' + e_dict.get("desc")))
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
            print(returncode(1, str(e_dict.get("result")) + ' ' + e_dict.get("desc")))
            exit(1)
    else:
        ldif=[(ldap.MOD_REPLACE, 'userPassword', [new.encode('utf-8')])]
        try:
            l.modify_s(r[0][0], ldif)
        except ldap.LDAPError as e:
            e_dict = e.args[0]
            print(returncode(1, str(e_dict.get("result")) + ' ' + e_dict.get("desc")))
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
            print(returncode(1, str(e_dict.get("result")) + ' ' + e_dict.get("desc")))
            exit(1)


