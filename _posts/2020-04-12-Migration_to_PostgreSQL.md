---
category: pg
---

最近做去O或者迁移到pg的有点多，而这也正是我想要做的。写一篇文章记录整理一下。

## 一、 觉悟

不管是O还是去其他的数据库，不管是国产化还是降成本，决策层一定要有一个心理的预期。脱离业务谈架构都是耍流氓。也不是去了O你就可以方便你的管理运维了。事实上的大多数去O都是给自己找事情。

这个觉悟便是去O或者迁移到pg，你的一个心理准备，包括业务的支持程度、运维人员招聘、开发人员熟悉一个数据库、和以前大不一样的运维管理方式、费用的支出以及最重要的一点，出问题有没有人能搞定。

然而，去年以来各种迁移去O如火如荼。Oracle的DBA都被逼着转型了，中高级Oracle DBA越来越难招，pg就更不用说了。做，还是要做的。



## 二、可行性分析

一个项目，决策层可能细节问题都不了解，POC或者自己测试的时候才暴露出问题。前期的调研、验证和规划就相当重要了。这是一个项目成功的基石。

不是说MySQL不好，就算分布式的他还是一个MySQL，如果硬拿着不能建视图存过触发器（开发规范要求）来支持复杂的业务逻辑，那就是真的给自己找事情，就更不用说一个慢SQL把数据库拖垮的事情了。当然8.0什么的就不谈了，新版本很多不一样需要时间和项目去验证。

同样，去O，不管是迁移到pg还是其他的国产数据库，能不能很好地支持你的业务，这点非常重要，需要技术人员的充分调研来支持最后的决策。当然，最后的决策就不仅仅是技术的问题了。



##  三、迁移

### 3.1 调研

这里很重要！！！

* 老库的数据库编码，新库支持的编码还有你迁移中需要的文件格式编码。这些一定要前期调研清楚
* 数据类型map，有些java代码可能读取了数据类型的符号，比如O的number对应到pg的numeric就没问题
* 需要迁移的数据量大小
* 需要迁移的用户、对象

### 3.2 新库的安装部署规划

哪怕是测试环境，也是需要尽可能做到最优，而不是安装起就好了。主备模式、备份恢复、数据参数等等，都需要规划好。做好沟通和协调。

### 3.3 迁移方案

O到pg可以ora2pg等等的很多工具，很多厂商也有成熟的一键迁移工具，当然也可以自己手动以txt的格式来导出导入。比如O的sqlldr导出文本格式（导出文件记得utf8编码），pg端copy导入。具体的方案也需要去测试评估去选择。

### 3.4 迁移步骤

* 表结构改造和导入

* 索引导出ddl，新库去创建索引

* 视图和序列

* 存过改造

* 其他对象

* 迁移完成后数据对比

* 统计信息收集

### 3.5 功能和性能测试

可以按需测试数据库功能和性能，这里可以dba来测，也需要业务来测试部分sql。压测可以看tpmc等等，压测的工具就很多了。如benckmarksql、jmeter等等。

### 3.6 输出

按需看是否出具测试报告，压测报告，问题报告等等。



## 四、整体实施计划

有些测试可能只有你一个dba来完成，有些需要业务配合，有些需要很多小伙伴一起来配合。这里的话时间表和分工协作就很重要了。

调研清楚之后，每个步骤的工作量，需要协同的人员和事项，按时间分配，不要一个人抗压，有事情解决不了可以向上汇报沟通，也不要遇到问题就问人，自己多思考。

总之，沟通最重要。有了一致的目标和方案才能做得更好。







------------------

--whf307

--20200413

--Life is fantastic
