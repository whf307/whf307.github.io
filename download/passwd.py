#!/usr/bin/python
###################################################################################################################################
## Author             : whf307
## Created            : 2018-01-09
## Mail               : whf307@gmail.com
## Website            : https://whf307.github.io
## Platform           : Linux
## Python             : 2.7
## How to use         : chmod +x passwd.py   &  ./passwd.py 
## About the scripts  : To generate a strong password with 4 digital , 4 capital letters ,4 small letters and 4 special character
###################################################################################################################################

import random

#difine the base char to use
c1=random.sample('0123456789',4) 
c2=random.sample('~!#$%^&*()_+',4) 
c3=random.sample('abcdefghijklmnopqrstuvwxyz',4) 
c4=random.sample('ABCDEFGHIJKLMNOPQRSTUVWXYZ',4) 

#genereate digital for each position
passwd1=c1+c2+c3+c4

#shuffle the items
items = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]
random.shuffle(items)
passwd2=[]
for i in items:
        passwd2.append(passwd1[items[i]])
        passwd=''.join(passwd2)
print passwd