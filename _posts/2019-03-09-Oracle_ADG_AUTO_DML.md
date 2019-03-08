---
category: oracle
---

2019-02-14 Oracle 发布了19C for Exadata，说说我比较关注的新特性。3月的DB-Engine Oracle的得分增长很大。下面留个纪念

| Rank     | DBMS                                              | Database Model                                 | Score                                                        |                                                              |          |        |        |
| -------- | ------------------------------------------------- | ---------------------------------------------- | ------------------------------------------------------------ | ------------------------------------------------------------ | -------- | ------ | ------ |
| Mar 2019 | Feb 2019                                          | Mar 2018                                       | Mar 2019                                                     | Feb 2019                                                     | Mar 2018 |        |        |
| 1.       | 1.                                                | 1.                                             | [Oracle ![detailed information](https://db-engines.com/moreattributes.png)](https://db-engines.com/en/system/Oracle) | [Relational](https://db-engines.com/en/article/RDBMS), Multi-model ![img](https://db-engines.com/info.png) | 1279.14  | +15.12 | -10.47 |
| 2.       | 2.                                                | 2.                                             | [MySQL ![detailed information](https://db-engines.com/moreattributes.png)](https://db-engines.com/en/system/MySQL) | [Relational](https://db-engines.com/en/article/RDBMS), Multi-model ![img](https://db-engines.com/info.png) | 1198.25  | +30.96 | -30.62 |
| 3.       | 3.                                                | 3.                                             | [Microsoft SQL Server ![detailed information](https://db-engines.com/moreattributes.png)](https://db-engines.com/en/system/Microsoft+SQL+Server) | [Relational](https://db-engines.com/en/article/RDBMS), Multi-model ![img](https://db-engines.com/info.png) | 1047.85  | +7.79  | -56.94 |
| 4.       | 4.                                                | 4.                                             | [PostgreSQL ![detailed information](https://db-engines.com/moreattributes.png)](https://db-engines.com/en/system/PostgreSQL) | [Relational](https://db-engines.com/en/article/RDBMS), Multi-model ![img](https://db-engines.com/info.png) | 469.81   | -3.75  | +70.46 |
| 5.       | 5.                                                | 5.                                             | [MongoDB ![detailed information](https://db-engines.com/moreattributes.png)](https://db-engines.com/en/system/MongoDB) | [Document](https://db-engines.com/en/article/Document+Stores) | 401.34   | +6.24  | +60.82 |
| 6.       | 6.                                                | 6.                                             | [IBM Db2 ![detailed information](https://db-engines.com/moreattributes.png)](https://db-engines.com/en/system/IBM+Db2) | [Relational](https://db-engines.com/en/article/RDBMS), Multi-model ![img](https://db-engines.com/info.png) | 177.20   | -2.23  | -9.47  |
| 7.       | ![up arrow](https://db-engines.com/up.gif) 9.     | 7.                                             | [Microsoft Access](https://db-engines.com/en/system/Microsoft+Access) | [Relational](https://db-engines.com/en/article/RDBMS)        | 146.20   | +2.18  | +14.26 |
| 8.       | ![down arrow](https://db-engines.com/down.gif) 7. | 8.                                             | [Redis ![detailed information](https://db-engines.com/moreattributes.png)](https://db-engines.com/en/system/Redis) | [Key-value](https://db-engines.com/en/article/Key-value+Stores), Multi-model ![img](https://db-engines.com/info.png) | 146.12   | -3.32  | +14.90 |
| 9.       | ![down arrow](https://db-engines.com/down.gif) 8. | 9.                                             | [Elasticsearch ![detailed information](https://db-engines.com/moreattributes.png)](https://db-engines.com/en/system/Elasticsearch) | [Search engine](https://db-engines.com/en/article/Search+Engines), Multi-model ![img](https://db-engines.com/info.png) | 142.79   | -2.46  | +14.25 |
| 10       | 10.                                               | ![up arrow](https://db-engines.com/up.gif) 11. | [SQLite ![detailed information](https://db-engines.com/moreattributes.png)](https://db-engines.com/en/system/SQLite) | [Relational](https://db-engines.com/en/article/RDBMS)        | 124.87   | -1.29  | +10.06 |

## 一、 Automatic Indexing

```
The automatic indexing feature automates index management tasks, such as creating, rebuilding, and dropping indexes in an Oracle database based on changes in the application workload.

This feature improves database performance by managing indexes automatically in an Oracle database.
```

这将是一个巨大的飞跃，索引对数据库太重要了。智能化的索引更符合趋势，也大大减少了DBA和开发人员的工作量。由"_optimizer_use_auto_indexes"这个隐含参数控制 。



## 二、DML on ADG

### 2.1 配置生效

可以在system和session级别配置

Automatic redirection of DML operations to the primary can be configured at the system level or the session level. The session level setting overrides the system level setting.

To configure automatic redirection of DML operations for all standby sessions in an Active Data Guard environment:

```
Set the ADG_REDIRECT_DML initialization parameter to TRUE.
```

To configure automatic redirection of DML operations for the current session, use the following command:

```
ALTER SESSION ENABLE ADG_REDIRECT_DML;
```



### 2.2 测试

```
[ora19@whf307 ~]$ sqlplus  system/oracle

SQL*Plus: Release 19.0.0.0.0 - Production on Sat Mar 9 00:45:45 2019
Version 19.2.0.0.0

Copyright (c) 1982, 2018, Oracle.  All rights reserved.


Connected to:
Oracle Database 19c Enterprise Edition Release 19.0.0.0.0 - Production
Version 19.2.0.0.0

SQL> alter session set container=&pdb;
Enter value for pdb: pdbll
old   1: alter session set container=&pdb
new   1: alter session set container=pdborcl

Session altered.

SQL> select open_mode,database_role from v$database;

OPEN_MODE            DATABASE_ROLE
-------------------- ----------------
READ ONLY WITH APPLY PHYSICAL STANDBY

SQL> select * from t1;

        ID
----------
         1
         2
         2

SQL> insert into t1 values(3);

1 row created.

SQL> commit;

Commit complete.

SQL> select  * from t1;

        ID
----------
         1
         2
         2
         3

SQL> show parameter ADG_REDIRECT_DML

NAME                                 TYPE        VALUE
------------------------------------ ----------- ------------------------------
adg_redirect_dml                     boolean     TRUE
SQL> 
```



###  2.3 失败的原因

ORA-16397

```
SQL> select * from sa.t1 where id=1;

        ID NAME               C1
---------- ---------- ----------
         1 x                   1
         1 yy                  1
         1 x                   2

SQL> update sa.t1 set c1=1 where id=1;
update sa.t1 set c1=1 where id=1
          *
ERROR at line 1:
ORA-16397: statement redirection from Oracle Active Data Guard standby database to primary database failed
```

第一次测试的时候没有成功，看看error

```
[ora19@whf307 ~]$ oerr ora 16397
16397, 00000, "statement redirection from Oracle Active Data Guard standby database to primary database failed"
// *Cause:  The statement redirection failed because of one of the following reasons:
//          1. The primary database connect string was not established.
//          2. The primary database could not be reached.
//          3. The undo-mode or incarnation were not the same.
//          4. The current user and logged-in user were not the same.
//          5. Redirecting CREATE TABLE AS SELECT (CTAS) of the global temporary
//             table was not supported.
//          6. Redirecting PL/SQL execution having bind variable was not supported.
// *Action: Run the statement after fixing the condition that caused the failure.
```

这里我猜测是4用户不同的原因，dg上我是sys用户，当用system建表，dg上用system用户去dml的时候是ok了的，所以上面几个地方也需要注意一下。

还是不够努力啊，加油！



------------------

--Life is fantastic

--whf307

--20190308