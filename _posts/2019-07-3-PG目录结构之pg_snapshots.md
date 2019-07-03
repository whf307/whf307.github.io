---
category: pg
---

今天来看看pg_snapshots这个目录以及相关的知识点。

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

### 二、snapshot

顾名思义，这个快照是mvcc的一种方式。每个SQL都可以看到一份快照数据（某一时刻的数据，**比如可重复读的隔离级别下的session**）。可以参考pg文档，并发访问控制部分 <https://www.postgresql.org/docs/11/mvcc-intro.html>

​	PostgreSQL provides a rich set of tools for developers to manage concurrent access to data. Internally, data consistency is maintained by using a multiversion model (Multiversion Concurrency Control, MVCC). This means that each SQL statement sees a snapshot of data (a *database version*) as it was some time ago, regardless of the current state of the underlying data. This prevents statements from viewing inconsistent data produced by concurrent transactions performing updates on the same data rows, providing *transaction isolation* for each database session. MVCC, by eschewing the locking methodologies of traditional database systems, minimizes lock contention in order to allow for reasonable performance in multiuser environments.



### 三、old_snapshot_threshold

这个参数控制着数据库保留dead tuple的时间。默认是-1禁用的，修改需要重启。可选值有 ：

```
1min-60d
-1 disables
0 is immediate
```

#### 3.1 设置为1分钟

```
postgres=# show old_snapshot_threshold;
 old_snapshot_threshold 
------------------------
 -1
(1 row)

postgres=# alter system set old_snapshot_threshold=1;
ALTER SYSTEM
postgres=# show old_snapshot_threshold;
 old_snapshot_threshold 
------------------------
 -1
(1 row)

postgres=# \q


[pg12@whf307 ~]$ pg_ctl stop
waiting for server to shut down.... done
server stopped
[pg12@whf307 ~]$ pg_ctl start -l ./alert.log
waiting for server to start.... done
server started

[pg12@whf307 ~]$ psql
psql (12beta1)
Type "help" for help.

postgres=# show old_snapshot_threshold;
 old_snapshot_threshold 
------------------------
 1min
(1 row)
```

#### 3.2 session A 开启一个可重复读隔离级别的事务去查询t3表

```
[pg12@whf307 ~]$ psql mydb
psql (12beta1)
Type "help" for help.

mydb=# begin transaction isolation level repeatable read;
BEGIN
mydb=# select now();
              now              
-------------------------------
 2019-07-03 17:11:30.326306+08
(1 row)

mydb=# select  * from t3;
 owner |  object_name   | object_id | data_object_id | object_type |       created       
-------+----------------+-----------+----------------+-------------+---------------------
 SYS   | I_FILE#_BLOCK# |         9 |              9 | INDEX       | 2018-02-07 19:20:25
 SYS   | I_OBJ3         |        38 |             38 | INDEX       | 2018-02-07 19:20:25
 SYS   | I_TS1          |        45 |             45 | INDEX       | 2018-02-07 19:20:25
 SYS   | I_CON1         |        51 |             51 | INDEX       | 2018-02-07 19:20:25
 SYS   | IND$           |        19 |              2 | TABLE       | 2018-02-07 19:20:25
 SYS   | CDEF$          |        31 |             29 | TABLE       | 2018-02-07 19:20:25
 SYS   | C_TS#          |         6 |              6 | CLUSTER     | 2018-02-07 19:20:25
 SYS   | I_CCOL2        |        58 |             58 | INDEX       | 2018-02-07 19:20:25
 SYS   | I_PROXY_DATA$  |        24 |             24 | INDEX       | 2018-02-07 19:20:25
 SYS   | I_CDEF4        |        56 |             56 | INDEX       | 2018-02-07 19:20:25
 SYS   | I_TAB1         |        33 |             33 | INDEX       | 2018-02-07 19:20:25
 me    | y              |           |                |             | 
(12 rows)
```

#### 3.3 session B 去修改这个表

```
[pg12@whf307 ~]$ psql mydb
psql (12beta1)
Type "help" for help.

mydb=# update t3 set object_name='x' where owner='me';
UPDATE 1
mydb=# 
```

#### 3.4 等1分钟session A再去查这个表

```
mydb=# select  * from t3;
psql: ERROR:  snapshot too old
mydb=# 
```

可以看到出现了快照过旧的报错。我们设置了快照保留时间1分钟，超过这个时间的快照数据查询都会报错（在REPEATABLE READ 和 SERIALIZABLE 的隔离级别下）。



### 四、pg_snapshots目录

#### 4.1 pg_export_snapshot()

这个function可以查看当前的快照

```
[pg12@whf307 ~]$ psql mydb
psql (12beta1)
Type "help" for help.

mydb=# begin transaction isolation level repeatable read;
BEGIN
mydb=# select pg_export_snapshot();
 pg_export_snapshot  
---------------------
 00000007-000000C6-1
(1 row)

mydb=# 
```

#### 4.2 REPEATABLE READ 和 SERIALIZABLE下会在$PGDATA/pg_snapshots下面生成对应的文件

```
[pg12@whf307 pg_snapshots]$ ls
00000007-000000C6-1
[pg12@whf307 pg_snapshots]$ file 00000007-000000C6-1 
00000007-000000C6-1: ASCII text
[pg12@whf307 pg_snapshots]$ more 00000007-000000C6-1 
vxid:7/198
pid:2182
dbid:18051
iso:2
ro:0
xmin:1167
xmax:1167
xcnt:0
sof:0
sxcnt:0
rec:0
[pg12@enmodb2 pg_snapshots]$ 
```



|       | 含义                   |
| ----- | ---------------------- |
| vxid  | virtualxid，虚拟事务id |
| pid   | 查询快照的会话pid      |
| dbid  | pg_database.oid        |
| iso   |                        |
| ro    |                        |
| xmin  |                        |
| xmax  |                        |
| xcnt  |                        |
| sof   |                        |
| sxcnt |                        |
| rec   |                        |

如果之前的 pg_export_snapshot的事务结束，这里的文件也会消失。

### 4.3 另外一个会话设置snapshot

```
[pg12@enmodb2 ~]$ psql mydb
psql (12beta1)
Type "help" for help.

mydb=# BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ;
BEGIN
mydb=# SET TRANSACTION SNAPSHOT '00000007-000000C6-1';
SET
mydb=# 
```

这样这个事务就只能看到这个快照点的数据了。



更多参考

https://www.postgresql.org/docs/current/sql-set-transaction.html

