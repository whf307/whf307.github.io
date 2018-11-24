---

category: pg

---

# BBED for PostgreSQL

## 一、关于bbedp

用python模仿bbed写了一个bbed for pg的脚本，简单的查看和修改字节都可以做到，你可以在[这里](https://whf307.github.io/download/)下载到最新的版本，如果你有任何问题可以联系我：whf307@gmail.com。如果你不清楚这个脚本的功能，请不要轻易在生产环境使用它，这很危险。不一定有用，但比较好玩。

使用环境：

1、linux

2、python 2.7



## 二、如何开始

### 2.1 找到table对应page的绝对路径

你可以通过$PGDATA环境变量找到数据文件的目录。

```
postgres@whf307-> echo $PGDATA
/oracle/soft/pg_data/
postgres@whf307-> 
```

如果没有配置环境变量，当然可以通过进程找到

```
postgres@whf307-> ps -ef | grep postgres
postgres 32739     1  0 Nov13 ?        00:00:07 /oracle/soft/pgsql9.6/bin/postgres
postgres 32747 32739  0 Nov13 ?        00:00:02 postgres: checkpointer process   
postgres 32748 32739  0 Nov13 ?        00:00:06 postgres: writer process   
postgres 32749 32739  0 Nov13 ?        00:00:12 postgres: wal writer process   
postgres 32750 32739  0 Nov13 ?        00:00:05 postgres: autovacuum launcher process  
postgres 32751 32739  0 Nov13 ?        00:00:00 postgres: archiver process   last was 000000010000000600000067
postgres 32752 32739  0 Nov13 ?        00:00:12 postgres: stats collector process  
postgres@whf307-> lsof -p 32739| grep cwd
postgres 32739 postgres  cwd    DIR              253,7      4096 147604224 /oracle/soft/pg_data
postgres@whf307-> 
```

再比如t1表的page

```
postgres=# select pg_relation_filepath('t1');
 pg_relation_filepath 
----------------------
 base/13323/24706
(1 row)

postgres=# 
```

然后编辑bbedp脚本下的file文件就可以开始了，目前仅支持单个文件

```
vi file
/oracle/soft/pg_data/base/13323/24706
```

### 2.2 运行bbedp

这里你需要给x权限运行就可以了，为了效果就不要密码了。

```
postgres@cs-db-> ./bbedp
Password: 

BBEDP: Release 0.1.0.0.0 - Limited Production on Sat Nov 24 16:50:30 2018

Copyright (c) 2018, 2018, whf307 and/or its affiliates.  All rights reserved.

************* !!! For PostgreSQL Internal Test only !!! *************** 

BBEDP> help
set block [block_offset]
set count [bytes_to_display]
set offset  [offset_to_dump]
map :map the struct
d   :dump the offset
p   :print offset
p PageHeaderData :to print the page header struct
p Linps :to print the linps
p linp[n] :to print the linp[n]
p Tuples: print all tupels
p tuples [n]:print the tuple n
p Pd_special : print pd_special
m /x aaaa offset bbbb :to modify the offset
exit :exit the program
BBEDP> 
```

如果你了解bbed，那么help看一眼帮助就很容易上手bbedp了，你不了解bbed也没关系，脚本很简单，主要功能有查看page结构，dump字节，修改字节。



## 三、查看page

### 3.1 map查看page结构

```
BBEDP> map
 File: /oracle/soft/pg_data/base/13323/16428
 Block: 0                                offset: 0
 -------------------------------------------------------------------
 struct  PageHeaderData , 24 bytes          @0

 struct  Linps , 44 bytes                   @24

 struct  Tuples , 392 bytes                 @68     

 struct  Pd_special , 0 bytes               @8191

 There are 11 tuples in the block
BBEDP> 

默认从block 0开始，你可以set block到指定的block再开始
```

### 3.2 p查看具体结构

```
BBEDP> p PageHeaderData
struct PageHeaderData, 24 bytes                @0
 pd_lsn                                        @0           0x0600000008e2a262
 pd_checksum                                   @8           0x0000
 pd_flags                                      @10          0x0000
 pd_lower                                      @12          0x4400
 pd_upper                                      @14          0x781e
 pd_special                                    @16          0x0020
 pd_pagesize_version                           @18          0x0420
 pd_prune_xid                                  @20          0x33070000
 
BBEDP> p Linps
linp 1    @24  0x003c9fe0
-------------------------
lp_off   : 8160
lp_flags : 1
lp_len   : 30

linp 2    @28  0x3c9fc000
-------------------------
lp_off   : 8128
lp_flags : 1
lp_len   : 30

linp 3    @32  0x9fa0003c
-------------------------
lp_off   : 8096
lp_flags : 1
lp_len   : 28
...

BBEDP> p Tuples
tuple 1
-----------------------------------------------------
lp_off        8160          @24            0x003c9fe0
lp_flags      1             @24            0x003c9fe0
lp_len        30            @24            0x003c9fe0
t_xmin        1791          @8160          0xff060000
t_xmax        1843          @8164          0x33070000
t_field3      0             @8168          0x00000000
t_ctid        (0,6)         @8172          0x000000000600
t_infomask2   16387         @8178          0x0340
t_infomask    1795          @8180          0x0307
t_hoff        24            @8182          0x18
bits8         0b11          @8183          0x03
tupledata                   @8184          0x010000000578

tuple 2
-----------------------------------------------------
lp_off        8128          @28            0x3c9fc000
lp_flags      1             @28            0x3c9fc000
lp_len        30            @28            0x3c9fc000
t_xmin        1791          @8128          0xff060000
t_xmax        1843          @8132          0x33070000
t_field3      0             @8136          0x00000000
t_ctid        (0,7)         @8140          0x000000000700
t_infomask2   16387         @8146          0x0340
t_infomask    1795          @8148          0x0307
t_hoff        24            @8150          0x18
bits8         0b11          @8151          0x03
tupledata                   @8152          0x040000000578
...
```

当然，也可直接p

```
BBEDP> p PageHeaderData
struct PageHeaderData, 24 bytes                @0
 pd_lsn                                        @0           0x0600000008e2a262
 pd_checksum                                   @8           0x0000
 pd_flags                                      @10          0x0000
 pd_lower                                      @12          0x4400
 pd_upper                                      @14          0x781e
 pd_special                                    @16          0x0020
 pd_pagesize_version                           @18          0x0420
 pd_prune_xid                                  @20          0x33070000
BBEDP> 
BBEDP> p 20
PageHeaderData.pd_checksum
------------------------------------------------
pd_prune_xid            @20                 0x33070000
BBEDP> p 44
IteamIdDatas
------------------------------------------------
linp6                   @44                0x00440078
BBEDP> p 8188
Tuples
------------------------------------------------
tupledata              @8188                0x0578
BBEDP> 
```

p 指定行指针和tuple

```
BBEDP> p linp 1
linp1    @24  0xe09f3c
-------------------------
lp_off   : 8160
lp_flags : 1
lp_len   : 30
BBEDP> p tuple 1
tuple 1
-----------------------------------------------------
lp_off        8160          @24            0x003c9fe0
lp_flags      1             @24            0x003c9fe0
lp_len        30            @24            0x003c9fe0
t_xmin        1791          @8160          0xff060000
t_xmax        1843          @8164          0x33070000
t_field3      0             @8168          0x00000000
t_ctid        (0,6)         @8172          0x000000000600
t_infomask2   16387         @8178          0x0340
t_infomask    1795          @8180          0x0307
t_hoff        24            @8182          0x18
bits8         0b11          @8183          0x03
tupledata                   @8184          0x010000000578

BBEDP> 
```

### 3.3 d打印出字节

```
BBEDP> p PageHeaderData
struct PageHeaderData, 24 bytes                @0
 pd_lsn                                        @0           0x0600000008e2a262
 pd_checksum                                   @8           0x0000
 pd_flags                                      @10          0x0000
 pd_lower                                      @12          0x4400
 pd_upper                                      @14          0x781e
 pd_special                                    @16          0x0020
 pd_pagesize_version                           @18          0x0420
 pd_prune_xid                                  @20          0x33070000
BBEDP> d
 File: /oracle/soft/pg_data/base/13323/16428
 Block: 0                                Offsets: 0 to 511
 ----------------------------------------------------------------------
06000000 08e2a262 00000000 4400781e 00200420 33070000 e09f3c00 c09f3c00
a09f3800 809f3c00 609f3c00 389f4800 109f4800 f09e4000 c89e4800 a09e4800
789e4800 00000000 00000000 00000000 00000000 00000000 00000000 00000000
00000000 00000000 00000000 00000000 00000000 00000000 00000000 00000000
00000000 00000000 00000000 00000000 00000000 00000000 00000000 00000000
00000000 00000000 00000000 00000000 00000000 00000000 00000000 00000000
00000000 00000000 00000000 00000000 00000000 00000000 00000000 00000000
00000000 00000000 00000000 00000000 00000000 00000000 00000000 00000000
00000000 00000000 00000000 00000000 00000000 00000000 00000000 00000000
00000000 00000000 00000000 00000000 00000000 00000000 00000000 00000000
00000000 00000000 00000000 00000000 00000000 00000000 00000000 00000000
00000000 00000000 00000000 00000000 00000000 00000000 00000000 00000000
00000000 00000000 00000000 00000000 00000000 00000000 00000000 00000000
00000000 00000000 00000000 00000000 00000000 00000000 00000000 00000000
00000000 00000000 00000000 00000000 00000000 00000000 00000000 00000000
00000000 00000000 00000000 00000000 00000000 00000000 00000000 00000000

<32 bytes per line>
BBEDP> 


BBEDP> set offset 18
        OFFSET           18
BBEDP> set count 32
        COUNT           32
BBEDP> d
 File: /oracle/soft/pg_data/base/13323/16428
 Block: 0                                Offsets: 18 to 49
 ----------------------------------------------------------------------
04203307 0000e09f 3c00c09f 3c00a09f 3800809f 3c00609f 3c00389f 4800109f

<32 bytes per line>
BBEDP> 
```



## 四、修改

### 4.1 表T5有一条删除的tuple

```
postgres=# select * from t5;
 id |    name    
----+------------
  1 | x         
  2 | xx        
  3 | xxx       
(3 rows)

postgres=# delete from t5 where id=3;
DELETE 1
postgres=# checkpoint;
CHECKPOINT
postgres=# select * from t5;
 id |    name    
----+------------
  1 | x         
  2 | xx        
(2 rows)

postgres=# 

postgres=# checkpoint;
CHECKPOINT
postgres=# 

postgres=# select pg_relation_filepath('t5');
 pg_relation_filepath 
----------------------
 base/13323/24714
(1 row)

postgres=# 

postgres@whf307-> vi file
/oracle/soft/pg_data/base/13323/24714
```

### 4.2 查看tuple

```
postgres@whf307-> ./bbedp
Password: 

BBEDP: Release 0.1.0.0.0 - Limited Production on Sat Nov 24 17:15:45 2018

Copyright (c) 2018, 2018, whf307 and/or its affiliates.  All rights reserved.

************* !!! For PostgreSQL Internal Test only !!! *************** 

BBEDP> map
 File: /oracle/soft/pg_data/base/13323/24714
 Block: 0                                offset: 0
 -------------------------------------------------------------------
 struct  PageHeaderData , 24 bytes          @0

 struct  Linps , 12 bytes                   @24

 struct  Tuples , 120 bytes                 @36     

 struct  Pd_special , 0 bytes               @8191

 There are 3 tuples in the block
BBEDP> 

BBEDP> p Tuples
tuple 1
-----------------------------------------------------
lp_off        8152          @24            0x004e9fd8
lp_flags      1             @24            0x004e9fd8
lp_len        39            @24            0x004e9fd8
t_xmin        1793          @8152          0x01070000
t_xmax        0             @8156          0x00000000
t_field3      0             @8160          0x00000000
t_ctid        (0,1)         @8164          0x000000000100
t_infomask2   2             @8170          0x0200
t_infomask    2818          @8172          0x020b
t_hoff        24            @8174          0x18
bits8         0b0           @8175          0x00
tupledata                   @8176          0x010000001778202020202020202020

tuple 2
-----------------------------------------------------
lp_off        8112          @28            0x4e9fb000
lp_flags      1             @28            0x4e9fb000
lp_len        39            @28            0x4e9fb000
t_xmin        1884          @8112          0x5c070000
t_xmax        0             @8116          0x00000000
t_field3      0             @8120          0x00000000
t_ctid        (0,2)         @8124          0x000000000200
t_infomask2   2             @8130          0x0200
t_infomask    2306          @8132          0x0209
t_hoff        24            @8134          0x18
bits8         0b0           @8135          0x00
tupledata                   @8136          0x020000001778782020202020202020

tuple 3
-----------------------------------------------------
lp_off        8072          @32            0x9f88004e
lp_flags      1             @32            0x9f88004e
lp_len        39            @32            0x9f88004e
t_xmin        1884          @8072          0x5c070000
t_xmax        1885          @8076          0x5d070000
t_field3      0             @8080          0x00000000
t_ctid        (0,3)         @8084          0x000000000300
t_infomask2   8194          @8090          0x0220
t_infomask    1282          @8092          0x0205
t_hoff        24            @8094          0x18
bits8         0b0           @8095          0x00
tupledata                   @8096          0x030000001778787820202020202020

BBEDP> 
```

### 4.3 修改

可以看到tuple3这里t_xmax不为空，可能被删了，我们修改找回来。

```
BBEDP> p tuple 3
tuple 3
-----------------------------------------------------
lp_off        8072          @32            0x9f88004e
lp_flags      1             @32            0x9f88004e
lp_len        39            @32            0x9f88004e
t_xmin        1884          @8072          0x5c070000
t_xmax        1885          @8076          0x5d070000
t_field3      0             @8080          0x00000000
t_ctid        (0,3)         @8084          0x000000000300
t_infomask2   8194          @8090          0x0220
t_infomask    1282          @8092          0x0205
t_hoff        24            @8094          0x18
bits8         0b0           @8095          0x00
tupledata                   @8096          0x030000001778787820202020202020

BBEDP> m /x 0000 offset 8076
BBEDP> m /x 0200 offset 8090
BBEDP> m /x 0209 offset 8092
BBEDP> p tuple 3
tuple 3
-----------------------------------------------------
lp_off        8072          @32            0x9f88004e
lp_flags      1             @32            0x9f88004e
lp_len        39            @32            0x9f88004e
t_xmin        1884          @8072          0x5c070000
t_xmax        0             @8076          0x00000000
t_field3      0             @8080          0x00000000
t_ctid        (0,3)         @8084          0x000000000300
t_infomask2   2             @8090          0x0200
t_infomask    2306          @8092          0x0209
t_hoff        24            @8094          0x18
bits8         0b0           @8095          0x00
tupledata                   @8096          0x030000001778787820202020202020

BBEDP> 
```

可以看到已经改过来了，重启实例刷新shared  buffer

```
postgres@whf307-> pg_ctl stop -m fast
waiting for server to shut down.... done
server stopped
postgres@whf307-> pg_ctl start -l ./server.log 
server starting

postgres@whf307-> psql
psql (9.6.9)
Type "help" for help.

postgres=# select * from t5;
 id |    name    
----+------------
  1 | x         
  2 | xx        
  3 | xxx       
(3 rows)
```

最后，你可以exit来退出程序



## 五、最后

不一定有用，但是好玩！

: )

