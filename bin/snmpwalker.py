#! /usr/bin/python
'''
version = 0.2
'''
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
#from fastsnmpy import SnmpSession
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
        self.client = InfluxDBClient('localhost', 8086, 'root', '', 'snmp')
        return
    
    def getOid(self):
        uri = '/api/config_oid/?type=realtime' 
        url = self.apiurl+uri
        r = requests.get(url, timeout=10)
        data = json.loads(r.text)
        oids = {i['oid']:i['name'] for i in data}
        logging.info('[%s] Total OIDs: %s.' % (time.time(),str(len(oids.keys()))))
        return oids 
        
    def getSwitchIp(self):
        uri = '/api/device/?'+self.args 
        url = self.apiurl+uri
        r = requests.get(url, timeout=20)
        devs = json.loads(r.text)
        for i in devs:
            self.results[i['device_ip']] = defaultdict(dict)
        logging.info('[%s] Total devices: %s.' % (time.time(),str(len(devs))))
        return 

    def getIfDesc(self):
        uri = '/api/view_port/?'+self.args
        #uri = '/api/port/?devip=%s' % (','.join(self.results.keys()))
        url = self.apiurl+uri
        r = requests.get(url, timeout=10)
        data = json.loads(r.text)
        for i in data:
            try:
                self.results[i['device_ip']][i['port_ifindex']]={'ifname':i['port_name']}
            except Exception, e:
                #logging.error(e)
                pass
        return 

    ''' fastsnmpy '''
    '''
    def walker(self):
        newsession = SnmpSession (
            targets = self.results.keys(),
            oidlist = self.oids.keys(),
            maxreps = 150,
            community='public'
        )
        data = newsession.snmpwalk(workers=200)
        data = json.loads(data)
        for i in data:
            i['ifdesc'] = self.ports[i['hostname']][i['iid']]['name'] 
            i['key'] = self.oids[i['oid']]
        logging.debug('Snmp walker finished...')
        return data
    '''

    ''' netsnmp threading start '''

    def createTask(self):
        for i in itertools.product(self.results.keys(),self.oids):
            self.taskq.put(i)
        logging.info('[%s] Total tasks: %s.' % (time.time(),self.taskq.qsize()))
        #self.bar = Bar(max_value=self.taskq.qsize())
        #self.bar.cursor.clear_lines(100) 
        #self.bar.cursor.save()

        return 

    def netSnmpWalker(self,num):
        while True:
            #print self.taskq.qsize()
            try:
                host, oid=self.taskq.get(block=False) 
                oidname = self.oids[oid]
                logging.debug('%s Thread [%s] take a task : [%s-%s]. Remaining Task:[%s]' % (time.time(),num,host,oidname,self.taskq.qsize()))
                session = netsnmp.Session(
                    Community='public',
                    Version = 2, 
                    DestHost = host, 
                    Timeout = 10000000,   
                    Retries = 3,   
                )
                var_list = netsnmp.VarList()
                var_list.append(netsnmp.Varbind(oid))

                ret = session.walk(var_list)
                logging.debug('%s Thread [%s] :%s [%s] walk finished.' % (time.time(),num,host,oidname))
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

        mt = threading.Thread(target=self.resultMonitor, kwargs={})
        mt.setDaemon(True)
        mt.start()
        thread_list.append(mt)
        mt.join(200)

        for i in range(num):
            thread_list[i].join()
        logging.info('[%s] All snmp task done.'% (time.time())) 

        #pprint.pprint(self.results)
        #print json.dumps(self.results)

    def resultMonitor(self):
        iflag = 1 
        while True:
            time.sleep(1)
            json_body = []
            for k,v in self.results.items():
                for port,value in v.items():
                    try:
                        data = {
                                    "measurement": k,
                                    "tags": {
                                        "ifindex": port ,
                                        "ifname":value['ifname'],
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
                        v.pop(port)
                    except Exception,e:
                        pass
                if len(v) == 0:
                    self.results.pop(k)
                    logging.debug('[%s] %s walk done.' % (time.time(),k))
            if len(json_body) > 0:
                self.client.write_points(json_body)
                logging.info('[%s] %s ports finished.' % (time.time(),len(json_body))) 
            if len(self.results) == 0 :
                break
            logging.info('[%s] Times : %s , remains: %s' % (time.time(),iflag,len(self.results)))
            iflag += 1
        logging.info('[%s] write DB finished.' % (time.time()))


if __name__ == '__main__':
    arg=sys.argv[1]
    snmp = SnmpWalker(arg)
    #snmp = SnmpWalker('device_ip=10.149.1.1,10.135.1.1')
    snmp.createTask()
    snmp.multiWalker(200)
    #snmp.writeDB()
    #pprint.pprint(data)
