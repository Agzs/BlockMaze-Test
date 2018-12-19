from singlechain import SingleChain
from ips import IPList
import threading
import time
import gethnode
from hibechain import HIBEChain
count = 0
rightCount = 0
while count < 1000:
    startTime = time.time()
    IPlist = IPList('ip.txt')
    IDList = ["", "1", "11", "12", "13"]
    threshList = [(3, 2), (2, 1), (1, 1), (1,1), (1,1)]
    startTime = time.time()
    hibe = HIBEChain(IDList, threshList, IPlist)
        
    hibe.constructHIBEChain()
    hibe.setNumber()#门限
    hibe.setLevel()#层次
    hibe.setID()#id
    endTime = time.time()

    a, b, c, d = hibe.getChain(''), hibe.getChain('1'), hibe.getChain('11'), hibe.getChain("12")
    ap1 = a.getPrimer()
    bp1 = b.getPrimer()
    cp1 = c.getPrimer()
    dp1 = d.getPrimer()
    print(ap1.getPeerCount(), bp1.getPeerCount(), cp1.getPeerCount(), dp1.getPeerCount()) # 4 7 2 2
    if ap1.getPeerCount() == 4 and bp1.getPeerCount() == 7 and cp1.getPeerCount() == 2 and cp1.getPeerCount() == 2:
        rightCount += 1 
    count += 1
    time.sleep(2)
    hibe.destructHIBEChain()
    endTime = time.time()
    print('count = ',count,'rightCount = ',rightCount,'time = ',endTime-startTime)