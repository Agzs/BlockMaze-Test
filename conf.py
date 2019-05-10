#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Mar 16 11:04:55 2019

@author: rkd
"""

import json

def generate_genesis(chain_id, accounts, config_file):
    """Generate a genesis file."""
    with open('vnt.json', 'rb') as f:  #先在本地json打开
        genesis = json.load(f)
    genesis['config']['chainId'] = chain_id

    for acc in accounts:
        i = 0
        i = i + 1
        if (i == 1 or i == 2):
            genesis['alloc'][acc] = {'balance': "0x100000000000000000000000000000000000000000000000000000200000000"}
            continue                                                       
        genesis['alloc'][acc] = {'balance': "0x000000000000000000000000000000000000000000000000000000200000000"} #添加余额 
        
    #extra_data = '0x' + '0'*64 + ''.join(accounts) + '0' * 130
    #print("extra data in genesis file", extra_data)
    #genesis['extraData'] = extra_data

    new_genesis = json.dumps(genesis, indent=2) #ident 缩进相关
    with open(config_file, 'w') as f:
        print(new_genesis, file=f)

