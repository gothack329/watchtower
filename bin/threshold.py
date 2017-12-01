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
import json
from influxdb import InfluxDBClient
import time,datetime
reload(sys)
sys.setdefaultencoding('utf-8')


#try:
#    import httplib
#except ImportError:
#    import http.client as httplib

#httplib.HTTPConnection.debuglevel = 1
logging.basicConfig(level=logging.INFO)  


class CreateThread(object):
    def __init__(self, days='20d', interval='5', aggr=5 ):
        self.apiurl = ''
        self.db = 'localhost:8086'
        self.days = days
        self.aggr = aggr
        self.interval = int(interval) # interval: minute
        self.datasource = InfluxDBClient('localhost', 8086, 'root', '', 'snmpnew')
        self.thresource = InfluxDBClient('localhost', 8086, 'root', '', 'threshold')
        # sql arg : % (in, in, portgroup_name, time length, interval)
        self.selectsql = 'SELECT 8*difference(mean(%s))/elapsed(mean(%s),1s)  FROM "autogen"./^(%s)$/  WHERE  time>now()-%s GROUP BY time(1m), "ifname","device_ip" fill(previous)'
        return
    
    def getPortgroup(self):
        uri = '/api/portgroup/?limit=none' 
        url = self.apiurl+uri
        r = requests.get(url, timeout=10)
        data = json.loads(r.text)
        groups = [(i['name'],i['codename']) for i in data]
        logging.info('[%s] Total PortGroups: %s.' % (time.time(),str(len(groups))))
        # groups: [('公网：（电信）','uplink_sh_ctc'),]
        return groups 
        
    def getSourceData(self, portgroup, *arg):
        ''' 获取单个端口组合的流量数据 '''
        result = {}
        key = ['ifHCInOctets','ifHCOutOctets']
        for i in key:
            sql = self.selectsql % (i,i,portgroup[0],self.days)
            tfc = self.datasource.query(sql)
            result[i]=tfc.raw['series']

        ''' tfc.raw  时间处理需要+8h
            {u'series': [{u'columns': [u'time', u'difference_elapsed'],
               u'name': u'\u516c\uff09',
               u'tags': {u'device_ip': u'10.14.1.1',
                u'ifname': u'Ten-GigabitEthernet1/4/0/16'},
               u'values': [[u'2017-10-12T02:45:00Z', 612.8533333333334],
                    [u'2017-10-12T02:50:00Z', 621.3866666666667],
                    [u'2017-10-12T02:55:00Z', 619.68],
                    [u'2017-10-12T03:00:00Z', 614.795],
                    [u'2017-10-12T03:05:00Z', 628.2616666666667],
                    [u'2017-10-12T03:10:00Z', 617.29],
                    [u'2017-10-12T03:15:00Z', 615.9258333333333],
                    [u'2017-10-12T03:20:00Z', 614.9333333333333]]}],
             u'statement_id': 0}
        '''
        return result


    def singleData(self,data):
        '''
        将self.getSourceData()中数据按单端口数据处理：取出单个端口历史10天，每5分钟的均值的平均值
        '''
        allports = []
        for k,v in data.items():
            for singleport in v:
                result = {}
                result['portgroup'] = singleport['name']
                result['device_ip'] = singleport['tags']['device_ip']
                result['ifname'] = singleport['tags']['ifname']
                result[k] = defaultdict(list)
                for i in singleport['values']:
                    if result[k].has_key(i[0].split('T')[1]):
                        result[k][i[0].split('T')[1]].append(i[1])
                    else:
                        result[k][i[0].split('T')[1]] = [i[1]]
                # 求均值
                for z,x in result[k].items():
                    result[k][z]=[sum(x)/len(x)]
                # 按self.interval进行汇总，求上述每分钟均值的最大值
                for z,x in result[k].items():
                    h,m,s = z.split(':')
                    m=int(m)
                    if m%self.interval != 0:
                        result[k][h+':'+'%02d'%(m/self.interval*self.interval)+':'+s].append(result[k][z][0])
                        result[k].pop(z)
                for z,x in result[k].items():
                    if len(result[k][z]) < 5:
                        result[k].pop(z)
                    else:
                        result[k][z] = sum(result[k][z])/len(result[k][z])
                        #result[k][z] = max(result[k][z])
                allports.append(result)

        # 合并相同端口的in和out
        ret = []
        for i in range(len(allports)):
            for j in range(i+1,len(allports)):
                if allports[i]['device_ip']==allports[j]['device_ip'] and allports[i]['ifname']==allports[j]['ifname']:
                    allports[i].update(allports[j])
                    ret.append(allports[i])

        #pprint.pprint(json.loads(json.dumps(ret)))
        return ret


    def groupData(self,data):
        '''
        将self.getSourceData()中数据按端口组数据处理：取出组合叠加值历史10天，每5分钟的均值的最大值
        '''
        result = {} 
        for k,v in data.items():
            result[k] = defaultdict(list)
            for singleport in v:
                result['portgroup'] = singleport['name']
                for i in singleport['values']:
                    if result[k].has_key(i[0].split('T')[1]):
                        result[k][i[0].split('T')[1]].append(i[1])
                    else:
                        result[k][i[0].split('T')[1]] = [i[1]]
            # 求每分钟均值
            for z,x in result[k].items():
                x.sort()
                result[k][z]=[sum(x[2:-2])*len(v)/(len(x)-4)]
            
            # 按self.interval进行汇总，求上述每分钟均值的最大值
            for z,x in result[k].items():
                h,m,s = z.split(':')
                m=int(m)
                if m%self.interval != 0:
                    result[k][h+':'+'%02d'%(m/self.interval*self.interval)+':'+s].append(result[k][z][0])
                    result[k].pop(z)
            for z,x in result[k].items():
                if len(result[k][z]) < 5:
                    result[k].pop(z)
                else:
                    result[k][z] = max(result[k][z])
        
                    
        #print json.loads(json.dumps(result))
        a=[result]
        #pprint.pprint(json.loads(json.dumps(a)))
        return a


    def write(self,data):
        json_body = []
        for i in data:
            portgroup = i['portgroup']
            try:
                device_ip = i['device_ip']
                ifname = i['ifname']
            except:
                ifname = None
                device_ip = None

            for k,v in i['ifHCInOctets'].items():
                tomorrow=datetime.date.today()+datetime.timedelta(days=1)
                tomorrow=tomorrow.strftime('%Y-%m-%dT')+k
                try:
                    data = {
                                "measurement": 'threshold',
                                "time":tomorrow,
                                "tags": {
                                    'portgroup':portgroup
                                },
        
                                "fields": {
                                    'ifHCInOctets':float(v),
                                    'ifHCOutOctets':float(i['ifHCOutOctets'][k])
                                }
                            }
                    if device_ip and ifname:
                         data['tags']['device_ip'] = device_ip
                         data['tags']['ifname'] = ifname
                    else:
                         data['tags']['device_ip'] = 'group' 
                         data['tags']['ifname'] = 'group'
                        
                    json_body.append(data)
                except Exception,e:
                    print e
        try:
            self.datasource.write_points(json_body)
        except Exception,e:
            print e

        logging.info('[%s] %s Write finished.' % (time.time(),portgroup))


    def main(self):
        # 获取端口组合
        groups = self.getPortgroup()
        for group in groups:
            # 获取端口组合的原始流量数据
            try:
                data = self.getSourceData(group)
            except Exception,e:
                print e
                continue
            # 处理单端口阈值
            a=self.singleData(data)
            # 处理组合阈值
            b=self.groupData(data)
            self.write(a)
            self.write(b)

        return



if __name__ == '__main__':
    inst = CreateThread()
    inst.main()

