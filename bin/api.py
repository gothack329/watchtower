#!/bin/env python

'''
    version : v2.1
    date : 20171130
    comment:
        v2.0: add http post 
        v2.1: add sql where query
'''

import os, sys
import re
import time, json, datetime
from urllib import unquote
from cgi import parse_qs
import ConfigParser
import logging 
import collections
import MySQLdb as mysql
reload(sys)
sys.setdefaultencoding('utf8')

logger = logging.basicConfig(level=logging.DEBUG,
    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
    datefmt='%a, %d %b %Y %H:%M:%S',
    )

def application(env, start_response):
    print dir(env)
    start_response('200 OK', [('Content-Type','application/json')])
    try:
        query = env.get('QUERY_STRING',None)
        method = env.get('REQUEST_METHOD',None)
        uri = env.get('REQUEST_URI',None)
    except Exception, e:
        logging.debug(e)
        query = None

    args = {}
    print method
    if method == 'POST':
        postData = env['wsgi.input'].readline().decode()
        query =  parse_qs(postData)
        for k,v in query.items():
            args[k]=v[0]
    else:
        for arg in query.split('&'):
            try:
                args[arg.split('=')[0]] = unquote(arg.split('=')[1]).strip()
            except Exception,e:
                #logging.debug(e)
                pass
        
    uri = uri.split('?')[0]
    resp = url_route(uri,args)
    if resp:
        return resp
    else:
        pass

def url_route(uri,args):
    app = uri.split('/')
    urlpatterns = [
        ['api',  api, args],
    ]
    for i in urlpatterns:
        url, func, arg = i
        if app[1] == url :
            return func(arg,app[2])

def api(args,table):
    if args.has_key('limit'):
        limit = args['limit']
        args.pop('limit')
        if limit == 'none':
            limit = None
    else:
        limit = '20'

    if args.has_key('sql'):
        print args['sql']
        sqlwhere = args['sql'].strip('"')
        args.pop('sql')
    else:
        sqlwhere = None


    con = mysql.connect(user='username',db='nms',passwd='password',host='localhost',charset="utf8")
    cur = con.cursor()

    base_sql = 'select * from %s '
    if sqlwhere:
        base_sql = base_sql + ' where ' + sqlwhere 
    elif limit:
        base_sql = base_sql + ' limit '+limit

    if len(args) == 0:
        sql = base_sql % (table)  
    else:
        sqlarg = [] 
        for k,v in args.items():
            if ',' in v:
               sqlarg.append(' or '.join([' %s like "%s" ' % (k,j) for j in v.split(',')])) 
            else:
               sqlarg+=[' %s like "%s" '%(k,v) ]
        sql = base_sql.split('limit')[0] % (table) + ' where ' + ' and '.join(sqlarg)
        #sql = base_sql.split('limit')[0] % (table) + ' where ' + ' and '.join([' %s like "%s" '%(k,v) for k,v in args.items()])

        #print sql
    try:
        counter = cur.execute(sql)
    except Exception,e:
        print e
        print sql

    data = cur.fetchall()
    fields = cur.description   
    cur.close()
    con.close()
    
    result = [] 
    for item in data:
        i = {} 
        for index in range(len(item)):
            i[fields[index][0]] = str(item[index])
        result.append(i)
    
    return json.dumps(result,sort_keys=True)


