#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import threading

USERNAME = 'dell'  # username of servers
PASSWD = 'dell@2017'  # password of servers
# USERNAME = 'ethtest'  # username of servers
# PASSWD = 'test'  # password of servers
MAXPAYLOAD = 3  # maximum number of containers running on one server
SEMAPHORE = threading.BoundedSemaphore(10)
MINER_COUNT = 12
NODE_COUNT = 12 * MAXPAYLOAD   #所有节点数  最大为 主机数×MAXPAYLOAD  270                     32*5-10 = 150   360
PUB_COUNT = 10  #发送普通交易节点数  10