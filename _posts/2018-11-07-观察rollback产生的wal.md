---
category: pg
---



pg回滚会不会写wal呢？

我们知道Oracle肯定会写的，来看看pg的吧

用的pg11

![image-20181107114328330](/var/folders/rs/ycl_gwmx6v3_nf84nhfvk7v00000gn/T/abnerworks.Typora/image-20181107114328330.png)



## 一、commit 时的wal

### 1.1 t3表插入

![image-20181107114250396](/var/folders/rs/ycl_gwmx6v3_nf84nhfvk7v00000gn/T/abnerworks.Typora/image-20181107114250396.png)

### 1.2 查看wal

![image-20181107114451301](/var/folders/rs/ycl_gwmx6v3_nf84nhfvk7v00000gn/T/abnerworks.Typora/image-20181107114451301.png)

commit的话看到insert和commit了。



## 二、事务中，暂时不提交

### 2.1 begin插入

![image-20181107114621113](/var/folders/rs/ycl_gwmx6v3_nf84nhfvk7v00000gn/T/abnerworks.Typora/image-20181107114621113.png)

### 2.2 观察wal

![image-20181107114658368](/var/folders/rs/ycl_gwmx6v3_nf84nhfvk7v00000gn/T/abnerworks.Typora/image-20181107114658368.png)

不提交的时候，我们看到有running的事务。



## 三、rollback

### 3.1 紧接着rollback掉

 	                  ![image-20181107114734545](/var/folders/rs/ycl_gwmx6v3_nf84nhfvk7v00000gn/T/abnerworks.Typora/image-20181107114734545.png)

### 3.2 观察wal

![image-20181107114803886](/var/folders/rs/ycl_gwmx6v3_nf84nhfvk7v00000gn/T/abnerworks.Typora/image-20181107114803886.png)

rollback之后，607这个事务abort了，但是也记录了wal的。



## 四、Oracle中rollback的redo

我们用logminer挖归档，直接看v$logmnr_contents视图

![image-20181107115032655](/var/folders/rs/ycl_gwmx6v3_nf84nhfvk7v00000gn/T/abnerworks.Typora/image-20181107115032655.png)

![image-20181107115715859](/var/folders/rs/ycl_gwmx6v3_nf84nhfvk7v00000gn/T/abnerworks.Typora/image-20181107115715859.png)

可以看到，上面部分delete的rollback字段是1，而且这部分是按rowid来删除的，可以肯定是回滚产生的delete记录了。最下面那部分是我执行delete，然后commit看到的redo记录，rollback部分是0，而且可以看到sql是正常的显示。