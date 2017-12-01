#! /usr/bin/python
import os
import threading
import logging
import Queue
import itertools
from collections import defaultdict
import requests
import json
import pprint
import sys
import MySQLdb as mysql
from fastsnmpy import SnmpSession
import json
import netsnmp
from influxdb import InfluxDBClient
import time

#from progressive.bar import Bar

#try:
#    import httplib
#except ImportError:
#    import http.client as httplib

#httplib.HTTPConnection.debuglevel = 1
logging.basicConfig(level=logging.INFO)  


class SnmpWalker(object):
    def __init__(self, args):
        self.apiurl = ''
        self.db = 'localhost:8086'
        self.args = args
        #self.devs = self.getSwitchIp()
        #self.ports = self.getIfDesc()
        self.oids = self.getOid()
        self.taskq = Queue.Queue()
        #self.rq = Queue.Queue()
        #self.results = [] 
        self.results = {} 
        self.getSwitchIp()
        self.getIfDesc()
        self.client = InfluxDBClient('localhost', 8086, 'root', '', 'snmpnew')
        return
    
    def getOid(self):
        uri = '/api/config_oid/?type=realtime' 
        url = self.apiurl+uri
        r = requests.get(url, timeout=10)
        data = json.loads(r.text)
        oids = {i['oid']:i['name'] for i in data}
        logging.info('[%s] Total OIDs: %s.' % (time.strftime('%Y-%m-%d %H:%M:%S'),str(len(oids.keys()))))
        return oids 
        
    def getSwitchIp(self):
        uri = '/api/view_portgroup/?limit=none&'+self.args 
        url = self.apiurl+uri
        r = requests.get(url, timeout=10)
        devs = json.loads(r.text)
        for i in devs:
            self.results[i['device_ip']] = defaultdict(dict)
        logging.info('[%s] Total devices: %s.' % (time.strftime('%Y-%m-%d %H:%M:%S'),str(len(devs))))
        return 

    def getIfDesc(self):
        uri = '/api/view_portgroup/?limit=none&'+self.args
        url = self.apiurl+uri
        r = requests.get(url, timeout=20)
        data = json.loads(r.text)
        for i in data:
            try:
                self.results[i['device_ip']][i['port_ifindex']]={'ifname':i['port_name'],'groupname':i['portgroup_name'],'groupcode':i['codename']}
            except Exception, e:
                pass
        return 

    ''' netsnmp threading start '''

    def createTask(self):
        #pprint.pprint(json.loads(json.dumps(self.results)))
        for i in itertools.product(self.results.keys(),self.oids):
            for j in self.results[i[0]].keys():
                a=(i[0],i[1]+'.'+j)
            	self.taskq.put(a)
        logging.info('[%s] Total tasks: %s.' % (time.strftime('%Y-%m-%d %H:%M:%S'),self.taskq.qsize()))
        #self.bar = Bar(max_value=self.taskq.qsize())
        #self.bar.cursor.clear_lines(100) 
        #self.bar.cursor.save()

        return 

    def netSnmpWalker(self,num):
        while True:
            #print self.taskq.qsize()
            try:
                host, oid=self.taskq.get(block=False) 
                oidname = self.oids['.'.join(oid.split('.')[:-1])]
                logging.debug('%s Thread [%s] take a task : [%s-%s]. Remaining Task:[%s]' % (time.strftime('%Y-%m-%d %H:%M:%S'),num,host,oidname,self.taskq.qsize()))
                session = netsnmp.Session(
                    Community='public',
                    Version = 2, 
                    DestHost = host, 
                    Timeout = 10000000,   
                    Retries = 3,   
                )
                var_list = netsnmp.VarList()
                var_list.append(netsnmp.Varbind(oid))

                ret = session.get(var_list)
                logging.debug('%s Thread [%s] :%s [%s] walk finished.' % (time.strftime('%Y-%m-%d %H:%M:%S'),num,host,oidname))
                #self.bar.cursor.restore()
                #self.bar.draw(value=self.taskq.qsize())

                for i in var_list:
                    try:
                        self.results[host][i.iid][i.tag]=i.val
                        #self.results.append({'host':host,'oid':oid,'ifdesc':self.ports[host][i.iid]['name'],'tag':i.tag,'ifindex':i.iid,'value':i.val})
                    except Exception, e:
                        #logging.error(e)
                        pass
            except Queue.Empty:
                break
    
    def multiWalker(self,num=100):
        thread_list = []

        for i in range(num):
            t = threading.Thread(target=self.netSnmpWalker, kwargs={'num':i})
            t.setDaemon(True)
            t.start()
            thread_list.append(t)
        #time.sleep(10)

        for i in range(num):
            thread_list[i].join()

        #pprint.pprint(self.results)

    def writeDB(self):
        #pprint.pprint(json.loads(json.dumps(self.results)))
        json_body = []
        for k,v in self.results.items():
            for port,value in v.items():
                try:
                    data = {
                                "measurement": value['groupname'],
                                "tags": {
                                    "ifindex": port ,
                                    "ifname":value['ifname'],
                                    "device_ip":k,
                                },
    
                                "fields": {
                                    'ifHCInOctets':int(value['ifHCInOctets']),
                                    'ifHCOutOctets':int(value['ifHCOutOctets']),
                                    'ifInErrors':int(value['ifInErrors']),
                                    'ifInUcastPkts':int(value['ifInUcastPkts']),
                                    'ifOperStatus':int(value['ifOperStatus']),
                                    'ifOutErrors':int(value['ifOutErrors']),
                                    'ifOutUcastPkts':int(value['ifOutUcastPkts'])
                                }
                            }
                    json_body.append(data)
                except Exception,e:
                    print e
                    print k,value
        self.client.write_points(json_body)
        logging.info('[%s] Write DB finished.' % (time.strftime('%Y-%m-%d %H:%M:%S')))


if __name__ == '__main__':
    snmp = SnmpWalker('')
    #snmp = SnmpWalker('device_role=tor&device_ip=10.136.1.34,10.136.1.36')
    snmp.createTask()
    snmp.multiWalker(1000)
    snmp.writeDB()
    #pprint.pprint(data)

