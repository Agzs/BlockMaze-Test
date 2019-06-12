#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Mar 16 11:04:55 2019

@author: rkd
"""

import json
from const import MAXPAYLOAD, NODE_COUNT, PUB_COUNT


def generate_genesis_poa(chain_id, accounts, config_file):
    """Generate a genesis file."""
    with open('vnt.json', 'rb') as f:  
        genesis = json.load(f)
    genesis['config']['chainId'] = chain_id
    min_nums = (NODE_COUNT-1)//MAXPAYLOAD + 1  
    min_accounts = []
    for i in range(min_nums):
        min_accounts.append(accounts[i * MAXPAYLOAD])
    genesis['extraData'] = '0x' + '0'*64  + ''.join(min_accounts) + '0' * 130

    pub_nums = PUB_COUNT 
    pub_accounts = []
    for i in range(pub_nums):
        pub_accounts.append(accounts[1 + i * MAXPAYLOAD])
    print("pubaccount",pub_accounts)
    for i, acc in enumerate(accounts):
        if (acc in pub_accounts or acc in min_accounts): 
            genesis['alloc'][acc] = {'balance': "0x100000000000000000000000000000000000000000000000000000200000000"}
            continue                                                       
        genesis['alloc'][acc] = {'balance': "0x000000000000000000000000000000000000000000000000000000200000000"} 

    new_genesis = json.dumps(genesis, indent=2) 
    with open(config_file, 'w') as f:
        print(new_genesis, file=f)


def generate_genesis_pow(chain_id, accounts, config_file):
    """Generate a genesis file."""
    with open('vnt.json', 'rb') as f:
        genesis = json.load(f)
    genesis['config']['chainId'] = chain_id

    pub_nums = PUB_COUNT  
    pub_accounts = []
    for i in range(pub_nums):
        pub_accounts.append(accounts[1 + i * MAXPAYLOAD])
    print("pubaccount", pub_accounts)
    for i, acc in enumerate(accounts):
        if (acc in pub_accounts ):
            genesis['alloc'][acc] = {'balance': "0x100000000000000000000000000000000000000000000000000000200000000"}
            continue
        genesis['alloc'][acc] = {
            'balance': "0x000000000000000000000000000000000000000000000000000000200000000"} 


    new_genesis = json.dumps(genesis, indent=2) 
    with open(config_file, 'w') as f:
        print(new_genesis, file=f)