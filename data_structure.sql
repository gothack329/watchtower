-- phpMyAdmin SQL Dump
-- version 4.7.4
-- https://www.phpmyadmin.net/
--
-- Generation Time: 2017-12-08 08:55:38
-- 服务器版本： 5.5.28-log
-- PHP Version: 5.5.38

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET AUTOCOMMIT = 0;
START TRANSACTION;
SET time_zone = "+00:00";

--
-- Database: `nms`
--

-- --------------------------------------------------------

--
-- 表的结构 `config_alert`
--

CREATE TABLE `config_alert` (
  `id` int(11) NOT NULL,
  `device_ip` varchar(40) NOT NULL,
  `ifindex` varchar(16) NOT NULL,
  `threshold` varchar(8) NOT NULL COMMENT '单位：%',
  `frequence` varchar(8) DEFAULT '1' COMMENT '连续几次报警',
  `tag` varchar(64) DEFAULT NULL,
  `inuse` varchar(3) DEFAULT 'y'
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- 表的结构 `config_collector`
--

CREATE TABLE `config_collector` (
  `id` int(11) NOT NULL,
  `device_ip` varchar(40) NOT NULL,
  `ifindex` varchar(16) NOT NULL,
  `period` varchar(8) NOT NULL DEFAULT '60' COMMENT '单位：秒',
  `inuse` varchar(3) DEFAULT 'y',
  `tag` varchar(128) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- 表的结构 `config_oid`
--

CREATE TABLE `config_oid` (
  `id` int(11) NOT NULL,
  `name` varchar(128) NOT NULL,
  `oid` varchar(128) NOT NULL,
  `type` varchar(128) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- 转存表中的数据 `config_oid`
--

INSERT INTO `config_oid` (`id`, `name`, `oid`, `type`) VALUES
(1, 'ifSpeed', '.1.3.6.1.2.1.2.2.1.5 ', 'period'),
(3, 'ifOperStatus', '.1.3.6.1.2.1.2.2.1.8', 'realtime'),
(5, 'ifHCInOctets', '.1.3.6.1.2.1.31.1.1.1.6', 'realtime'),
(7, 'ifInErrors', '.1.3.6.1.2.1.2.2.1.14', 'realtime'),
(9, 'ifInUcastPkts', '.1.3.6.1.2.1.2.2.1.11', 'realtime'),
(11, 'ifHCOutOctets', '.1.3.6.1.2.1.31.1.1.1.10', 'realtime'),
(13, 'ifOutErrors', '.1.3.6.1.2.1.2.2.1.20', 'realtime'),
(15, 'ifOutUcastPkts', '.1.3.6.1.2.1.2.2.1.17', 'realtime'),
(17, 'lldpRemSysName', '.1.0.8802.1.1.2.1.4.1.1.9', 'lldp'),
(19, 'lldpRemPortId', '.1.0.8802.1.1.2.1.4.1.1.7', 'lldp'),
(21, 'dot1dBasePortIfIndex', '.1.3.6.1.2.1.17.1.4.1.2', 'lldp');

-- --------------------------------------------------------

--
-- 表的结构 `datacenter`
--

CREATE TABLE `datacenter` (
  `id` int(11) NOT NULL,
  `name` varchar(128) NOT NULL,
  `codename` varchar(128) NOT NULL,
  `location` varchar(1024) DEFAULT NULL,
  `provider` varchar(128) DEFAULT NULL,
  `isp` varchar(128) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- 表的结构 `device`
--

CREATE TABLE `device` (
  `id` int(11) NOT NULL,
  `imcid` varchar(8) DEFAULT NULL,
  `name` varchar(128) DEFAULT NULL,
  `device_ip` varchar(40) NOT NULL,
  `sn` varchar(40) DEFAULT NULL,
  `device_role` varchar(128) DEFAULT NULL,
  `idc` varchar(128) DEFAULT NULL,
  `model` varchar(128) DEFAULT NULL,
  `vendor` varchar(128) DEFAULT NULL,
  `sysdesc` varchar(128) DEFAULT NULL,
  `ctime` timestamp NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- 表的结构 `dev_role`
--

CREATE TABLE `dev_role` (
  `id` int(11) NOT NULL,
  `name` varchar(128) NOT NULL,
  `codename` varchar(128) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- 转存表中的数据 `dev_role`
--

INSERT INTO `dev_role` (`id`, `name`, `codename`) VALUES
(1, '接入交换机', 'tor'),
(3, '核心交换机', 'pod-core'),
(5, '内网路由器', 'dci-router'),
(7, '汇聚交换机', 'aggr');

-- --------------------------------------------------------

--
-- 表的结构 `isp`
--

CREATE TABLE `isp` (
  `id` int(11) NOT NULL,
  `name` varchar(32) NOT NULL,
  `codename` varchar(32) NOT NULL,
  `tag` varchar(32) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- 表的结构 `lldpid`
--

CREATE TABLE `lldpid` (
  `id` int(11) NOT NULL,
  `aid` int(11) NOT NULL,
  `zid` int(11) NOT NULL,
  `tag` varchar(32) DEFAULT NULL,
  `ctime` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `mtime` varchar(40) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- 表的结构 `port`
--

CREATE TABLE `port` (
  `id` int(11) NOT NULL,
  `name` varchar(128) NOT NULL,
  `ifindex` varchar(40) NOT NULL,
  `ifdesc` varchar(64) DEFAULT NULL,
  `device_ip` varchar(40) NOT NULL,
  `speed` varchar(16) DEFAULT NULL COMMENT '单位：Bit',
  `portgroup` varchar(128) DEFAULT NULL,
  `tag` varchar(32) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- 表的结构 `portgroup`
--

CREATE TABLE `portgroup` (
  `id` int(11) NOT NULL,
  `name` varchar(128) NOT NULL,
  `codename` varchar(128) NOT NULL,
  `type` varchar(128) DEFAULT NULL,
  `logical_bw` varchar(16) DEFAULT NULL COMMENT '单位：M',
  `ctime` timestamp NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- 表的结构 `topology_node_position`
--

CREATE TABLE `topology_node_position` (
  `id` int(12) NOT NULL,
  `nodeid` varchar(8) NOT NULL,
  `viewname` varchar(64) NOT NULL,
  `x` varchar(20) NOT NULL DEFAULT '0',
  `y` varchar(20) NOT NULL DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- 表的结构 `topology_view`
--

CREATE TABLE `topology_view` (
  `id` int(12) NOT NULL,
  `name` varchar(64) NOT NULL,
  `codename` varchar(64) NOT NULL,
  `deviceid` varchar(1024) DEFAULT NULL,
  `uri` varchar(1024) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- 替换视图以便查看 `view_device`
-- (See below for the actual view)
--
CREATE TABLE `view_device` (
`device_id` int(11)
,`device_name` varchar(128)
,`device_ip` varchar(40)
,`device_sn` varchar(40)
,`device_model` varchar(128)
,`device_vendor` varchar(128)
,`sysdesc` varchar(128)
,`idc_name` varchar(128)
,`device_role` varchar(128)
);

-- --------------------------------------------------------

--
-- 替换视图以便查看 `view_lldp`
-- (See below for the actual view)
--
CREATE TABLE `view_lldp` (
`id` int(11)
,`aportid` int(11)
,`adevid` int(11)
,`aip` varchar(40)
,`aport` varchar(128)
,`zport` varchar(128)
,`zip` varchar(40)
,`zdevid` int(11)
,`zportid` int(11)
,`tag` varchar(32)
,`ctime` timestamp
,`mtime` varchar(40)
);

-- --------------------------------------------------------

--
-- 替换视图以便查看 `view_port`
-- (See below for the actual view)
--
CREATE TABLE `view_port` (
`port_id` int(11)
,`port_name` varchar(128)
,`port_ifindex` varchar(40)
,`port_ifdesc` varchar(64)
,`device_ip` varchar(40)
,`device_name` varchar(128)
,`vendor` varchar(128)
,`port_speed` varchar(16)
,`portgroup` varchar(128)
,`idc` varchar(128)
,`device_role` varchar(128)
,`tag` varchar(32)
);

-- --------------------------------------------------------

--
-- 替换视图以便查看 `view_portgroup`
-- (See below for the actual view)
--
CREATE TABLE `view_portgroup` (
`portgroup_id` int(11)
,`portgroup_name` varchar(128)
,`codename` varchar(128)
,`device_id` int(11)
,`device_ip` varchar(40)
,`port_ifindex` varchar(40)
,`port_name` varchar(128)
,`port_speed` varchar(16)
,`type` varchar(128)
,`port_tag` varchar(32)
);

-- --------------------------------------------------------

--
-- 视图结构 `view_device`
--
DROP TABLE IF EXISTS `view_device`;

CREATE ALGORITHM=UNDEFINED DEFINER=`network`@`10.%` SQL SECURITY DEFINER VIEW `view_device`  AS  select `a`.`id` AS `device_id`,`a`.`name` AS `device_name`,`a`.`device_ip` AS `device_ip`,`a`.`sn` AS `device_sn`,`a`.`model` AS `device_model`,`a`.`vendor` AS `device_vendor`,`a`.`sysdesc` AS `sysdesc`,`b`.`name` AS `idc_name`,`c`.`name` AS `device_role` from ((`device` `a` join `datacenter` `b`) join `dev_role` `c`) where ((`a`.`idc` = `b`.`codename`) and (`a`.`device_role` = `c`.`codename`)) ;

-- --------------------------------------------------------

--
-- 视图结构 `view_lldp`
--
DROP TABLE IF EXISTS `view_lldp`;

CREATE ALGORITHM=UNDEFINED DEFINER=`network`@`10.%` SQL SECURITY DEFINER VIEW `view_lldp`  AS  select `b`.`id` AS `id`,`a`.`id` AS `aportid`,`d`.`id` AS `adevid`,`a`.`device_ip` AS `aip`,`a`.`name` AS `aport`,`c`.`name` AS `zport`,`c`.`device_ip` AS `zip`,`e`.`id` AS `zdevid`,`c`.`id` AS `zportid`,`b`.`tag` AS `tag`,`b`.`ctime` AS `ctime`,`b`.`mtime` AS `mtime` from ((((`port` `a` join `lldpid` `b`) join `port` `c`) join `device` `d`) join `device` `e`) where ((`a`.`id` = `b`.`aid`) and (`c`.`id` = `b`.`zid`) and (`a`.`device_ip` = `d`.`device_ip`) and (`c`.`device_ip` = `e`.`device_ip`)) ;

-- --------------------------------------------------------

--
-- 视图结构 `view_port`
--
DROP TABLE IF EXISTS `view_port`;

CREATE ALGORITHM=UNDEFINED DEFINER=`network`@`10.%` SQL SECURITY DEFINER VIEW `view_port`  AS  select `a`.`id` AS `port_id`,`a`.`name` AS `port_name`,`a`.`ifindex` AS `port_ifindex`,`a`.`ifdesc` AS `port_ifdesc`,`a`.`device_ip` AS `device_ip`,`b`.`name` AS `device_name`,`b`.`vendor` AS `vendor`,`a`.`speed` AS `port_speed`,`a`.`portgroup` AS `portgroup`,`b`.`idc` AS `idc`,`b`.`device_role` AS `device_role`,`a`.`tag` AS `tag` from (`port` `a` join `device` `b`) where (`a`.`device_ip` = `b`.`device_ip`) ;

-- --------------------------------------------------------

--
-- 视图结构 `view_portgroup`
--
DROP TABLE IF EXISTS `view_portgroup`;

CREATE ALGORITHM=UNDEFINED DEFINER=`network`@`10.%` SQL SECURITY DEFINER VIEW `view_portgroup`  AS  select `b`.`id` AS `portgroup_id`,`b`.`name` AS `portgroup_name`,`b`.`codename` AS `codename`,`c`.`id` AS `device_id`,`a`.`device_ip` AS `device_ip`,`a`.`ifindex` AS `port_ifindex`,`a`.`name` AS `port_name`,`a`.`speed` AS `port_speed`,`b`.`type` AS `type`,`a`.`tag` AS `port_tag` from ((`port` `a` join `portgroup` `b`) join `device` `c`) where ((`a`.`portgroup` = `b`.`codename`) and (`c`.`device_ip` = `a`.`device_ip`)) ;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `config_alert`
--
ALTER TABLE `config_alert`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `config_collector`
--
ALTER TABLE `config_collector`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `config_oid`
--
ALTER TABLE `config_oid`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `datacenter`
--
ALTER TABLE `datacenter`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `codename` (`codename`);

--
-- Indexes for table `device`
--
ALTER TABLE `device`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `ip` (`device_ip`),
  ADD KEY `sn_2` (`sn`),
  ADD KEY `sn_3` (`sn`);

--
-- Indexes for table `dev_role`
--
ALTER TABLE `dev_role`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `codename` (`codename`);

--
-- Indexes for table `isp`
--
ALTER TABLE `isp`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `lldpid`
--
ALTER TABLE `lldpid`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `aid` (`aid`,`zid`),
  ADD KEY `id` (`id`);

--
-- Indexes for table `port`
--
ALTER TABLE `port`
  ADD PRIMARY KEY (`id`),
  ADD KEY `devip` (`device_ip`);

--
-- Indexes for table `portgroup`
--
ALTER TABLE `portgroup`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `id` (`id`);

--
-- Indexes for table `topology_node_position`
--
ALTER TABLE `topology_node_position`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `view_devid` (`nodeid`,`viewname`);

--
-- Indexes for table `topology_view`
--
ALTER TABLE `topology_view`
  ADD PRIMARY KEY (`id`);

--
-- 在导出的表使用AUTO_INCREMENT
--

--
-- 使用表AUTO_INCREMENT `config_oid`
--
ALTER TABLE `config_oid`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=23;

--
-- 使用表AUTO_INCREMENT `datacenter`
--
ALTER TABLE `datacenter`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=37;

--
-- 使用表AUTO_INCREMENT `device`
--
ALTER TABLE `device`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3661;

--
-- 使用表AUTO_INCREMENT `dev_role`
--
ALTER TABLE `dev_role`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;

--
-- 使用表AUTO_INCREMENT `isp`
--
ALTER TABLE `isp`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=15;

--
-- 使用表AUTO_INCREMENT `lldpid`
--
ALTER TABLE `lldpid`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=334465;

--
-- 使用表AUTO_INCREMENT `port`
--
ALTER TABLE `port`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=271925;

--
-- 使用表AUTO_INCREMENT `portgroup`
--
ALTER TABLE `portgroup`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=189;

--
-- 使用表AUTO_INCREMENT `topology_node_position`
--
ALTER TABLE `topology_node_position`
  MODIFY `id` int(12) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=545337;

--
-- 使用表AUTO_INCREMENT `topology_view`
--
ALTER TABLE `topology_view`
  MODIFY `id` int(12) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=27;
COMMIT;
