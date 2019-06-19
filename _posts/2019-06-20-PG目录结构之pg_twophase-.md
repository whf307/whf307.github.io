---
category: pg
---

pg的数据库目录有点多，仅仅知道是做什么的远远不够，今天开始学习他的目录结构。

###  一、pg的目录结构

我这里用了目前最新的12.1。目录结构如下：

```
[pg12@enmodb2 pg_twophase]$ ls -rtl ..
total 136
drwx------ 2 pg12 pg12  4096 Jun 14 11:08 pg_snapshots         ------->存放快照信息文件
drwx------ 2 pg12 pg12  4096 Jun 14 11:08 pg_serial            ------->已提交的可串行事务信息
drwx------ 2 pg12 pg12  4096 Jun 14 11:08 pg_replslot          ------->复制槽数据
drwx------ 4 pg12 pg12  4096 Jun 14 11:08 pg_multixact         ------->多事务状态数据
drwx------ 2 pg12 pg12  4096 Jun 14 11:08 pg_dynshmem          ------->动态共享内存子系统使用
drwx------ 2 pg12 pg12  4096 Jun 14 11:08 pg_commit_ts         ------->事务提交的时间戳数据
-rw------- 1 pg12 pg12     3 Jun 14 11:08 PG_VERSION           ------->pg版本
-rw------- 1 pg12 pg12  1636 Jun 14 11:08 pg_ident.conf        ------->代理配置文件
-rw------- 1 pg12 pg12  4513 Jun 14 11:08 pg_hba.conf          ------->访问限制配置文件
drwx------ 2 pg12 pg12  4096 Jun 14 11:08 pg_xact              ------->事务提交状态文件
drwx------ 3 pg12 pg12  4096 Jun 14 11:08 pg_wal               ------->wal目录
drwx------ 2 pg12 pg12  4096 Jun 14 11:08 pg_subtrans          ------->子事务状态文件夹
drwx------ 5 pg12 pg12  4096 Jun 14 11:08 base                 ------->数据库子目录存放位置
-rw------- 1 pg12 pg12 26671 Jun 14 11:09 postgresql.conf      ------->参数文件
drwx------ 2 pg12 pg12  4096 Jun 18 11:06 pg_tblspc            ------->表空间连接目录
-rw------- 1 pg12 pg12   121 Jun 20 00:25 postgresql.auto.conf ------->alter命令的保存文件
-rw------- 1 pg12 pg12    26 Jun 20 00:26 postmaster.opts      ------->主程序文件
drwx------ 2 pg12 pg12  4096 Jun 20 00:26 pg_notify            ------->listen\notify状态
-rw------- 1 pg12 pg12    73 Jun 20 00:26 postmaster.pid       ------->启动进程文件
drwx------ 2 pg12 pg12  4096 Jun 20 00:26 pg_stat              ------->统计子系统的永久文件
drwx------ 2 pg12 pg12  4096 Jun 20 00:26 global               ------->系统表以及控制文件
drwx------ 4 pg12 pg12  4096 Jun 20 00:30 pg_logical           ------->逻辑解码状态数据
drwx------ 2 pg12 pg12  4096 Jun 20 00:30 pg_twophase          ------->2阶段提交状态文件
drwx------ 2 pg12 pg12  4096 Jun 20 00:31 pg_stat_tmp          ------->统计子系统临时文件
[pg12@enmodb2 pg_twophase]$ 
```

### 二、如何开始分布式事务

这个目录看名字就知道是为分布式事务而用的，而且是2阶段提交的机制。这个目录下存放的就是分布式事务的状态文件。

用PREPARE TRANSACTION+gid（分布式事务id）来开启一个分布式事务。2阶段提交有2个使用前提：1、在事务中才能使用这个命令；2、max_prepared_transactions>0

```
[pg12@enmodb2 pg_twophase]$ psql
psql (12beta1)
Type "help" for help.

postgres=# PREPARE TRANSACTION 'the first prepared transactionx';
psql: WARNING:  there is no transaction in progress
ROLLBACK
postgres=# begin;
BEGIN
postgres=# PREPARE TRANSACTION 'the first prepared transactionx';
PREPARE TRANSACTION
postgres=# 
```

```
postgres=# begin;
BEGIN
postgres=# PREPARE TRANSACTION 'the first prepared transaction';
psql: ERROR:  prepared transactions are disabled
HINT:  Set max_prepared_transactions to a nonzero value.
postgres=# show max_prepared_transactions;
 max_prepared_transactions 
---------------------------
 0
(1 row)
           
postgres=# alter system set max_prepared_transactions=10;
ALTER SYSTEM
postgres=# show max_prepared_transactions;
 max_prepared_transactions 
---------------------------
 0
(1 row)

postgres=# \q
[pg12@enmodb2 pg_twophase]$ pg_ctl stop
waiting for server to shut down.... done
server stopped
[pg12@enmodb2 pg_twophase]$ pg_ctl start -l ../alert.logg 
waiting for server to start.... done
server started
[pg12@enmodb2 pg_twophase]$ 
[pg12@enmodb2 pg_twophase]$ psql
psql (12beta1)
Type "help" for help.

postgres=# show max_prepared_transactions;
 max_prepared_transactions 
---------------------------
 10
(1 row)
postgres=# begin;
BEGIN
postgres=# PREPARE TRANSACTION 'the first prepared transaction';
PREPARE TRANSACTION
```



### 三、pg_twophase

这个目录下存放的是分布式事务状态文件。文件名一般为8个16进制位，存放着gid

```
[pg12@enmodb2 pg_twophase]$ ls -rtl
total 4
-rw------- 1 pg12 pg12 1732 Jun 20 00:30 000001F4
[pg12@enmodb2 pg_twophase]$ file 000001F4
000001F4: data
[pg12@enmodb2 pg_twophase]$ strings 000001F4
the first prepared transaction
```

不要去随意更改或者破坏这些文件，可能会导致分布式事务状态异常。例如删了这些文件rollback分布式事务会报错

```
postgres=# rollback prepared 'the first prepared transactionx';
psql: ERROR:  could not open file "pg_twophase/000001F5": No such file or directory
```

如果重启数据库，这个被删了的分布式事务才会消失

```
[pg12@enmodb2 ~]$ pg_ctl stop
waiting for server to shut down.... done
server stopped
[pg12@enmodb2 ~]$ pg_ctl start -l ./alert.log
waiting for server to start.... done
server started
[pg12@enmodb2 ~]$ psql
psql (12beta1)
Type "help" for help.

postgres=# SELECT * FROM pg_prepared_xacts;
 transaction | gid | prepared | owner | database 
-------------+-----+----------+-------+----------
(0 rows)

postgres=# 
```



### 四、体验分布式事务

#### 4.1 普通事务

只要没有提交肯定不在了，哪怕退出当前会话

```
postgres=# create table demo1(id int,name varchar(10));
CREATE TABLE

postgres=# \set AUTOCOMMIT off
postgres=# \echo :AUTOCOMMIT  
off
postgres=# insert into demo1 values(2,'jsonX');
INSERT 0 1
postgres=# select * from demo1;
 id | name  
----+-------
  1 | json
  2 | jsonX
(2 rows)

postgres=# \q
[pg12@enmodb2 ~]$ psql
psql (12beta1)
Type "help" for help.

postgres=# select * from demo1;
 id | name 
----+------
  1 | json
(1 row)

postgres=# 
```

#### 4.2 体验分布式事务

```
pg12@enmodb2 ~]$ psql
psql (12beta1)
Type "help" for help.

postgres=# \set AUTOCOMMIT off
postgres=# \echo :AUTOCOMMIT
off
postgres=# prepare transaction 'demo1 test';
psql: WARNING:  there is no transaction in progress
ROLLBACK
postgres=# select * from demo1;
 id | name 
----+------
  1 | json
(1 row)

postgres=# insert into demo1 values(2,'x');
INSERT 0 1
postgres=#  prepare transaction 'demo1 test';
PREPARE TRANSACTION
postgres=# SELECT * FROM pg_prepared_xacts;
 transaction |    gid     |           prepared            | owner | database 
-------------+------------+-------------------------------+-------+----------
         507 | demo1 test | 2019-06-20 01:22:18.794777+08 | pg12  | postgres
(1 row)
```

分布式事务，哪怕数据库重启了，事务依然存在，除非rollback或者commit

```
[pg12@enmodb2 ~]$ pg_ctl stop
waiting for server to shut down.... done
server stopped
[pg12@enmodb2 ~]$ pg_ctl start -l ./alert.log  
waiting for server to start.... done
server started
[pg12@enmodb2 ~]$ psql
psql (12beta1)
Type "help" for help.

postgres=# SELECT * FROM pg_prepared_xacts;
 transaction |    gid     |           prepared            | owner | database 
-------------+------------+-------------------------------+-------+----------
         507 | demo1 test | 2019-06-20 01:22:18.794777+08 | pg12  | postgres
(1 row)

postgres=# select * from demo1;
 id | name 
----+------
  1 | json
(1 row)

postgres=# commit prepared 'demo1 test';
COMMIT PREPARED
postgres=# select * from demo1;
 id | name 
----+------
  1 | json
  2 | x
(2 rows)
```

rollback一个分布式事务命令如下：

```
rollback prepared 'demo1 test';
```

rollback的前提是pg_twophase中的状态文件正常。