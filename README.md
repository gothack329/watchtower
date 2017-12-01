## WatchTower 数据中心网络监控

## 一、基础数据表

**datacenter**: 定义数据中心名称、codename，通过codename和设备所在机房进行关联

**device:** iMC对网络设备自动探活，然后每天同步到此表中，device_role、idc分别是通过设备上snmp contact、location配置获取

**dev_role:** 定义设备角色，通过codename和设备关联

**port:** 也是从iMC中获取，主要抓取端口名称、描述、ifindex、端口速率，tag字段目前仅用ign标识忽略报警

**portgroup:** 定义重要端口组合，通过codename和`port`表中做关联，目前codename前缀和type字段都可用于端口组合类型筛选

**config_oid:** 定义snmp采集的oid，所有程序中需要的oid都从这里获取

**lldpid:** 存储的是lldp两段端口的id值，对应`port`表中的id，对于无法通过lldp采集的连接，可以通过手动录入端口id的方法，此情况需要在tag字段加manual，用于页面绘图使用

**topology_view:** 定义网络拓扑中的视图，以及每个视图中的设备，设备添加方法有两种，可以通过/api/view_device/用uri过滤，或者直接添加deviceid，deviceid对应`device`表中id字段

**topology_node_position:** 每个视图中每台设备坐标位置，在topo页面中拖动后即保存

**view_device:** 关联`device`、`dev_role`、`datacenter `三张表

**view_lldp**：关联`lldpid`、`port`两张表

**view_port:** 关联`port`、`device`两张表

**view_portgroup:** 关联`port`、`portgroup`、`device`三张表

## 二、数据抓取程序

##### getDevices.py

从iMC读取设备列表，保存到`device`表中，同时保存到`device.all`文件中，用做logins登陆脚本。

##### getInterfaces.py

从iMC读取所有端口列表，保存到`port`表中。

> 以上两个程序提供所有外部数据的获取

##### snmpwalker.py

采集交换机端口数据的程序，采集oid通过`config_oid`表中的realtime类型获取，按照每台交换机、每个oid区分多线程，另外有一个监控进程，会在每个端口所有oid的数据采集完成后实时存入influxdb中。此程序是采集所有设备全量端口数据。

##### snmp_portgroup.py

针对H3C S125系列交换机，snmp采集响应慢，无法完成每分钟全量端口数据的采集，因此对于公网出口、专线等portgroup中的核心端口，通过此程序仅对指定端口采集数据，非全量端口采集。此程序会在所有数据都采集完成后，一并将本次数据都存入influxdb中。

##### threshold.py

`portgroup`表中的端口会有流量高低的报警，此程序会通过过去N天的数据，计算端口组合和单端口的流量5分钟均值，存入influxdb。

##### tfcalert.py

根据threshold.py中的数据，计算每个端口、端口组合的流量高低阈值。原则上，阈值是根据每端口/端口组合历史均值乘以系数，高阈值默认是1.2，低阈值默认是0.5，然后考虑到每条线路正常流量值差异较大，对于平时流量较低的，抖动通常比较大，平时流量较高的，抖动通常比较小。因此，阈值的生成并非固定系数，而是也采用动态曲线生成，流量越大，越接近上面所说的默认系数。高低阈值系数生成的两条曲线如下图，高阈值的最小阈值是700M，低阈值的最小阈值是10M。

![](https://ws3.sinaimg.cn/large/006tNc79ly1fm13pw8iirj30px0bzt9n.jpg)

##### lldp.release.py

此程序负责采集全网所有连接关系，通过lldpRemSysName和lldpRemPortId抓取对端设备的sysname和ifindex，然后通过`device`表、`port`表对应具体的port id，录入`lldpid`表中。

需要特殊说明的是H3C通过lldpRemPortId抓出来的并非对端接口的ifindex，而是另一种形式的端口id，还需要通过dot1dBasePortIfIndex来对应。

采集方式是，将`port`中的所有端口取出放到一个池子里，然后扫描所有的`device`，每采集到一个端口的lldp，就将本端和对端端口从池子里取出，如果所采集端口或者邻居端口池子里没有，则跳过。直至所有设备采集完毕，或者池子中端口不再有变化超时退出。

##### api.py

此程序用于提供基础数据mysql的http api，使用uwsgi开发，提供get/post接口，url通过/api/`{table}`/来调用，可按字段查询，另通过sql参数可提供where语句的复杂查询。不加参数则默认显示20条记录，可以通过limit=none显示全部或指定返回记录数。

##### logins

登陆跳板程序



## 三、监控数据

监控数据都存储在influxdb，snmpwalker.py抓取的结果存在snmp库中，snmp_portgroup抓取的数据存在snmpnew中。snmp库每台设备一张表，表名为设备ip，snmpnew每个portgroup一张表，表名为portgroup名称。

```
> show databases
name: databases
name
----
_internal
snmp
snmpnew
```

```
> use snmp
> select * from "10.149.1.134" limit 2
name: 10.149.1.134
time                ifHCInOctets     ifHCOutOctets    ifInErrors ifInUcastPkts ifOperStatus ifOutErrors ifOutUcastPkts ifindex ifname
----                ------------     -------------    ---------- ------------- ------------ ----------- -------------- ------- ------
1507527248756286782 180341358151028  92432149688206   0          1512643599    1            0           3217864119     1       GigabitEthernet1/0/11
1507527248756286782 3012893271170626 3548530337647621 0          1552092790    1            0           4089709693     99      Ten-GigabitEthernet1/0/1
> use snmpnew
> select * from /^公网：电信$/ limit 2
name: 公网：电信
time                device_ip  ifHCInOctets    ifHCOutOctets    ifInErrors ifInUcastPkts ifOperStatus ifOutErrors ifOutUcastPkts ifindex ifname
----                ---------  ------------    -------------    ---------- ------------- ------------ ----------- -------------- ------- ------
1507691886324274970 10.135.1.1 696169018535421 2846296772727103 0          1237080399    1            0           1138560445     4242    Ten-GigabitEthernet2/5/0/34:2
1507691886324274970 10.135.1.1 915746057555810 2960801668357786 1          2888292000    1            0           3342504025     762     Ten-GigabitEthernet1/5/0/34:2
> 
```



## 四、实时拓扑监控

![](https://ws1.sinaimg.cn/large/006tNc79ly1fm19w2876vj313q0ks47s.jpg)

拓扑采用Django绘制，待补充













