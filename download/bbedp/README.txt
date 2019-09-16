This script is used to print and edit block offset of PostgreSQL pages,written in python 2.7 .And you can use it only on Linux,if you want to use it on other platfrom like AIX ,maybe you could edit it again youself,good luck!

Just find the $PGDATA,oid of database and relfilenode into ./file and then u can use it now! 
For $PGDATA  excute "echo $PGDATA" or "ps -ef | grep postgres" to find the data directory!!! 
For others,just run "select pg_relation_filepath('t1');" to find the file path.
And edit the ./file like '/oracle/soft/pg_data/base/13323/16422'
And then ,run chmod 755 bbedp,and execute "./bbedp" ,the new world is here.

If you have any problem about it, please concat with me.

Mail:whf307@gmail.com
*******************************************************************************************
Ex:
[pg@whf307 soft]$ more file
/oracle/soft/pg11rc_data/base/13285/16394
[pg@whf307 soft]$ ./bbedp 
Password: 

BBEDP: Release 0.1.0.0.0 - Limited Production on Thur Nov 01 14:06:31 2018

Copyright (c) 2018, 2018, whf307 and/or its affiliates.  All rights reserved.

************* !!! For PostgreSQL Internal Test only !!! *************** 

BBEDP> help
set block [blpck_offset]
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
exit :quit the program
BBEDP> 
BBEDP> exit
[pg@whf307 soft]$
*******************************************************************************************
