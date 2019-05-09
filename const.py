#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import threading

USERNAME = 'fzqa'  # username of servers
PASSWD = '123150'  # password of servers
MAXPAYLOAD = 15  # maximum number of containers running on one server
SEMAPHORE = threading.BoundedSemaphore(10)