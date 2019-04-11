---
category: pg
---

Oracle到pg的迁移可以用ora2pg，oracle_fdw到工具。今天看到德哥提到的ora-migrator结合oracle_fdw的迁移方式非常简单，顺便测试一下。

Ora-migrator的github主页在这里 <https://github.com/cybertec-postgresql/ora_migrator>

这个extension可以将一个或多个schema下的序列，普通表和他们的约束、索引一起迁移过去。触发器，存过和package得自己迁移。

我自己测试视图迁移会报错，物化视图也不会迁移过去。

## 一、准备阶段

### 1.1 安装Oracle client

```shell
[root@whf307 soft]# rpm -ivh oracle-instantclient11.2-basic-11.2.0.4.0-1.x86_64.rpm
Preparing...                          ################################# [100%]
Updating / installing...
   1:oracle-instantclient11.2-basic-11################################# [100%]
[root@whf307 soft]# rpm -ivh oracle-instantclient11.2-sqlplus-11.2.0.4.0-1.x86_64.rpm
Preparing...                          ################################# [100%]
Updating / installing...
   1:oracle-instantclient11.2-sqlplus-################################# [100%]
[root@whf307 soft]# rpm -ivh oracle-instantclient11.2-devel-11.2.0.4.0-1.x86_64.rpm
Preparing...                          ################################# [100%]
Updating / installing...
   1:oracle-instantclient11.2-devel-11################################# [100%]
```

### 1.2 Oralce环境变量加入到pg用户

```shell
< pg@whf307 ~ 12:59 --> vi .bash_profile 
export PGDATA=/oracle/soft/pgdata11.2
export LANG=C
#export PGHOME=/oracle/soft/pg11
export PGHOME=/oracle/soft/pg11.2
export LD_LIBRARY_PATH=$PGHOME/lib:/lib64:/usr/lib64:/usr/local/lib64:/lib:/usr/lib:/usr/local/lib:/usr/include:$LD_LIBRARY_PATH
export PATH=$PGHOME/bin:$PATH:.
export DATE=`date +"%Y%m%d%H%M"`
export MANPATH=$PGHOME/share/man:$MANPATH
export PGHOST=$PGDATA
export PGUSER=pg
export PGDATABASE=li
export PGPORT=5555
export PS1="< \u@\H \w \A --> "

export ORACLE_BASE=/usr/lib/oracle
export ORACLE_HOME=/usr/lib/oracle/11.2/client64
export ORACLE_SID=wade
export PATH=$ORACLE_HOME/bin:$ORACLE_HOME/OPatch:$PATH:$ORACLE_HOME/rdbms/lib
export TNS_ADMIN=$ORACLE_HOME/network/admin
export LD_LIBRARY_PATH=$ORACLE_HOME/lib:$PGHOME/lib:/lib64:/usr/lib64:/usr/local/lib64:/lib:/usr/lib:/usr/local/lib:/usr/include:$ORACLE_HOME/lib:$ORACLE_HOME/lib32:$LD_LIBRARY_PATH
```

测试连接

```shell
< pg@whf307 ~ 12:59 --> . .bash_profile 
< pg@whf307 ~ 12:59 --> sqlplus system/oracle@127.0.0.1/wade

SQL*Plus: Release 11.2.0.4.0 Production on Fri Mar 15 12:59:40 2019

Copyright (c) 1982, 2013, Oracle.  All rights reserved.


Connected to:
Oracle Database 11g Enterprise Edition Release 11.2.0.4.0 - 64bit Production
With the Partitioning, OLAP, Data Mining and Real Application Testing options

SQL> 
```

### 1.3 安装oracle_fdw

fdw(foreign data wrappers)是pg的外部数据接口， pg中有各种fdw来实现pg和pg或者pg和其他数据库的连接。oracle_fdw是pg的一个扩展，有点像dblink，外部表。下载解压后， make，make install就好了

```sql
< pg@whf307 /oracle/soft/pg 09:11 --> unzip oracle_fdw-ORACLE_FDW_2_1_0.zip  
< pg@whf307 /oracle/soft/pg 09:03 --> cd oracle_fdw-ORACLE_FDW_2_1_0/

< pg@whf307 /oracle/soft/pg/oracle_fdw-ORACLE_FDW_2_1_0 09:03 --> make
< pg@whf307 /oracle/soft/pg/oracle_fdw-ORACLE_FDW_2_1_0 09:03 --> make install
```

### 1.4 安装ora-migrator

Ora-migrator是github上一个pg迁移工具，结合oracle_fdw来迁移很方便。同样下载，解压，make  install

```shell
< pg@whf307 /oracle/soft/pg 09:11 --> unzip ora_migrator-master.zip
< pg@whf307 /oracle/soft/pg 09:11 --> cd ora_migrator-master/

< pg@whf307 /oracle/soft/pg/ora_migrator-master 09:11 --> make install
```

### 1.5  拷贝Oracle的包到pg的软件目录下

```shell
< pg@whf307 /oracle/soft/pg11.2/lib 09:05 --> cd /oracle/soft/pg11.2/lib
< pg@whf307 /oracle/soft/pg11.2/lib 09:05 --> cp /usr/lib/oracle/11.2/client64/lib/libclntsh.so.11.1 .
< pg@whf307 /oracle/soft/pg11.2/lib 09:05 --> cp /usr/lib/oracle/11.2/client64/lib/libnnz11.so .

如果不拷贝会报包缺失
mydb=# create extension oracle_fdw;
ERROR:  could not load library "/oracle/soft/pg_11/lib/postgresql/oracle_fdw.so": libclntsh.so.11.1: cannot open shared object file: No such file or directory
```

### 1.6 新建数据库和extension

```sql
li=# create database orcl;
CREATE DATABASE
li=# \c orcl
You are now connected to database "orcl" as user "pg".
orcl=# \dx
                 List of installed extensions
  Name   | Version |   Schema   |         Description          
---------+---------+------------+------------------------------
 plpgsql | 1.0     | pg_catalog | PL/pgSQL procedural language
(1 row)

orcl=# create extension oracle_fdw;
CREATE EXTENSION
orcl=# CREATE EXTENSION ora_migrator;
CREATE EXTENSION
orcl=# \dx
                             List of installed extensions
     Name     | Version |   Schema   |                   Description                   
--------------+---------+------------+-------------------------------------------------
 ora_migrator | 0.9.1   | public     | Tools to migrate Oracle databases to PostgreSQL
 oracle_fdw   | 1.1     | public     | foreign data wrapper for Oracle access
 plpgsql      | 1.0     | pg_catalog | PL/pgSQL procedural language
(3 rows)

orcl=# 
```

### 1.7 pg数据库新建用户

这里oracle和pg我都使用了超级用户，ora-migrator的说明中oracle用户只要有select any dictionary的权限就可以了。

```sql
orcl=# create user scott  password 'oracle' superuser;
CREATE ROLE
```

### 1.8 Oracle数据库新建用户

```sql
SQL> create user sa identified by oracle;
User created.

SQL> grant dba to sa;
Grant succeeded.
```

### 1.9 创建外部服务

这里相当于建一个连接

```sql
orcl=# \des
       List of foreign servers
 Name | Owner | Foreign-data wrapper 
------+-------+----------------------
(0 rows)

orcl=# create server oracle foreign data wrapper oracle_fdw options (dbserver '//127.0.0.1/wade');
CREATE SERVER
orcl=# \des
        List of foreign servers
  Name  | Owner | Foreign-data wrapper 
--------+-------+----------------------
 oracle | pg    | oracle_fdw
(1 row)
```

### 1.10 创建用户映射

比较oracle这里像dblink用两步来创建

```sql
orcl=#\c orcl scott
You are now connected to database "orcl" as user "scott".

orcl=# create user mapping for scott server oracle options ( user 'sa',password 'oracle');
CREATE USER MAPPING
orcl=# 
```



## 二、迁移

### 2.1 Oracle端数据

```sql
SQL> select object_name,object_type from dba_objects where owner='SC';

OBJECT_NAME          OBJECT_TYPE
-------------------- -------------------
T1                   TABLE
INIT1                TABLE
EMP                  TABLE
TMP_T1               TABLE
SP_PROFILER_TEST1    PROCEDURE
DEMO                 TABLE
PK_DEMO              INDEX
SEQTEST              SEQUENCE
V_T1                 VIEW
MV_T1                TABLE
MV_T1                MATERIALIZED VIEW
GET_ROWID            FUNCTION

12 rows selected.

SQL> select count(*) from sc.t1;

  COUNT(*)
----------
     16063

SQL> 
```

### 2.2 pg端数据

```sql
orcl=# \dn
List of schemas
  Name  | Owner 
--------+-------
 public | pg
(1 row)

orcl=# select count(*) from pg_tables where schemaname='sc';
 count 
-------
     0
(1 row)

orcl=# 
```

###  2.3  开始迁移

```sql
orcl=# SELECT oracle_migrate(server => 'oracle', only_schemas => '{SC}'); 
NOTICE:  Creating staging schemas "ora_stage" and "pgsql_stage" ...
NOTICE:  Creating Oracle metadata views in schema "ora_stage" ...
NOTICE:  Copy definitions to PostgreSQL staging schema "pgsql_stage" ...
NOTICE:  Creating schemas ...
NOTICE:  Creating sequences ...
NOTICE:  Creating foreign tables ...
NOTICE:  Migrating table sc.demo ...
NOTICE:  Migrating table sc.emp ...
NOTICE:  Migrating table sc.init1 ...
NOTICE:  Migrating table sc.t1 ...
WARNING:  Error creating view sc.v_t1
DETAIL:  column "OWNER" does not exist: 
NOTICE:  Creating UNIQUE and PRIMARY KEY constraints ...
NOTICE:  Creating FOREIGN KEY constraints ...
NOTICE:  Creating CHECK constraints ...
NOTICE:  Creating indexes ...
NOTICE:  Setting column default values ...
NOTICE:  Dropping staging schemas ...
NOTICE:  Migration completed with 1 errors.
 oracle_migrate 
----------------
              1
(1 row)

orcl=# 
```

可以看到输出很详细，有报错也会输出到前台。

### 2.4  验证数据

```sql
orcl=# select count(*) from sc.t1;
 count 
-------
 16063
(1 row)

orcl=# 

orcl=# select * from pg_tables where schemaname='sc';
 schemaname | tablename | tableowner | tablespace | hasindexes | hasrules | hastriggers | rowsecurity 
------------+-----------+------------+------------+------------+----------+-------------+-------------
 sc         | demo      | scott      |            | t          | f        | f           | f
 sc         | emp       | scott      |            | f          | f        | f           | f
 sc         | init1     | scott      |            | f          | f        | f           | f
 sc         | t1        | scott      |            | f          | f        | f           | f
(4 rows)

orcl=# select schemaname,tablename,tableowner from pg_tables where schemaname='sc';
 schemaname | tablename | tableowner 
------------+-----------+------------
 sc         | demo      | scott
 sc         | emp       | scott
 sc         | init1     | scott
 sc         | t1        | scott
(4 rows)

orcl=# select schemaname,sequencename,sequenceowner from pg_sequences where schemaname='sc';
 schemaname | sequencename | sequenceowner 
------------+--------------+---------------
 sc         | seqtest      | scott
(1 row)


orcl=# select  * from pg_indexes where schemaname='sc';
 schemaname | tablename | indexname | tablespace |                         indexdef                          
------------+-----------+-----------+------------+-----------------------------------------------------------
 sc         | demo      | demo_pkey |            | CREATE UNIQUE INDEX demo_pkey ON sc.demo USING btree (id)
(1 row)

orcl=# 
```





#### 可以看到用ora-migrator+oracle_fdw很方便地将schema用户下的sequence，table和index迁移到了pg中。具体环境可以多多测试，真的是很方便了。





「插件下载」

<https://github.com/laurenz/oracle_fdw/releases>

<https://github.com/cybertec-postgresql/ora_migrator>



「参考文章」

<https://github.com/digoal/blog/blob/master/201903/20190311_01.md?from=timeline&isappinstalled=0>