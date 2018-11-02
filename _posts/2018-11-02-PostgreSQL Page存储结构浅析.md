## 一、Page

pg中的page和Oracle中的数据块是一个意思，都是数据库的块，操作系统（文件系统）块的整数倍个，默认是8K也就是两个操作系统块（4k的文件系统块大小）。这个大小在pg安装configure的时候通过--with-blocksize参数指定，单位是Kb。 

## 二、Page的内部结构

### 2.1 page结构

```c++
+----------------+---------------------------------+
| PageHeaderData | linp1 linp2 linp3 ...           |
+-----------+----+---------------------------------+
| ... linpN |                                      |
+-----------+--------------------------------------+
|           ^ pd_lower                             |
|                                                  |
|             v pd_upper                           |
+-------------+------------------------------------+
|             | tupleN ...                         |
+-------------+------------------+-----------------+
|       ... tuple3 tuple2 tuple1 | "special space" |
+--------------------------------+-----------------+
                                 ^ pd_special
                                 
*这部分代码在src/include/storage/bufpage.h
```

可以看到一个Page有 Pager header（页头），后面是linp（行指针），pd_lower和pd_upper分别是空闲空间的开始位置和结束位置；后面就是行数据（pg里面的行就是tuple）和special空间，可以看到整个page的结构比Oracle的数据块结构简单多了：）。

### 2.2PageHeaderData数据结构 （页头）

```c++
typedef struct PageHeaderData
{
	/* XXX LSN is member of *any* block, not only page-organized ones */
	PageXLogRecPtr pd_lsn;		/* LSN: next byte after last byte of xlog
								 * record for last change to this page */
	uint16		pd_checksum;	/* checksum */
	uint16		pd_flags;		/* flag bits, see below */
	LocationIndex pd_lower;		/* offset to start of free space */
	LocationIndex pd_upper;		/* offset to end of free space */
	LocationIndex pd_special;	/* offset to start of special space */
	uint16		pd_pagesize_version;
	TransactionId pd_prune_xid; /* oldest prunable XID, or zero if none */
	ItemIdData	pd_linp[FLEXIBLE_ARRAY_MEMBER]; /* line pointer array */
} PageHeaderData;

typedef PageHeaderData *PageHeader;
```

| Field               | Type           | Length  | Description                                                  |
| ------------------- | -------------- | ------- | ------------------------------------------------------------ |
| pd_lsn              | PageXLogRecPtr | 8 bytes | LSN: next byte after last byte of WAL record for last change to this page |
| pd_checksum         | uint16         | 2 bytes | Page checksum                                                |
| pd_flags            | uint16         | 2 bytes | Flag bits                                                    |
| pd_lower            | LocationIndex  | 2 bytes | Offset to start of free space                                |
| pd_upper            | LocationIndex  | 2 bytes | Offset to end of free space                                  |
| pd_special          | LocationIndex  | 2 bytes | Offset to start of special space                             |
| pd_pagesize_version | uint16         | 2 bytes | Page size and layout version number information              |
| pd_prune_xid        | TransactionId  | 4 bytes | Oldest unpruned XMAX on page, or zero if none                |

源码都有详细的注释，简单来说，pd_lsn是指最后修改过这个page的lsn（log sequence number），和wal（write ahead log，同oracle redo）中记录的lsn一致。数据落盘时redo必须先刷到wal，这个pd_lsn就记录了最后落盘的相关redo的lsn。

pd_checksum是校验和，在initdb的时候通过-k参数指定开启，默认是关闭的，initdb之后不能修改，它基于FNV-1a hash算法，做了相应的改动。这个校验和与Oracle的chkval一样用于数据块在读入和写出内存时的校验。比如我们在内存中修改了一个数据块，写入到磁盘的时候，在内存里面先计算好checksum，数据块写完后再计算一遍cheksum是否和之前在内存中的一致，确保整个写出过程没有出错，保护数据结构不被破坏。

pg_flags有以下的值：

```c++
/*
 * pd_flags contains the following flag bits.  Undefined bits are initialized
 * to zero and may be used in the future.
 *
 * PD_HAS_FREE_LINES is set if there are any LP_UNUSED line pointers before
 * pd_lower.  This should be considered a hint rather than the truth, since
 * changes to it are not WAL-logged.
 *
 * PD_PAGE_FULL is set if an UPDATE doesn't find enough free space in the
 * page for its new tuple version; this suggests that a prune is needed.
 * Again, this is just a hint.
 */
#define PD_HAS_FREE_LINES	0x0001	/* are there any unused line pointers? */
#define PD_PAGE_FULL		0x0002	/* not enough free space for new tuple? */
#define PD_ALL_VISIBLE		0x0004	/* all tuples on page are visible to
									 * everyone */

#define PD_VALID_FLAG_BITS	0x0007	/* OR of all valid pd_flags bits */
```

pd_lower和pd_upper是分表示空闲空间起始位置和结束位置；pd_special在索引page才会有效；pd_pagesize_version是page大小和page version的存储位，在不同数据库版本中，page version不一样：

| 数据库版本 | pd_pagesize_version |
| :--------- | :------------------ |
| <7.3       | 0                   |
| 7.3 & 7.4  | 1                   |
| 8.0        | 2                   |
| 8.1        | 3                   |
| >8.3       | 4                   |

prune_xid表示这个page上最早删除或者修改tuple的事务id，用于vacuum操作

### 2.3 linp结构（行指针）

```c++
/*
 * An item pointer (also called line pointer) on a buffer page
 *
 * In some cases an item pointer is "in use" but does not have any associated
 * storage on the page.  By convention, lp_len == 0 in every item pointer
 * that does not have storage, independently of its lp_flags state.
 */
typedef struct ItemIdData
{
	unsigned	lp_off:15,		/* offset to tuple (from start of page) */
				lp_flags:2,		/* state of item pointer, see below */
				lp_len:15;		/* byte length of tuple */
} ItemIdData;

typedef ItemIdData *ItemId;
/*
 * lp_flags has these possible states.  An UNUSED line pointer is available
 * for immediate re-use, the other states are not.
 */
#define LP_UNUSED		0		/* unused (should always have lp_len=0) */
#define LP_NORMAL		1		/* used (should always have lp_len>0) */
#define LP_REDIRECT		2		/* HOT redirect (should have lp_len=0) */
#define LP_DEAD			3		/* dead, may or may not have storage */
```

lp_off是tuple的开始的偏移量；lp_flags是标志位（0表示没有使用，1表示有数据了，2表示HOT重定向了，3表示这个tuple没用了）；lp_len是tuple的长度

| Field    | Length  | Description            |
| -------- | ------- | ---------------------- |
| lp_off   | 15 bits | offset to tuple        |
| lp_flags | 2 bits  | State of iteam pointer |
| lp_len   | 15 bits | Byte  length of tuple  |

### 2.4 tuple header结构（行头）

```c++
typedef struct HeapTupleFields
{
	TransactionId t_xmin;		/* inserting xact ID */
	TransactionId t_xmax;		/* deleting or locking xact ID */

	union
	{
		CommandId	t_cid;		/* inserting or deleting command ID, or both */
		TransactionId t_xvac;	/* old-style VACUUM FULL xact ID */
	}			t_field3;
} HeapTupleFields;

typedef struct DatumTupleFields
{
	int32		datum_len_;		/* varlena header (do not touch directly!) */
	int32		datum_typmod;	/* -1, or identifier of a record type */
	Oid			datum_typeid;	/* composite type OID, or RECORDOID */
	/*
	 * Note: field ordering is chosen with thought that Oid might someday
	 * widen to 64 bits.
	 */
} DatumTupleFields;

struct HeapTupleHeaderData
{
	union
	{
		HeapTupleFields t_heap;
		DatumTupleFields t_datum;
	}			t_choice;

	ItemPointerData t_ctid;		/* current TID of this or newer tuple (or a
								 * speculative insertion token) */
	/* Fields below here must match MinimalTupleData! */
	uint16		t_infomask2;	/* number of attributes + various flags */
	uint16		t_infomask;		/* various flag bits, see below */
	uint8		t_hoff;			/* sizeof header incl. bitmap, padding */
	/* ^ - 23 bytes - ^ */
	bits8		t_bits[FLEXIBLE_ARRAY_MEMBER];	/* bitmap of NULLs */
	/* MORE DATA FOLLOWS AT END OF STRUCT */
};

*这部分代码在src/include/access/htup_details.h
```

| Field       | Type            | Length  | Description                                           |
| ----------- | --------------- | ------- | ----------------------------------------------------- |
| t_xmin      | TransactionId   | 4 bytes | insert XID stamp                                      |
| t_xmax      | TransactionId   | 4 bytes | delete XID stamp                                      |
| t_cid       | CommandId       | 4 bytes | insert and/or delete CID stamp (overlays with t_xvac) |
| t_xvac      | TransactionId   | 4 bytes | XID for VACUUM operation moving a row version         |
| t_ctid      | ItemPointerData | 6 bytes | current TID of this or newer row version              |
| t_infomask2 | uint16          | 2 bytes | number of attributes, plus various flag bits          |
| t_infomask  | uint16          | 2 bytes | various flag bits                                     |
| t_hoff      | uint8           | 1 byte  | offset to user data                                   |

union是共享结构体，起作用的变量是最后一次赋值的成员。来看看tuple header的结构。

在HeapTupleFields中，t_xmin是插入这行tuple的事务id；t_xmin是插入或者锁住tuple的事务id；它的union结构中的t_cid是删除或者插入这个tuple的id，是块号和tuple号的结合；t_xvac是以前格式下vacuum full用到的事务id。

在DatumTupleFields中，datum_len_ 指tuple的长度；datum_typmod是记录的type；datum_typeid是记录的id。

页头HeapTupleHeaderData包含了union结构体中的两个变量HeapTupleFields和DatumTupleFields。

**t_infomask2 **表示属性和标志位

**t_infomask **是flag标志位，具体值如下：

```c++
/*
 * information stored in t_infomask:
 */
#define HEAP_HASNULL			0x0001	/* has null attribute(s) */
#define HEAP_HASVARWIDTH		0x0002	/* has variable-width attribute(s) */
#define HEAP_HASEXTERNAL		0x0004	/* has external stored attribute(s) */
#define HEAP_HASOID				0x0008	/* has an object-id field */
#define HEAP_XMAX_KEYSHR_LOCK	0x0010	/* xmax is a key-shared locker */
#define HEAP_COMBOCID			0x0020	/* t_cid is a combo cid */
#define HEAP_XMAX_EXCL_LOCK		0x0040	/* xmax is exclusive locker */
#define HEAP_XMAX_LOCK_ONLY		0x0080	/* xmax, if valid, is only a locker */

/* xmax is a shared locker */
#define HEAP_XMAX_SHR_LOCK	(HEAP_XMAX_EXCL_LOCK | HEAP_XMAX_KEYSHR_LOCK)

#define HEAP_LOCK_MASK	(HEAP_XMAX_SHR_LOCK | HEAP_XMAX_EXCL_LOCK | \
						 HEAP_XMAX_KEYSHR_LOCK)
#define HEAP_XMIN_COMMITTED		0x0100	/* t_xmin committed */
#define HEAP_XMIN_INVALID		0x0200	/* t_xmin invalid/aborted */
#define HEAP_XMIN_FROZEN		(HEAP_XMIN_COMMITTED|HEAP_XMIN_INVALID)
#define HEAP_XMAX_COMMITTED		0x0400	/* t_xmax committed */
#define HEAP_XMAX_INVALID		0x0800	/* t_xmax invalid/aborted */
#define HEAP_XMAX_IS_MULTI		0x1000	/* t_xmax is a MultiXactId */
#define HEAP_UPDATED			0x2000	/* this is UPDATEd version of row */
#define HEAP_MOVED_OFF			0x4000	/* moved to another place by pre-9.0
										 * VACUUM FULL; kept for binary
										 * upgrade support */
#define HEAP_MOVED_IN			0x8000	/* moved from another place by pre-9.0
										 * VACUUM FULL; kept for binary
										 * upgrade support */
#define HEAP_MOVED (HEAP_MOVED_OFF | HEAP_MOVED_IN)

#define HEAP_XACT_MASK			0xFFF0	/* visibility-related bits */
```

t_hoff表示tuple header的长度；t_bits表示null值的数量。

## 三、实验

### 3.1 安装pageinspect

它在源码的crontrib下面

```sql
postgres@307-> cd postgresql-10.4/contrib/pageinspect
```

make && make install

```
postgres@307-> make
postgres@307-> make install
```

create extension就好了

```sql
postgres@307-> psql
psql (10.4)
Type "help" for help.

postgres=# CREATE EXTENSION pageinspect;
CREATE EXTENSION

postgres=# \x
Expanded display is on.
postgres=# \dx
List of installed extensions
-[ RECORD 1 ]------------------------------------------------------
Name        | pageinspect
Version     | 1.6
Schema      | public
Description | inspect the contents of database pages at a low level
-[ RECORD 2 ]------------------------------------------------------
Name        | plpgsql
Version     | 1.0
Schema      | pg_catalog
Description | PL/pgSQL procedural language

postgres=# 
```

### 3.2 创建建测试表t1，插入数据

```sql
postgres=# create table t1(id int,name varchar(10));
CREATE TABLE

postgres=# insert into t1 select generate_series(1,1000),generate_series(1,1000)||'_x';
INSERT 0 1000
postgres=# 

postgres=# select * from t1 limit 10;
 id | name 
----+------
  1 | 1_x
  2 | 2_x
  3 | 3_x
  4 | 4_x
  5 | 5_x
  6 | 6_x
  7 | 7_x
  8 | 8_x
  9 | 9_x
 10 | 10_x
(10 rows)
postgres=# 

postgres=# select count(*) from t1;
 count 
-------
  1000
(1 row)

postgres=# select max(ctid) from t1;
  max   
--------
 (5,73)
(1 row)

postgres=# \d+
                  List of relations
 Schema | Name | Type  | Owner | Size  | Description 
--------+------+-------+-------+-------+-------------
 public | t1   | table | pg    | 72 kB | 
(1 row)

postgres=# 
```

这里可以看到1000行数据用了6个数据块来存储（这里数据块从0开始计数）

### 3.3 Pageinspect查看page

这里我们通过两个函数来查看

page_header        可以看到页头的数据

heap_page_items 可以看到具体tuple的数据

#### 3.3.1 page_header

```sql
postgres=# \x
Expanded display is on.
postgres=# select * from page_header(get_raw_page('t1',0));
-[ RECORD 1 ]--------
lsn       | 0/1671188
checksum  | 0
flags     | 0
lower     | 772
upper     | 784
special   | 8192
pagesize  | 8192
version   | 4
prune_xid | 0

postgres=# 
```

可以看到第0个page的pd_lsn为0/1671188，checksum和flags都是0，这里没有开启checksum；tuple开始偏移是772（pd_lower），结束偏移是784（pd_upper），这个page是个表，所以它没有special，我们看到的sepcial就是8192了；pagesize是8192，version是4，没有需要清理的tuple，所以存储需要清理的tuple的最早事务的id就是0（prune_xid）。

#### 3.3.2 heap_page_items

```sql
postgres=# select * from heap_page_items(get_raw_page('t1',0)) limit 1;
-[ RECORD 1 ]-------------------
lp          | 1
lp_off      | 8160
lp_flags    | 1
lp_len      | 32
t_xmin      | 557
t_xmax      | 0
t_field3    | 0
t_ctid      | (0,1)
t_infomask2 | 2
t_infomask  | 2306
t_hoff      | 24
t_bits      | 
t_oid       | 
t_data      | \x0100000009315f78

postgres=# 
```

我们来看一行记录，可以看到它是第1行记录（lp=1），tuple的开始偏移量8160（lp_off）,tuple的长度是32bytes（lp_len为32，这个tuple是第一个插入的tuple，所以lp_off+lp_len=8160+32=8192），这行记录的插入事务id是557（t_min），和tuple的删除事务id是0（t_max），这里数据没有被删除，所以都是0。我们还可以看到t_ctid是（0，1），这里表示这个tuple是这个事务里第一条命令插入的，t_ctid就是事务内部的命令序号；t_infomask2是2，t_infomask为2306；tuple头部结构（行头）的长度是24（t_hoff），t_data就是16进制存储的真正的数据了。

```sql
postgres=# \d t1
                        Table "public.t1"
 Column |         Type          | Collation | Nullable | Default 
--------+-----------------------+-----------+----------+---------
 id     | integer               |           |          | 
 name   | character varying(10) |           |          | 

postgres=# 
```

### 3.4 删除一行数据观察prune_xid

```sql
postgres=# select * from page_header(get_raw_page('t1',0));
-[ RECORD 1 ]--------
lsn       | 0/1671188
checksum  | 0
flags     | 0
lower     | 772
upper     | 784
special   | 8192
pagesize  | 8192
version   | 4
prune_xid | 0

postgres=# delete from t1 where id=1;
DELETE 1
postgres=# select * from page_header(get_raw_page('t1',0));
-[ RECORD 1 ]--------
lsn       | 0/16852A0
checksum  | 0
flags     | 0
lower     | 772
upper     | 784
special   | 8192
pagesize  | 8192
version   | 4
prune_xid | 559

postgres=# 
```

我们删除一行tuple可以看到prune_xid有了值，为559，这个559就是删除这个tuple的事务id（当前最早的删除或更改了tuple的事务id）

```sql
postgres=# select * from heap_page_items(get_raw_page('t1',0)) limit 1;
-[ RECORD 1 ]-------------------
lp          | 1
lp_off      | 8160
lp_flags    | 1
lp_len      | 32
t_xmin      | 557
t_xmax      | 559
t_field3    | 0
t_ctid      | (0,1)
t_infomask2 | 8194
t_infomask  | 258
t_hoff      | 24
t_bits      | 
t_oid       | 
t_data      | \x0100000009315f78

postgres=# 
```

同样，我们可以看到lp为1的这个tuple的t_xmax为559，这里就是删除这行tuple的事务id。



PostgreSQL的物理存储结构相比Oracle来说简单很多了，而且开放源代码，更方便学习和研究，但是要研究透彻毕竟还是不容易的一件事情。
