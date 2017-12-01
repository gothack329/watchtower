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

httplib.HTTPConnection.debuglevel = 1

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
    
    interface = []
    if_url = '/imcrs/plat/res/device/%s/interface/?size=2000'
    for i in data[key]:
        req = requests.get(imc_url+if_url % (i['id']), auth=auth, headers=headers, timeout=10)
        data2 = json.loads(req.text)
        try:
            interface.append({i['ip']:data2['interface']})
        except Exception,e:
            print data2
    return interface
                
    

def sync2db(list):
    
    con = mysql.connect(user = 'username',db='nms',passwd = 'password',host='localhost')
    cur = con.cursor()
    for i in list :
        for device,interfaces in i.items():
            for interface in interfaces:
                ifindex = interface['ifIndex']
                ifdesc = interface['ifAlias']
                ifname = interface['ifDescription']
                ifspeed = interface['ifspeed']
                #status = i['operationStatusDesc']
                counter = cur.execute('select * from port where device_ip="%s" and ifindex="%s" '%(device,ifindex))
                if counter == 0:
                    print "insert:",device,ifname
                    sql = 'insert into port(name, ifindex, ifdesc, device_ip, speed ) values ("%s","%s","%s","%s","%s")'% ( ifname,ifindex,ifdesc,device,ifspeed)
                else:
                    print "update:",device,ifname
                    sql = 'update port set name="%s", speed="%s", ifdesc="%s" where device_ip="%s" and ifindex="%s"' % ( ifname,ifspeed,ifdesc,device,ifindex)
                try:
                    cur.execute(sql)
                except Exception,e:
                    print e
                    print sql
    con.commit()
    cur.close()
    con.close()


if __name__ == '__main__':
    data = imc()
    #parseData(data)
    sync2db(data)

