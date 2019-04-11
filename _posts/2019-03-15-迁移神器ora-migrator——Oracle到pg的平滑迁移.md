---
category: pg
---

Oracle到pg的迁移可以用ora2pg，oracle_fdw到工具。之前看到德哥提到的ora-migrator结合oracle_fdw的迁移方式非常简单，最近有空了来测试一下。

Ora-migrator的github主页在这里 <https://github.com/cybertec-postgresql/ora_migrator>

这个extension可以将一个或多个schema下的序列，普通表和他们的约束、索引一起迁移过去。临时表、触发器、物化视图、视图、存储过程和function得自己迁移。

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

### 1.8 Oracle数据库新建迁移用户

```sql
SQL> create user sa identified by oracle;
User created.

SQL> grant dba to sa;
Grant succeeded.
```

### 1.9 创建外部服务

这里相当于建一个连接

```sql
orcl=#\c orcl scott
You are now connected to database "orcl" as user "scott".

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
orcl=# create user mapping for scott server oracle options ( user 'sa',password 'oracle');
CREATE USER MAPPING
orcl=# 
```



## 二、表和索引的迁移

### 2.1 Oracle端数据

```sql
SQL> select object_type,count(*) from dba_objects where owner='SC' group by object_type order by 2;

OBJECT_TYPE           COUNT(*)
------------------- ----------
VIEW                         1
MATERIALIZED VIEW            1
FUNCTION                     1
SEQUENCE                     1
PROCEDURE                    2
INDEX                        4
TABLE                        4

7 rows selected.

SQL>  select object_name,object_type from dba_objects where owner='SC';

OBJECT_NAME                    OBJECT_TYPE
------------------------------ -------------------
T2                             TABLE
T1                             TABLE
PK_T1                          INDEX
PK_T2                          INDEX
IND_T1_NAME                    INDEX
STAT_P4                        PROCEDURE
MV_T1                          TABLE
PK_T11                         INDEX
MV_T1                          MATERIALIZED VIEW
TMP_T1                         TABLE
SP_PROFILER_TEST1              PROCEDURE
SEQTEST                        SEQUENCE
V_T1                           VIEW
GET_ROWID                      FUNCTION

14 rows selected.

SQL> 
```

### 2.2 pg端数据

obj.sql是一个检查对象数量的脚本，可以用来比对数据，脚本在文末

```sql
orcl=# \i obj.sql
 database | user | schema | reltype | count 
----------+------+--------+---------+-------
(0 rows)

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
NOTICE:  Migrating table sc.t1 ...
NOTICE:  Migrating table sc.t2 ...
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


orcl=# \i obj.sql  
 database | user  | schema |    reltype    | count 
----------+-------+--------+---------------+-------
 orcl     | scott | sc     | sequence      |     1
 orcl     | scott | sc     | table         |     2
 orcl     | scott | sc     | index         |     3
(4 rows)

orcl=# 
```

可以看到输出很详细，有报错也会输出到前台。

#### 2.4 可能遇到的问题

我这里遇到了 OCIEnvCreate的错误，但是我检查所有的环境变量都是ok的，最后重启pg解决

```sql
orcl=# SELECT oracle_migrate(server => 'oracle', only_schemas => '{SC}'); 
WARNING:  Cannot establish connection with foreign server "oracle"
ERROR:  error connecting to Oracle: OCIEnvCreate failed to create environment handle
DETAIL:  
CONTEXT:  SQL statement "SELECT oracle_diag(server)"
PL/pgSQL function public.oracle_migrate_prepare(name,name,name,name[],integer) line 16 at PERFORM
PL/pgSQL function public.oracle_migrate(name,name,name,name[],integer,boolean) line 15 at assignment
orcl=# SELECT oracle_diag();
                         oracle_diag                         
-------------------------------------------------------------
 oracle_fdw 2.1.0, PostgreSQL 11.2, Oracle client 11.2.0.4.0
(1 row)

```

### 2.5 验证数据

oracle端

```
SQL> select count(*) from sc.t1;

  COUNT(*)
----------
      3701

SQL> 

SQL> desc sc.t1
 Name                    Null?    Type
 ----------------------- -------- ----------------
 OWNER                   NOT NULL VARCHAR2(30)
 OBJECT_NAME             NOT NULL VARCHAR2(30)
 SUBOBJECT_NAME                   VARCHAR2(30)
 OBJECT_ID               NOT NULL NUMBER
 DATA_OBJECT_ID          NOT NULL NUMBER
 OBJECT_TYPE                      VARCHAR2(19)
 CREATED                 NOT NULL DATE
 LAST_DDL_TIME           NOT NULL DATE
 TIMESTAMP                        VARCHAR2(19)
 STATUS                           VARCHAR2(7)
 TEMPORARY                        VARCHAR2(1)
 GENERATED                        VARCHAR2(1)
 SECONDARY                        VARCHAR2(1)
 NAMESPACE               NOT NULL NUMBER
 EDITION_NAME                     VARCHAR2(30)

SQL> 
```

pg端

```sql
orcl=# select count(*) from sc.t1;
 count 
-------
  3701
(1 row)

orcl=# \d sc.t1
                                  Table "sc.t1"
     Column     |              Type              | Collation | Nullable | Default 
----------------+--------------------------------+-----------+----------+---------
 owner          | character varying(30)          |           | not null | 
 object_name    | character varying(30)          |           | not null | 
 subobject_name | character varying(30)          |           |          | 
 object_id      | numeric                        |           | not null | 
 data_object_id | numeric                        |           | not null | 
 object_type    | character varying(19)          |           |          | 
 created        | timestamp(0) without time zone |           | not null | 
 last_ddl_time  | timestamp(0) without time zone |           | not null | 
 timestamp      | character varying(19)          |           |          | 
 status         | character varying(7)           |           |          | 
 temporary      | character varying(1)           |           |          | 
 generated      | character varying(1)           |           |          | 
 secondary      | character varying(1)           |           |          | 
 namespace      | numeric                        |           | not null | 
 edition_name   | character varying(30)          |           |          | 
Indexes:
    "t1_pkey" PRIMARY KEY, btree (data_object_id)
    "t1_object_name_idx" btree (object_name)
Check constraints:
    "t1_object_id_check" CHECK (object_id > 0::numeric)
Referenced by:
    TABLE "sc.t2" CONSTRAINT "t2_data_object_id_fkey" FOREIGN KEY (data_object_id) REFERENCES sc.t1(data_object_id)

orcl=# 
```

说明：

1、表、索引、约束和sequence都可以一次性迁移

2、临时表、物化视图、视图、存储过程、function，job需要人肉迁移



### 三、其他对象迁移

#### 3.1 临时表和触发器

临时表可以找出ddl，然后去创建

```
SQL> set long 10000
SQL> select dbms_metadata.get_ddl('TABLE','TMP_T1','SC') from dual;

DBMS_METADATA.GET_DDL('TABLE','TMP_T1','SC')
--------------------------------------------------------------------------------

  CREATE GLOBAL TEMPORARY TABLE "SC"."TMP_T1"
   (    "OWNER" VARCHAR2(30) NOT NULL ENABLE,
        "OBJECT_NAME" VARCHAR2(30) NOT NULL ENABLE,
        "SUBOBJECT_NAME" VARCHAR2(30),
        "OBJECT_ID" NUMBER NOT NULL ENABLE,
        "DATA_OBJECT_ID" NUMBER,
        "OBJECT_TYPE" VARCHAR2(19),
        "CREATED" DATE NOT NULL ENABLE,
        "LAST_DDL_TIME" DATE NOT NULL ENABLE,
        "TIMESTAMP" VARCHAR2(19),
        "STATUS" VARCHAR2(7),
        "TEMPORARY" VARCHAR2(1),
        "GENERATED" VARCHAR2(1),
        "SECONDARY" VARCHAR2(1),
        "NAMESPACE" NUMBER NOT NULL ENABLE,
        "EDITION_NAME" VARCHAR2(30)
   ) ON COMMIT PRESERVE ROWS


SQL> 
```

需要注意

1、数据类型的转换，比如number和varchar2对应的是int和varchar(int具体长度根据实际情况决定)

2、临时表的创建不能指定schema

```
ERROR:  cannot create temporary relation in non-temporary schema
```

3、11.2 不推荐使用global的临时表了

```
WARNING:  GLOBAL is deprecated in temporary table creation
```

4、pg的临时表会话结束后会自动删除，这也是需要特别注意的地方，也就是说每个会话需要单独创建。

创建如下

```
orcl=# CREATE  TEMPORARY TABLE "TMP_T1"
orcl-#    (    "OWNER" VARCHAR(30) NOT NULL ,
orcl(#         "OBJECT_NAME" VARCHAR(30) NOT NULL ,
orcl(#         "SUBOBJECT_NAME" VARCHAR(30),
orcl(#         "OBJECT_ID" int NOT NULL ,
orcl(#         "DATA_OBJECT_ID" int,
orcl(#         "OBJECT_TYPE" VARCHAR(19),
orcl(#         "CREATED" DATE NOT NULL ,
orcl(#         "LAST_DDL_TIME" DATE NOT NULL ,
orcl(#         "TIMESTAMP" VARCHAR(19),
orcl(#         "STATUS" VARCHAR(7),
orcl(#         "TEMPORARY" VARCHAR(1),
orcl(#         "GENERATED" VARCHAR(1),
orcl(#         "SECONDARY" VARCHAR(1),
orcl(#         "NAMESPACE" int NOT NULL ,
orcl(#         "EDITION_NAME" VARCHAR(30)
orcl(#    ) ON COMMIT drop
orcl-# ;
CREATE TABLE
orcl=# 
```

触发器也通过获取ddl去创建



#### 3.2 其他对象

其他对象可以用expdp+impdp sqlfile导出ddl到sqlfile指定的文件，修改加工之后再去pg里面创建

```shell
[oracle@whf307 soft]$ expdp \'/ as sysdba\' directory=dmp dumpfile=pg.dmp logfile=pg.log schemas=sc include=MATERIALIZED_VIEW,procedure,function,view

Export: Release 11.2.0.4.0 - Production on Fri Apr 12 01:50:02 2019

Copyright (c) 1982, 2011, Oracle and/or its affiliates.  All rights reserved.

Connected to: Oracle Database 11g Enterprise Edition Release 11.2.0.4.0 - 64bit Production
With the Partitioning, OLAP, Data Mining and Real Application Testing options
FLASHBACK automatically enabled to preserve database integrity.
Starting "SYS"."SYS_EXPORT_SCHEMA_01":  "/******** AS SYSDBA" directory=dmp dumpfile=pg.dmp logfile=pg.log schemas=sc include=MATERIALIZED_VIEW,procedure,function,view 
Estimate in progress using BLOCKS method...
Total estimation using BLOCKS method: 0 KB
Processing object type SCHEMA_EXPORT/FUNCTION/FUNCTION
Processing object type SCHEMA_EXPORT/PROCEDURE/PROCEDURE
Processing object type SCHEMA_EXPORT/FUNCTION/ALTER_FUNCTION
Processing object type SCHEMA_EXPORT/PROCEDURE/ALTER_PROCEDURE
Processing object type SCHEMA_EXPORT/VIEW/VIEW
Processing object type SCHEMA_EXPORT/MATERIALIZED_VIEW
Master table "SYS"."SYS_EXPORT_SCHEMA_01" successfully loaded/unloaded
******************************************************************************
Dump file set for SYS.SYS_EXPORT_SCHEMA_01 is:
  /oracle/soft/pg.dmp
Job "SYS"."SYS_EXPORT_SCHEMA_01" successfully completed at Fri Apr 12 01:50:07 2019 elapsed 0 00:00:04

[oracle@whf307 soft]$ impdp \'/ as sysdba \' directory=dmp dumpfile=pg.dmp sqlfile=other.sql

Import: Release 11.2.0.4.0 - Production on Fri Apr 12 01:50:20 2019

Copyright (c) 1982, 2011, Oracle and/or its affiliates.  All rights reserved.

Connected to: Oracle Database 11g Enterprise Edition Release 11.2.0.4.0 - 64bit Production
With the Partitioning, OLAP, Data Mining and Real Application Testing options
Master table "SYS"."SYS_SQL_FILE_FULL_01" successfully loaded/unloaded
Starting "SYS"."SYS_SQL_FILE_FULL_01":  "/******** AS SYSDBA" directory=dmp dumpfile=pg.dmp sqlfile=other.sql 
Processing object type SCHEMA_EXPORT/FUNCTION/FUNCTION
Processing object type SCHEMA_EXPORT/PROCEDURE/PROCEDURE
Processing object type SCHEMA_EXPORT/FUNCTION/ALTER_FUNCTION
Processing object type SCHEMA_EXPORT/PROCEDURE/ALTER_PROCEDURE
Processing object type SCHEMA_EXPORT/VIEW/VIEW
Processing object type SCHEMA_EXPORT/MATERIALIZED_VIEW
Job "SYS"."SYS_SQL_FILE_FULL_01" successfully completed at Fri Apr 12 01:50:21 2019 elapsed 0 00:00:01

[oracle@cs-db soft]$ 
```

pg的存储过程和oracle的写法还是有一点区别，这里需要去修改的，具体不在赘述，修改都pg的语法去创建就好了。



附：

「obj.sql」

```sql
SELECT current_database() AS DATABASE,rolname as user,
       nspname AS SCHEMA,
       CASE
           WHEN relkind='r' THEN 'table'
           WHEN relkind='i' THEN 'index'
           WHEN relkind='S' THEN 'sequence'
           WHEN relkind='t' THEN 'TOAST'
           WHEN relkind='v' THEN 'view'
           WHEN relkind='m' THEN 'materialized view'
           WHEN relkind='c' THEN 'composite type'
           WHEN relkind='f' THEN 'foreign table'
           WHEN relkind='p' THEN 'partitioned table'
           WHEN relkind='I' THEN 'partitioned index'
       END AS reltype,
       count(*)
FROM pg_class a,
     pg_namespace b,
     pg_authid c
WHERE a.relnamespace=b.oid
and a.relowner=c.oid
  AND nspname NOT IN ('pg_catalog',
                      'pg_toast',
                      'information_schema')
GROUP BY nspname,rolname,
         relkind
ORDER BY 5,2;
```

「插件下载」

<https://github.com/laurenz/oracle_fdw/releases>

<https://github.com/cybertec-postgresql/ora_migrator>



「参考文章」

<https://github.com/digoal/blog/blob/master/201903/20190311_01.md?from=timeline&isappinstalled=0>