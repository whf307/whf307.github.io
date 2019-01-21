---
category: pg
---

根据ctid来计算具体的page，因为超过1G的page会被切割。

### ll这个表有4G多

```sql
li=# \d+
                       List of relations
 Schema |  Name   |   Type   | Owner |    Size    | Description 
--------+---------+----------+-------+------------+-------------
 public | ll      | table    | pg    | 4727 MB    |  
 public | t1      | table    | pg    | 8192 bytes | 
 public | t2      | table    | pg    | 8192 bytes | 
 public | t3      | table    | pg    | 8192 bytes | 
(4 rows)
```

### 找一下最大的ctid

```sql
li=# select max(ctid) from ll;
     max     
-------------
 (604933,19)
(1 row)

li=# 
```

### 建一个函数来计算

```sql
create or replace function get_file_block(tab text,c1 int) returns varchar
as $$
select 'the file path is :'||pg_relation_filepath($1) 
||E'      \n'||'frag of pages is :'||$2*8/(1024*1024)
||E'      \n'||'block is :'||($2*8192::bigint)%(1024*1024*1024)/8192;
$$
language sql;

li=# select get_file_block('ll',604933);
              get_file_block              
------------------------------------------
 the file path is :base/16384/21150      +
 frag of pages is :4                     +
 block is :80645
(1 row)
```

### 简单说明下：

1、输入表名和blockid，表属于public的话owner可以省略

2、比如这里是 604933这个block，一个block是8K来计算。1G=1024*1024K，那么(604933\*8)/(1024\*1024)的结果就是第几个1G的文件了

3、取余的话就是这个文件中所在的偏移量了，单位是k，我们再除以8192就是块的个数了，所以就是(604933\*8192::bigint)%(1024\*1024\*1024)/8192。这里就是80645这块了

4、page物理位置用pg_relation_filepath查看得到

### 那么真正的物理文件就是

```sql
li=# show data_directory;
  data_directory   
-------------------
 /oracle/soft/data
(1 row)

li=# 


/oracle/soft/data/base/16384/21150.4
```

### 用bbedp查看验证

```shell
[root@whf307 soft]# ./bbedp 
Password: 

BBEDP: Release 0.1.0.0.0 - Limited Production on Fra Jan 18 17:57:58 2019

Copyright (c) 2018, 2018, whf307 and/or its affiliates.  All rights reserved.

************* !!! For PostgreSQL Internal Test only !!! *************** 

BBEDP> set block 80645
   BLOCK         80645
BBEDP> set block 80646
Out range of blocks!!!
BBEDP> 
BBEDP> set block 80645
   BLOCK         80645
BBEDP> p tuple 19
tuple 19
-----------------------------------------------------
lp_off        7424          @96            0x9da00040
lp_flags      1             @96            0x9da00040
lp_len        38            @96            0x9da00040
t_xmin        1845          @7424          0x35070000
t_xmax        0             @7428          0x00000000
t_field3      0             @7432          0x00000000
t_ctid        (604933,19)   @7436          0x0900053b1300
t_infomask2   2             @7442          0x0200
t_infomask    2306          @7444          0x0209
t_hoff        24            @7446          0x18
bits8         0b0           @7447          0x00
tupledata                   @7448          0x0b00000015277c7c73716c7c7c27

BBEDP> p tuple 20
No such tuple!!!
BBEDP> 
```

### pageinspect验证

```

li=# select * from heap_page_items(get_raw_page('ll',604933));
 lp | lp_off | lp_flags | lp_len | t_xmin | t_xmax | t_field3 |   t_ctid    | t_infomask2 | t_infomask | t_hoff | t_bits | t_oid |                                                                     
       t_data                                                                            
----+--------+----------+--------+--------+--------+----------+-------------+-------------+------------+--------+--------+-------+---------------------------------------------------------------------
  1 |   8160 |        1 |     32 |   1845 |      0 |        0 | (604933,1)  |           2 |       2306 |     24 |        |       | \x03000000097c787c
  2 |   8120 |        1 |     34 |   1845 |      0 |        0 | (604933,2)  |           2 |       2306 |     24 |        |       | \x030000000d277c787c27
  3 |   8080 |        1 |     36 |   1845 |      0 |        0 | (604933,3)  |           2 |       2306 |     24 |        |       | \x0300000011277c2778277c27
  4 |   8040 |        1 |     38 |   1845 |      0 |        0 | (604933,4)  |           2 |       2306 |     24 |        |       | \x030000001527277c277827277c27
  5 |   8000 |        1 |     38 |   1845 |      0 |        0 | (604933,5)  |           2 |       2306 |     24 |        |       | \x0a00000015277c7c73716c7c7c27
  6 |   7960 |        1 |     38 |   1845 |      0 |        0 | (604933,6)  |           2 |       2306 |     24 |        |       | \x0b00000015277c7c73716c7c7c27
  7 |   7928 |        1 |     30 |   1845 |      0 |        0 | (604933,7)  |           2 |       2306 |     24 |        |       | \x010000000578
  8 |   7896 |        1 |     31 |   1845 |      0 |        0 | (604933,8)  |           2 |       2306 |     24 |        |       | \x02000000077878
  9 |   7856 |        1 |     38 |   1845 |      0 |        0 | (604933,9)  |           2 |       2306 |     24 |        |       | \x0100000015277c7c73716c7c7c27
 10 |   7752 |        1 |    101 |   1845 |      0 |        0 | (604933,10) |           2 |       2306 |     24 |        |       | \x010000009375706461746520415454525f56414c55452073657420415454525f56
 11 |   7720 |        1 |     32 |   1845 |      0 |        0 | (604933,11) |           2 |       2306 |     24 |        |       | \x0300000009227822
 12 |   7688 |        1 |     32 |   1845 |      0 |        0 | (604933,12) |           2 |       2306 |     24 |        |       | \x0300000009277827
 13 |   7656 |        1 |     31 |   1845 |      0 |        0 | (604933,13) |           2 |       2306 |     24 |        |       | \x0300000007787c
 14 |   7624 |        1 |     32 |   1845 |      0 |        0 | (604933,14) |           2 |       2306 |     24 |        |       | \x03000000097c787c
 15 |   7584 |        1 |     34 |   1845 |      0 |        0 | (604933,15) |           2 |       2306 |     24 |        |       | \x030000000d277c787c27
 16 |   7544 |        1 |     36 |   1845 |      0 |        0 | (604933,16) |           2 |       2306 |     24 |        |       | \x0300000011277c2778277c27
 17 |   7504 |        1 |     38 |   1845 |      0 |        0 | (604933,17) |           2 |       2306 |     24 |        |       | \x030000001527277c277827277c27
 18 |   7464 |        1 |     38 |   1845 |      0 |        0 | (604933,18) |           2 |       2306 |     24 |        |       | \x0a00000015277c7c73716c7c7c27
 19 |   7424 |        1 |     38 |   1845 |      0 |        0 | (604933,19) |           2 |       2306 |     24 |        |       | \x0b00000015277c7c73716c7c7c27
(19 rows)

li=# 
```

### 参考资料：

[PostgreSQL数据页面损坏修复]: (https://mp.weixin.qq.com/s/LFPta3nGD12MRFVyuYEvHA)

