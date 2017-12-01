#! /usr/bin/python
import os
import logging
import requests
import json
import pprint
from requests.auth import HTTPDigestAuth
import sys
import MySQLdb as mysql
try:
    import httplib
except ImportError:
    import http.client as httplib

#httplib.HTTPConnection.debuglevel = 1

logging.basicConfig(level=logging.DEBUG)  

def imc():

    imc_url = ''
    api_url = '/imcrs/plat/res/device?size=2000'
    
    key = api_url.split('?')[0].split('/')[-1]
    
    username = 'admin'
    password = 'admin'
    
    auth = HTTPDigestAuth(username, password)
    headers = {'Accept': 'application/json'}
    
    r = requests.get(imc_url+api_url, auth=auth, headers=headers, timeout=10)
    
    data = json.loads(r.text)
    
    try:
        return data[key]
    except:
        return data
    
def parseData(list):
    result = []
    for i in list:
        line = '%s, %s, %s, %s' % (i['ip'],i['symbolName'],i['typeName'],i['contact'].upper())
        os.system('echo "' + str(line) +'" >> device.all')
        result.append(line)
    return result

def sync2db(list):
    
    con = mysql.connect(user = 'username',db='nms',passwd = 'password',host='localhost')
    cur = con.cursor()
    for i in list :
        imcid = i['id']
        ip = i['ip']
        role = i['contact']
        name = i['sysName']
        idc = i['location']
        model = i['typeName']
        vendor = model.split()[0]
        sysdesc = i['sysDescription']
            
        counter = cur.execute('select * from device where device_ip="%s"'%(ip))
        if counter == 0:
            print "insert:",ip,name,model
            sql = 'insert into device(imcid, device_ip, device_role, name, idc, model, sysdesc, vendor ) values ("%s","%s","%s","%s","%s","%s","%s","%s")'% ( imcid, ip,role,name,idc,model.upper(),sysdesc.strip(),vendor.upper())
        else:
            print "update:",ip,name,model
            sql = 'update device set imcid="%s", device_role="%s", name="%s", idc="%s", model="%s", sysdesc="%s", vendor="%s"  where device_ip="%s"' % ( imcid, role,name,idc,model.upper(),sysdesc.strip(),vendor.upper(),ip)
        try:
            cur.execute(sql)
        except Exception,e:
            print e
            print sql
    con.commit()
    cur.close()
    con.close()


if __name__ == '__main__':
    os.system('rm -rf ./device.all')
    data = imc()
    parseData(data)
    sync2db(data)

