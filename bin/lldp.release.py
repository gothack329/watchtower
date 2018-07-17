#!/usr/bin/env python
# -*- coding: UTF-8 -*-
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

reload(sys)
sys.setdefaultencoding('utf-8')

logging.basicConfig(level=logging.INFO)  


class LldpWalker(object):
    def __init__(self):
        self.apiurl = 'http://localhost'
        self.oids = defaultdict(dict) 
        self.taskq = Queue.Queue()
        self.devices = defaultdict(dict) 
        self._devices = defaultdict(dict) 
        self.ports = defaultdict(dict) 
        self._ports = defaultdict(dict) 
        self.mysql = mysql.connect(user='username',db='nms',passwd ='password',host='localhost')
        self.conn = [] 
        return
    
    def getOids(self):
        uri = '/api/config_oid/?type=lldp' 
        url = self.apiurl+uri
        r = requests.get(url, timeout=20)
        data = json.loads(r.text)
        self.oids = {i['name']:i['oid'] for i in data}
        logging.info('[%s] Total OIDs: %s.' % (time.time(),str(len(self.oids.keys()))))
        return 
        
    def getDevices(self):
        uri = '/api/device/?limit=none'
        #uri = '/api/device/?device_role=dci-router,pod-core'
        #uri = '/api/device/?device_role=dci-router&device_ip=192.168.100.39,192.168.100.34'
        url = self.apiurl+uri
        r = requests.get(url, timeout=20)
        devs = json.loads(r.text)
        for i in devs:
            self.devices[i['device_ip']] = {'name':i['name'],'vendor':i['vendor']}
            self._devices[i['name']] = i['device_ip'] 
        logging.info('[%s] Total devices: %s.' % (time.time(),str(len(devs))))
        return  

    def getPorts(self):
        uri = '/api/view_port/?limit=none'
        #uri = '/api/port/?devip=%s' % (','.join(self.results.keys()))
        url = self.apiurl+uri
        r = requests.get(url, timeout=20)
        data = json.loads(r.text)
        for i in data:
            try:
                self.ports[i['device_ip']+'_'+i['port_ifindex']]={'id':i['port_id']}
                self._ports[i['device_name']+'_'+i['port_name']]={'id':i['port_id']}
            except Exception, e:
                #logging.error(e)
                pass
        return 


    ''' netsnmp threading start '''
    def createTask(self):
        for i in self.devices.keys():
            self.taskq.put((i,self.devices[i]['vendor']))
        logging.info('[%s] Total tasks: %s.' % (time.time(),self.taskq.qsize()))
        return 

    def netSnmpWalker(self,num):
        while True:
            try:
                host,vendor=self.taskq.get(block=False)  
                logging.debug('%s Thread [%s] take a task : [%s]. Remaining Task:[%s]' % (time.time(),num,host,self.taskq.qsize()))
            except Queue.Empty:
                break
            session = netsnmp.Session(
                Community='public',
                Version = 2, 
                DestHost = host, 
                Timeout = 1000000 * 6,   
                Retries = 3,   
            )

            oid0 = 'dot1dBasePortIfIndex'
            oid1 = 'lldpRemSysName'
            oid2 = 'lldpRemPortId' 
            
            if vendor.lower() == 'h3c' or vendor.lower() == 'huawei':
                # step 1: oid0 , for h3c
                var_list = netsnmp.VarList()
                var_list.append(netsnmp.Varbind(self.oids[oid0]))

                ret = session.walk(var_list)
                portlist = {}

                for i in var_list:
                    portindex = i.tag.split('.')[-1]
                    ifindex = i.val
                    portlist[portindex]=ifindex
                    
                tmplist =[int(x) for x in  portlist.keys()]
                tmplist.sort()

                if vendor.lower() == 'huawei':
                    # fix huawei lldp bug
                    for i in range(tmplist[0],tmplist[-1]):
                        if portlist.has_key(str(i)):
                            pass
                        else:
                            portlist[str(i)] = str(i-tmp[0]+tmp[1])
                        tmp = (i,int(portlist[str(i)])) 
                        
            else:
                var_list = netsnmp.VarList()
                var_list.append(netsnmp.Varbind('.1.3.6.1.2.1.2.2.1.2')) # ifdesc

                ret = session.walk(var_list)
                portlist = {}

                for i in var_list:
                    portindex = i.iid
                    portlist[portindex] = portindex


            # step 2: oid1
            var_list = netsnmp.VarList()
            var_list.append(netsnmp.Varbind(self.oids[oid1]))

            ret = session.walk(var_list)
            local_ip = host 
            local_host = self.devices[host]['name'] 
            lldp = {}

            for i in var_list:
                remote_host = i.val
                try:
                    local_ifindex = portlist[i.tag.split('.')[-2]]
                    if remote_host not in self._devices.keys() or len(remote_host) == 0:
                        logging.info("Remote host [%s] doesn't in the host list." % remote_host)
                        continue
                    lldp[local_ifindex]={'aid':None,'zid':None,'remname':None,'remport':None}
                    lldp[local_ifindex]['aid'] = int(self.ports[local_ip+'_'+local_ifindex]['id']) 
                    lldp[local_ifindex]['remname'] = remote_host
                except Exception,e: 
                #    logging.error('145 '+str(e))
                #    pass
                    #logging.error(host,vendor,i.tag,str(e))
                    print host,vendor,i.tag,remote_host


            # step 3: oid2
            var_list = netsnmp.VarList()
            var_list.append(netsnmp.Varbind(self.oids[oid2]))

            ret = session.walk(var_list)
            logging.debug('%s Thread [%s] :%s walk finished.' % (time.time(),num,host))
            for i in var_list:
                remote_ifname = i.val
                try:
                    local_ifindex = portlist[i.tag.split('.')[-2]]
                except:
                    continue
                if not lldp.has_key(local_ifindex):
                    logging.info("Remote interface [%s] doesn't in the port list. " % remote_ifname)
                    continue

                if remote_ifname.startswith('BE'):
                    # for cisco asr9k 
                    continue
                elif remote_ifname.startswith('Ethernet') or remote_ifname.startswith('Ten-GigabitEthernet') or remote_ifname.startswith('FortyGigE') or remote_ifname.startswith('HundredGigE'):
                    pass
                else:
                    remote_ifname = remote_ifname.replace('Hu','HundredGigE') 
                    remote_ifname = remote_ifname.replace('Eth','Ethernet')
                    remote_ifname = remote_ifname.replace('Te','TenGigE')
                    remote_ifname = remote_ifname.replace('Fo','FortyGigE')
                lldp[local_ifindex]['remport'] = remote_ifname 
                try:
                    lldp[local_ifindex]['zid'] = int(self._ports[lldp[local_ifindex]['remname']+'_'+lldp[local_ifindex]['remport']]['id'])
                except Exception,e:
                    print len(lldp[local_ifindex]['remname'])
                #    #logging.error('176 '+str(e))
                #    print host,vendor,i.tag,remote_ifname
                #    #logging.error(host,vendor,i.tag,str(e))
                #    pass
            
            for k,v in lldp.items():
                if v['zid']==None:
                    pass
                else:
                    self.conn.append(v)
            

    def getRemoteIfindex(self,ip,ifname):
        for k,v in self.ports.items():
           if v['ifname'] == ifname.strip() and v['ip'] == ip:
               return k.split('_')[1]


    def write(self):
        cur = self.mysql.cursor()
        insertcount = 0
        updatecount = 0
        for i in self.conn:
            ids = [i['aid'],i['zid']]
            ids.sort()
            sql = 'insert into lldpid(aid,zid) values (%d,%d)' % tuple(ids) 
            try:
                cur.execute(sql)
                insertcount+=1
            except Exception,e:
                logging.error('205 '+str(e))
                try:
                    sql = 'update lldpid set mtime="%s" where aid="%d" and zid="%d"' % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),ids[0],ids[1]) 
                    cur.execute(sql)
                    updatecount+=1
                except:
                    print sql
                #print e

        logging.info('Insert: '+str(insertcount))
        logging.info('Update: '+str(updatecount))
        
        self.mysql.commit()
        cur.close()
        self.mysql.close()
        
    
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
        logging.info('[%s] All snmp task done.'% (time.time())) 


    def main(self):
        self.getOids()
        self.getDevices()
        self.getPorts()
        #print json.dumps(self.devices)
        self.createTask()
        self.multiWalker(1000)
        print len(self.conn)
        #print json.dumps(self.conn)
        self.write()

        #self.createTask(self.oids['lldpRemManAddrIfSubtype'])
        #self.multiWalker(100)
        #pprint.pprint(json.loads(json.dumps(self.devices)))
        #pprint.pprint(json.loads(json.dumps(self.ports)))


if __name__ == '__main__':
    lldp = LldpWalker()
    lldp.main()

