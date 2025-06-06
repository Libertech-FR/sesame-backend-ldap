import configparser
import json
from sys import stdin

__CONFIG__=configparser.RawConfigParser()


def read_config(file):
    global __CONFIG__
    __CONFIG__=configparser.RawConfigParser()
    with open(file) as f:
        file_content = '[config]\n' + f.read()
    __CONFIG__.read_string(file_content)
    return __CONFIG__

def config(key,default=''):
    c=__CONFIG__['config']
    return c.get(key,default)

def get_config():
    items=__CONFIG__.items('config')
    data = {}
    for k, v in items:
        data[k] = v
    return data

def readjsoninput():
    input = stdin.read()
    return json.loads(input)

def readjsonfile(file):
    fic=open(file,"r")
    content=fic.read()
    fic.close()
    return json.loads(content)

def returncode(code,message):
    '''
        Retourne le code au format json pour le backend
    '''
    data={}
    data['status']=code
    data['message']=message
    return json.dumps(data)

def is_backend_concerned(entity):
    br=config('branchAttr')
    entry=make_entry_array(entity);
    if config('branchAttr') in entry:
        peopleType=entry[config('branchAttr')]
    else:
        # il n y a pas de branchAttr dans le fichier de config on traitre tout
        return True
    x=config('backendFor')
    if config('backendFor','') == '':
        return True
    listBackend=config('backendFor').split(',')
    if type(peopleType) is list:
        for v in peopleType:
          if v in listBackend :
             return True
    else:
        if peopleType in listBackend:
            return True

    return False

def find_key(element, key):
    '''
    Check if *keys (nested) exists in `element` (dict).
    '''
    r=_finditem(element,key)
    if r is None:
        return ""
    else:
        return r

def _finditem(obj, key):
    if key in obj: return obj[key]
    for k, v in obj.items():
        if isinstance(v,dict):
            item = _finditem(v, key)
            if item is not None:
                return item

def make_entry_array(entity):
    data = {}
    if "identity" in entity['payload']:
        objectclasses = entity['payload']['identity']['identity']['additionalFields']['objectClasses']
        inetOrgPerson = entity['payload']['identity']['identity']['inetOrgPerson']
        addFieldsDict = entity['payload']['identity']['identity']['additionalFields']
        if 'attributes' in addFieldsDict:
            additionalFields = entity['payload']['identity']['identity']['additionalFields']['attributes']
        else:
            additionalFields = {}

    else:
        objectclasses = entity['payload']['additionalFields']['objectClasses']
        inetOrgPerson = entity['payload']['inetOrgPerson']
        additionalFields = entity['payload']['additionalFields']['attributes']
    # inetOrgPerson
    for k, v in inetOrgPerson.items():
        if type(v) is int:
            v = str(v)
        data[k] = v

    for obj in objectclasses:
        # recherche si l objectclass est exclu
        exclusions = config('excludedObjectclasses')
        if exclusions.find(obj.lower()) == -1:
            if obj in additionalFields.keys():
                for k, v in additionalFields[obj].items():
                    if type(v) is int:
                        v = str(v)
                    data[k] = v
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
    exclusions = config('excludedObjectclasses')
    for k in new_objectclasses:
        if k.lower() not in objectclasses:
            if exclusions.find(k.lower()) == -1:
                objectclasses.append(k)

    return objectclasses

def make_entry_array_without_empty(entity):
    data={}
    data1=make_entry_array(entity)
    for k,v in data1.items():
        if str(v) != "":
            data[k]=v
    return data
