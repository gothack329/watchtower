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
sys.setdefaultencoding('utf8')


#try:
#    import httplib
#except ImportError:
#    import http.client as httplib

#httplib.HTTPConnection.debuglevel = 1
logging.basicConfig(level=logging.INFO)  


class TfcAlert(object):
    def __init__(self, args):
        self.apiurl = ''
        self.db = 'locahost:8086'
        self.client = InfluxDBClient('localhost', 8086, 'root', '', 'snmpnew')
        self.args = args
        self.ports = self.getPortGroup()
        self.threshold = self.getThreshold()
        return

    
    def getPortGroup(self):
        results = defaultdict(dict) 
        uri = '/api/view_portgroup/?'+self.args 
        url = self.apiurl+uri
        r = requests.get(url, timeout=10)
        ports = json.loads(r.text)
        for i in ports:
            results[i['portgroup_name']] = [] 
        for i in ports:
            if i['port_tag'] and 'ign' in i['port_tag'].split(','):
                pass
                #print i['portgroup_name']
            else:
                results[i['portgroup_name']].append((i['device_ip'],i['port_name']))
        for k,v in results.items():
            if len(v) == 0:
                results.pop(k)

        #logging.info('[%s] Total devices: %s.' % (time.time(),str(len(devs))))
        return results 


    def getThreshold(self):
        threshold = self.client.query("select * from threshold where time>now()-10m and time<now() TZ('Asia/Shanghai')")
        ''' returns a dict :threshold.raw['series'][0] 
            {u'columns': [u'time',
               u'device_ip',
               u'ifHCInOctets',
               u'ifHCOutOctets',
               u'ifname',
               u'portgroup'],
              u'name': u'threshold',
              u'values': [[u'2017-10-17T05:15:00Z',
                u'10.18.64.54',
                1996960352.5777779,
                3017049524.5333333,
                u'Ten-GigabitEthernet1/0/52',
                u'\u516c\uff09'],]}
        '''
        data = {}
        for i in threshold.raw['series'][0]['values']:
            t,ip,intfc,outtfc,ifname,portgroup = i
            if data.has_key(portgroup):
                if data[portgroup].has_key(ip+','+ifname):
                    pass
                else:
                    data[portgroup][ip+','+ifname]=defaultdict(dict)
            else:
                data[portgroup]=defaultdict(dict)
                data[portgroup][ip+','+ifname]=defaultdict(dict)
            data[portgroup][ip+','+ifname][t]={'in':intfc,'out':outtfc}
                        
        return data 


    def getTFC(self):
        result = [] 
        
        for group,ipif in self.ports.items():
            tfc = self.client.query('''SELECT 8*difference(mean(ifHCOutOctets))/elapsed(mean(ifHCOutOctets),1s),8*difference(mean(ifHCInOctets))/elapsed(mean(ifHCInOctets),1s)  FROM /^%s$/ where time>now()-4m and time<now() group by time(1m),"ifname","device_ip" TZ('Asia/Shanghai')''' % group) 
            result += tfc.raw['series']
        
        # 组装数据，计算组合流量
        data = defaultdict(dict) 
        for i in result:
            for j in i['values']:
                if data[i['name']].has_key('group,group'):
                    pass
                else:
                    data[i['name']]['group,group'] = defaultdict(dict)
                if data[i['name']]['group,group'][j[0]].has_key('in'):
                    pass 
                else:
                    data[i['name']]['group,group'][j[0]]={'in':[],'out':[]}
                data[i['name']]['group,group'][j[0]]['in'].append(j[2]) 
                data[i['name']]['group,group'][j[0]]['out'].append(j[1]) 

        for k in data:
            for t,inout in data[k]['group,group'].items():
                inout['in'] = sum(inout['in'])
                inout['out'] = sum(inout['out'])
        
        # 组装单接口流量 
        for i in result:
            if data[i['name']].has_key(i['tags']['device_ip']+','+i['tags']['ifname']):
                pass
            else:
                data[i['name']][i['tags']['device_ip']+','+i['tags']['ifname']]=defaultdict(dict)
    
            for j in i['values']:
                data[i['name']][i['tags']['device_ip']+','+i['tags']['ifname']][j[0]]={'in':j[2],'out':j[1]}

        #pprint.pprint(json.loads(json.dumps(data)))
        '''
        data :
        {portgroup:{'ip,ifname':{time:{in:xxx,out:xxx}}}}
        '''
        return data 

    def overthreshold(self,tfcdata,maximum=1.2,minimum=0.5):
        result = [] 
        for portgroup,v1 in tfcdata.items():
            for ipif,v2 in v1.items():
                intfcmax = []
                outtfcmax = []
                intfcmin = []
                outtfcmin = []
                for t,inout in v2.items():
                    xin = self.threshold[portgroup][ipif][self.threshold_time(t)]['in'] +1
                    xout = self.threshold[portgroup][ipif][self.threshold_time(t)]['out'] +1
                    inmax = xin * ( maximum+700000000/xin )
                    inmin = xin * ( minimum-10000000/xin)
                    outmax = xout * ( maximum+700000000/xout )
                    outmin = xout * ( minimum-10000000/xout)
                    if inout['in'] > inmax:
                        intfcmax.append('warn')
                        intfcmin.append('normal')
                    elif inout['in'] < inmin:
                        intfcmin.append('warn')
                        intfcmax.append('normal')
                    else:
                        intfcmax.append('normal')
                        intfcmin.append('normal')
                    if inout['out'] > outmax:
                        outtfcmax.append('warn')
                        outtfcmin.append('normal')
                    elif inout['out'] < outmin:
                        outtfcmin.append('warn')
                        outtfcmax.append('normal')
                    else:
                        outtfcmax.append('normal')
                        outtfcmin.append('normal')

                if intfcmax.count('warn')/len(intfcmax) == 1:
                    self.sendmsg(portgroup,ipif,inout['in'],'in','max',inmax)  
                elif intfcmin.count('warn')/len(intfcmin) == 1:
                    self.sendmsg(portgroup,ipif,inout['in'],'in','min',inmin)  
                #else:
                #    print portgroup,ipif,self._human(inout['in']),self._human(inmax),self._human(inmin) 
                if outtfcmax.count('warn')/len(outtfcmax) == 1:
                    self.sendmsg(portgroup,ipif,inout['out'],'out','max',outmax)  
                elif outtfcmax.count('warn')/len(outtfcmin) == 1:
                    self.sendmsg(portgroup,ipif,inout['out'],'out','min',outmin)  
                #else:
                #    print portgroup,ipif,self._human(inout['out']),self._human(outmax),self._human(outmin) 
                         

    def threshold_time(self,t):
        d,m,s,tz = t.split(':')
        m = '%02d' % (int(m)-int(m)%5) # 5:threshold interval,created by /bin/threshold.py
        return ':'.join([d,m,s,tz])
    

    def sendmsg(self,portgroup,ipif,tfc,inout,maxmin,x):
        direction = {'in':'入','out':'出'}
        level = {'min':'过低','max':'过高'}
        if ipif != 'group,group':
            return
        tpl = '[TFC Alert][%s] %s%s流量%s，当前值%s，阈值%s' % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),portgroup,direction[inout],level[maxmin],self._human(tfc),self._human(x))
        os.system(" curl -POST http://10.134.25.170/api/alarmSenter --data-urlencode 'content=%s' >/dev/null"%(tpl))
        print time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),tpl
        return 
        
    def _human(self,traffic):
        Gb=traffic/1000000000
        Mb=traffic/1000000
        if Gb > 0.7:return str('%.2f' % Gb)+'Gbps'
        else: return str('%.2f' % Mb)+'Mbps'
    
    def main(self):
        data =self.getTFC()
        self.overthreshold(data)


if __name__ == '__main__':
    tfc = TfcAlert('type=uplink') 
    tfc.main()

