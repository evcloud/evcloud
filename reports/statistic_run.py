#!/usr/bin/python
#coding: utf-8#
import os
import sys
import math
import MySQLdb
import MySQLdb.cursors
import string 
import time,datetime

#database
dbhost='127.0.0.1'
dbname='vmmanager_2'
username='root'
password=''
tbname_host='compute_host'
tbname_group='compute_group'
tbname_center='compute_center'
tbname_report_host='reports_alloc_host'
tbname_report_host_latest='reports_alloc_host_latest'
tbname_report_group='reports_alloc_group'
tbname_report_group_latest='reports_alloc_group_latest'

tbname_report_center='reports_alloc_center'
tbname_report_center_latest='reports_alloc_center_latest'

#dict_host={"id":1,"group_id":1,"ipv4"='127.0.0.1',"vcpu_total":16,"vcpu_allocated":1,"mem_total":16,"mem_allocated":1,"mem_reserved":1}
#需要更新的统计列字段
th_statistic=["vcpu_total","vcpu_allocated","mem_total","mem_allocated","mem_reserved"]

T=24 #统计间隔时间（单位：h）

#统计资源使用情况，并更新数据库
#采用增量记录方式；
def statistic():
    #设置数据库查询结果类型为dict
    conn=MySQLdb.connect(host=dbhost,user=username,passwd=password,db=dbname, charset='utf8',cursorclass = MySQLdb.cursors.DictCursor)
    cur=conn.cursor()
    if not conn:
        print '数据库连接失败！\n'
    print '-----------statistic(): begin---------\n'
    nowtimestr=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    #####更新host资源统计信息######
    #查询最新的tbname_host 数据
    print '----更新host资源统计数据----\n'
    sqlstr='select * from %s;'%(tbname_host)
    cur.execute(sqlstr)
    compute_hosts=cur.fetchall()
    for h in compute_hosts:
        if h:
            host_id=h['id']
            #查询tbname_report_host_latest数据
            sqlstr='select * from %s where host_id=%d ;'%(tbname_report_host_latest,host_id)
            cur.execute(sqlstr)
            tmp=cur.fetchall() 
            if not tmp: #空值：插入表：report_host 和report_host_latest
                vcpu_alloc_rate=float(h['vcpu_allocated'])/float(h['vcpu_total'])
                mem_alloc_rate=float(h["mem_allocated"])/float(h["mem_total"])
                sqlstr='insert into %s(host_id,group_id,ipv4,vcpu_total,vcpu_allocated,vcpu_alloc_rate,mem_total,mem_allocated,mem_reserved,mem_alloc_rate,record_datetime) values(%d,%d,"%s",%d,%d,%f,%d,%d,%d,%f,"%s");' \
                        %(tbname_report_host,h["id"],h["group_id"],h["ipv4"],h["vcpu_total"],h["vcpu_allocated"],vcpu_alloc_rate,h["mem_total"],h["mem_allocated"],h["mem_reserved"],mem_alloc_rate,nowtimestr)
                cur.execute(sqlstr)
                conn.commit()
                sqlstr='insert into %s (host_id,group_id,ipv4,vcpu_total,vcpu_allocated,vcpu_alloc_rate,mem_total,mem_allocated,mem_reserved,mem_alloc_rate,record_datetime) values(%d,%d,"%s",%d,%d,%f,%d,%d,%d,%f,"%s");' \
                        %(tbname_report_host_latest,h["id"],h["group_id"],h["ipv4"],h["vcpu_total"],h["vcpu_allocated"],vcpu_alloc_rate,h["mem_total"],h["mem_allocated"],h["mem_reserved"],mem_alloc_rate,nowtimestr)
                cur.execute(sqlstr)
                conn.commit()
                continue
            
            report_host_latest=tmp[0]
            is_change=False
            for i in range(len(th_statistic)):
                if report_host_latest[th_statistic[i]] != h[th_statistic[i]]:
                    is_change=True
                    break
            #report_host 添加新数据，更新report_host_latest表
            if is_change:
                vcpu_alloc_rate=float(h["vcpu_allocated"])/float(h["vcpu_total"])
                mem_alloc_rate=float(h["mem_allocated"])/float(h["mem_total"])
                sqlstr='insert into %s(host_id,group_id,ipv4,vcpu_total,vcpu_allocated,vcpu_alloc_rate,mem_total,mem_allocated,mem_reserved,mem_alloc_rate,record_datetime) values(%d,%d,"%s",%d,%d,%f,%d,%d,%d,%f,"%s");' \
                        %(tbname_report_host,h["id"],h["group_id"],h["ipv4"],h["vcpu_total"],h["vcpu_allocated"],vcpu_alloc_rate,h["mem_total"],h["mem_allocated"],h["mem_reserved"],mem_alloc_rate,nowtimestr)
                cur.execute(sqlstr)
                conn.commit()
                #sqlstr='update %s set group_id=%d and ipv4="%s" and vcpu_total=%d and vcpu_allocated=%d and vcpu_alloc_rate=%d and mem_total=%d and mem_allocated=%d and mem_reserved=%d and mem_alloc_rate=%d and record_datetime="%s" where host_id=%d;' \
                #        %(tbname_report_host_latest,h["group_id"],h["ipv4"],h["vcpu_total"],h["vcpu_allocated"],vcpu_alloc_rate,h["mem_total"],h["mem_allocated"],h["mem_reserved"],mem_alloc_rate,nowtimestr,h["id"])
                sqlstr='delete from %s where host_id=%d' %(tbname_report_host_latest,h["id"])
                cur.execute(sqlstr)
                conn.commit()
                sqlstr='insert into %s(host_id,group_id,ipv4,vcpu_total,vcpu_allocated,vcpu_alloc_rate,mem_total,mem_allocated,mem_reserved,mem_alloc_rate,record_datetime) values(%d,%d,"%s",%d,%d,%f,%d,%d,%d,%f,"%s");' \
                        %(tbname_report_host_latest,h["id"],h["group_id"],h["ipv4"],h["vcpu_total"],h["vcpu_allocated"],vcpu_alloc_rate,h["mem_total"],h["mem_allocated"],h["mem_reserved"],mem_alloc_rate,nowtimestr)
                cur.execute(sqlstr)
                conn.commit()
    
    #####更新group资源统计信息######
    #查询tbname_group中的所有group，并更新统计数据
    print '----更新group资源统计数据----\n'
    sqlstr='select * from %s;'%(tbname_group)
    cur.execute(sqlstr)
    compute_groups=cur.fetchall()
    for g in compute_groups:
        if g:
            group_id=g['id']
            #通过表tbname_report_host_latest计算id=g['id']的最新的report_group统计数据
            sqlstr='select sum(%s) as %s,sum(%s) as %s,sum(%s) as %s,sum(%s) as %s,sum(%s) as %s from %s where group_id=%d;' %(th_statistic[0],th_statistic[0],th_statistic[1],th_statistic[1],th_statistic[2],th_statistic[2],th_statistic[3],th_statistic[3],th_statistic[4],th_statistic[4],tbname_report_host_latest,group_id)
            cur.execute(sqlstr)
            tmp1=cur.fetchall()
            if not tmp1: 
                continue
            group_statistic=tmp1[0]
            #计算cpu和mem使用率
            #没有属于g['id']的host资源统计信息,设置空值
            if  (group_statistic["vcpu_allocated"] != None) and (group_statistic["vcpu_total"] != None):
                vcpu_alloc_rate=float(group_statistic["vcpu_allocated"])/float(group_statistic["vcpu_total"])
            else :
                group_statistic["vcpu_allocated"]=0
                group_statistic["vcpu_total"]=0
                vcpu_alloc_rate=0
            if  (group_statistic["mem_allocated"] != None) and (group_statistic["mem_total"] != None ):
                mem_alloc_rate=float(group_statistic["mem_allocated"])/float(group_statistic["mem_total"])
            else :
                group_statistic["mem_allocated"]=0
                group_statistic["mem_total"]=0
                group_statistic["mem_reserved"]=0
                mem_alloc_rate=0
            
            #对比tbname_report_group_latest数据，是否有变化
            sqlstr='select * from %s where group_id=%d ;'%(tbname_report_group_latest,group_id)
            cur.execute(sqlstr)
            tmp=cur.fetchall()
            if (not tmp) : #空值：插入表：report_group 和report_group_latest
                sqlstr='insert into %s(group_id,group_name,center_id,vcpu_total,vcpu_allocated,vcpu_alloc_rate,mem_total,mem_allocated,mem_reserved,mem_alloc_rate,record_datetime) values(%d,"%s",%d,%d,%d,%f,%d,%d,%d,%f,"%s");' \
                        %(tbname_report_group,g["id"],g["name"],g["center_id"],group_statistic["vcpu_total"],group_statistic["vcpu_allocated"],vcpu_alloc_rate,group_statistic["mem_total"],group_statistic["mem_allocated"],group_statistic["mem_reserved"],mem_alloc_rate,nowtimestr)
                cur.execute(sqlstr)
                conn.commit()
                sqlstr='insert into %s(group_id,group_name,center_id,vcpu_total,vcpu_allocated,vcpu_alloc_rate,mem_total,mem_allocated,mem_reserved,mem_alloc_rate,record_datetime) values(%d,"%s",%d,%d,%d,%f,%d,%d,%d,%f,"%s");' \
                        %(tbname_report_group_latest,g["id"],g["name"],g["center_id"],group_statistic["vcpu_total"],group_statistic["vcpu_allocated"],vcpu_alloc_rate,group_statistic["mem_total"],group_statistic["mem_allocated"],group_statistic["mem_reserved"],mem_alloc_rate,nowtimestr)
                cur.execute(sqlstr)
                conn.commit()
                continue
            report_group_latest=tmp[0]
            is_change=False
            for i in th_statistic:
                if group_statistic[i] != report_group_latest[i]:
                    is_change=True
                    break
            #report_host 添加新数据，更新report_host_latest表
            if is_change:
                report_group_latest["record_datetime"]=nowtimestr
                sqlstr='insert into %s(group_id,group_name,center_id,vcpu_total,vcpu_allocated,vcpu_alloc_rate,mem_total,mem_allocated,mem_reserved,mem_alloc_rate,record_datetime) values(%d,"%s",%d,%d,%d,%f,%d,%d,%d,%f,"%s");' \
                        %(tbname_report_group,g["id"],g["name"],g["center_id"],group_statistic["vcpu_total"],group_statistic["vcpu_allocated"],vcpu_alloc_rate,group_statistic["mem_total"],group_statistic["mem_allocated"],group_statistic["mem_reserved"],mem_alloc_rate,nowtimestr)
                cur.execute(sqlstr)
                conn.commit()
                sqlstr='delete from %s where group_id=%d' %(tbname_report_group_latest,g["id"])
                cur.execute(sqlstr)
                conn.commit()
                sqlstr='insert into %s(group_id,group_name,center_id,vcpu_total,vcpu_allocated,vcpu_alloc_rate,mem_total,mem_allocated,mem_reserved,mem_alloc_rate,record_datetime) values(%d,"%s",%d,%d,%d,%f,%d,%d,%d,%f,"%s");' \
                        %(tbname_report_group_latest,g["id"],g["name"],g["center_id"],group_statistic["vcpu_total"],group_statistic["vcpu_allocated"],vcpu_alloc_rate,group_statistic["mem_total"],group_statistic["mem_allocated"],group_statistic["mem_reserved"],mem_alloc_rate,nowtimestr)
                cur.execute(sqlstr)
                conn.commit()
    
    #####更新center资源统计信息######
    #查询tbname_center中的所有center数据，分别更新统计数据
    print '----更新center资源统计数据----'
    sqlstr='select * from %s;'%(tbname_center)
    cur.execute(sqlstr)
    compute_centers=cur.fetchall()
    for c in compute_centers:
        if c:
            center_id=c['id']
            #通过表tbname_report_group_latest计算id=c['id']的最新的report_center统计数据
            sqlstr='select sum(%s) as %s,sum(%s) as %s,sum(%s) as %s,sum(%s) as %s,sum(%s) as %s from %s where center_id=%d;' %(th_statistic[0],th_statistic[0],th_statistic[1],th_statistic[1],th_statistic[2],th_statistic[2],th_statistic[3],th_statistic[3],th_statistic[4],th_statistic[4],tbname_report_group_latest,center_id)
            cur.execute(sqlstr)
            tmp1=cur.fetchall()
            if not tmp1: #没有属于c['id']的group资源统计信息
                continue
            center_statistic=tmp1[0]
            if  (center_statistic["vcpu_allocated"] != None) and (center_statistic["vcpu_total"] != None ):
                vcpu_alloc_rate=float(center_statistic["vcpu_allocated"])/float(center_statistic["vcpu_total"])
            else:
                center_statistic["vcpu_allocated"]=0
                center_statistic["vcpu_total"]=0
                vcpu_alloc_rate=0
            if  (center_statistic["mem_allocated"] != None) and (center_statistic["mem_total"] != None ):
                mem_alloc_rate=float(center_statistic["mem_allocated"])/float(center_statistic["mem_total"])
            else:
                center_statistic["mem_allocated"]=0
                center_statistic["mem_total"]=0
                center_statistic["mem_reserved"]=0
                mem_alloc_rate=0
            #对比tbname_report_center_latest数据，是否有变化
            sqlstr='select * from %s where center_id=%d ;'%(tbname_report_center_latest,center_id)
            cur.execute(sqlstr)
            tmp=cur.fetchall()
            
            if (not tmp) : #空值：插入表：report_center 和report_center_latest
                sqlstr='insert into %s(center_id,center_name,vcpu_total,vcpu_allocated,vcpu_alloc_rate,mem_total,mem_allocated,mem_reserved,mem_alloc_rate,record_datetime) values(%d,"%s",%d,%d,%f,%d,%d,%d,%f,"%s");' \
                        %(tbname_report_center,c["id"],c["name"],center_statistic["vcpu_total"],center_statistic["vcpu_allocated"],vcpu_alloc_rate,center_statistic["mem_total"],center_statistic["mem_allocated"],center_statistic["mem_reserved"],mem_alloc_rate,nowtimestr)
                cur.execute(sqlstr)
                conn.commit()
                sqlstr='insert into %s(center_id,center_name,vcpu_total,vcpu_allocated,vcpu_alloc_rate,mem_total,mem_allocated,mem_reserved,mem_alloc_rate,record_datetime) values(%d,"%s",%d,%d,%f,%d,%d,%d,%f,"%s");' \
                        %(tbname_report_center_latest,c["id"],c["name"],center_statistic["vcpu_total"],center_statistic["vcpu_allocated"],vcpu_alloc_rate,center_statistic["mem_total"],center_statistic["mem_allocated"],center_statistic["mem_reserved"],mem_alloc_rate,nowtimestr)
                cur.execute(sqlstr)
                conn.commit()
                continue
            report_center_latest=tmp[0]
            is_change=False
            for i in th_statistic:
                if center_statistic[i] != report_center_latest[i]:
                    is_change=True
                    break
            #report_host 添加新数据，更新report_center_latest表
            if is_change:
                report_center_latest["record_datetime"]=nowtimestr
                sqlstr='insert into %s(center_id,center_name,vcpu_total,vcpu_allocated,vcpu_alloc_rate,mem_total,mem_allocated,mem_reserved,mem_alloc_rate,record_datetime) values(%d,"%s",%d,%d,%f,%d,%d,%d,%f,"%s");' \
                        %(tbname_report_center,c["id"],c["name"],center_statistic["vcpu_total"],center_statistic["vcpu_allocated"],vcpu_alloc_rate,center_statistic["mem_total"],center_statistic["mem_allocated"],center_statistic["mem_reserved"],mem_alloc_rate,nowtimestr)
                cur.execute(sqlstr)
                conn.commit()
                sqlstr='delete from %s where center_id=%d' %(tbname_report_center_latest,c["id"])
                cur.execute(sqlstr)
                conn.commit()
                sqlstr='insert into %s(center_id,center_name,vcpu_total,vcpu_allocated,vcpu_alloc_rate,mem_total,mem_allocated,mem_reserved,mem_alloc_rate,record_datetime) values(%d,"%s",%d,%d,%f,%d,%d,%d,%f,"%s");' \
                        %(tbname_report_center_latest,c["id"],c["name"],center_statistic["vcpu_total"],center_statistic["vcpu_allocated"],vcpu_alloc_rate,center_statistic["mem_total"],center_statistic["mem_allocated"],center_statistic["mem_reserved"],mem_alloc_rate,nowtimestr)
                cur.execute(sqlstr)
                conn.commit()
    print '----更新center资源统计数据-结束---\n'
    cur.close()
    conn.close()
    print '-----------statistic(): end---------\n'

#main():run by itself
#每隔T 小时，运行一次资源数据统计
if __name__=='__main__':
    print 'welcome to use this process ,by lzx! lzxddz@cnic.cn \n'
    print time.strftime('当前时间： %Y-%m-%d %H:%M:%S',time.localtime(time.time()))
    last_datetime=datetime.datetime.now()
    now_datetime=datetime.datetime.now()
    statistic()
    print 'bye! \n'
