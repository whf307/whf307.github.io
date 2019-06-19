---
category: pg
---

pg的数据库目录有点多，仅仅知道是做什么的远远不够，今天开始学习他的目录结构。

一、pg的目录结构

我这里用了目前最新的12.1



`[pg12@enmodb2 pg_twophase]$ ls -rtl ..`
`total 136`
`drwx------ 2 pg12 pg12  4096 Jun 14 11:08 pg_snapshots`
`drwx------ 2 pg12 pg12  4096 Jun 14 11:08 pg_serial`
`drwx------ 2 pg12 pg12  4096 Jun 14 11:08 pg_replslot`
`drwx------ 4 pg12 pg12  4096 Jun 14 11:08 pg_multixact`
`drwx------ 2 pg12 pg12  4096 Jun 14 11:08 pg_dynshmem`
`drwx------ 2 pg12 pg12  4096 Jun 14 11:08 pg_commit_ts`
`-rw------- 1 pg12 pg12     3 Jun 14 11:08 PG_VERSION`
`-rw------- 1 pg12 pg12  1636 Jun 14 11:08 pg_ident.conf`
`-rw------- 1 pg12 pg12  4513 Jun 14 11:08 pg_hba.conf`
`drwx------ 2 pg12 pg12  4096 Jun 14 11:08 pg_xact`
`drwx------ 3 pg12 pg12  4096 Jun 14 11:08 pg_wal`
`drwx------ 2 pg12 pg12  4096 Jun 14 11:08 pg_subtrans`
`drwx------ 5 pg12 pg12  4096 Jun 14 11:08 base`
`-rw------- 1 pg12 pg12 26671 Jun 14 11:09 postgresql.conf`
`drwx------ 2 pg12 pg12  4096 Jun 18 11:06 pg_tblspc`
`-rw------- 1 pg12 pg12   121 Jun 20 00:25 postgresql.auto.conf`
`-rw------- 1 pg12 pg12    26 Jun 20 00:26 postmaster.opts`
`drwx------ 2 pg12 pg12  4096 Jun 20 00:26 pg_notify`
`-rw------- 1 pg12 pg12  8373 Jun 20 00:26 alert.logg`
`-rw------- 1 pg12 pg12    73 Jun 20 00:26 postmaster.pid`
`drwx------ 2 pg12 pg12  4096 Jun 20 00:26 pg_stat`
`drwx------ 2 pg12 pg12  4096 Jun 20 00:26 global`
`drwx------ 4 pg12 pg12  4096 Jun 20 00:30 pg_logical`
`drwx------ 2 pg12 pg12  4096 Jun 20 00:30 pg_twophase`
`drwx------ 2 pg12 pg12  4096 Jun 20 00:31 pg_stat_tmp`
`[pg12@enmodb2 pg_twophase]$` 