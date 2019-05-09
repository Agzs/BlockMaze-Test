# !/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
from iplist import IPList
from iplist import exec_command
from const import USERNAME, PASSWD, SEMAPHORE
from time import sleep


# class GethNode0(object):
#     """data structure for geth client running in a docker container"""
#
#     def __init__(self, userName=USERNAME, passWord=PASSWD):
#         self.enode = ''
#         self.ip, self.rpc_port, self.ethereum_network_port = IPlist.getNewPort()
#         self.name = 'geth-pbft' + str(self.rpc_port)
#         self._headers = {'Content-Type': 'application/json', 'Connection': 'close'}
#         self._userName = USERNAME
#         self.password = PASSWD
#         self.accounts = []
#         self._ifSetGenesis = False
#
#     def start(self):
#         """start a container for geth client """
#         pass


class GethNode():
    """Data structure for Geth-pbft client.    单独一个"""

    def __init__(self, ip_list, node_index, blockchain_id, username=USERNAME, password=PASSWD):
        self.enode = ''
        self.id = node_index    # used in rpc call
        self.ip, self.rpc_port, self.ethereum_network_port = ip_list.get_new_port() 
        self.node_index = node_index
        self.blockchain_id = blockchain_id
        self.name = 'geth-vnt' + str(self.rpc_port)    # docker container name of this node
        self._headers = {'Content-Type': 'application/json', 'Connection': 'close'}    # for rpc call use
        self.username = username    # user name of login user of a server
        self.password = password    # password of login user of a server
        self.accounts = []    # accounts list of a geth node

    def start(self):
        """Start a container for geth on remote server and create a new account."""
        # --ulimit nofile=<soft limit>:<hard limit> set the limit for open files  docker image name   rkdghd/gethzy
        docker_run_command = ('docker run --ulimit nofile=65535:65535 -td -p %d:8545 -p %d:30303 --rm --name %s '
                              'rkdghd/gethzy:latest' % (self.rpc_port, self.ethereum_network_port, self.name))
        sleep(0.4)
        result = self.ip.exec_command(docker_run_command)
        if result:
            if result.startswith('docker: Error'):
                raise RuntimeError('An error occurs while starting docker container. Container maybe already exists')
            print('container of node %s of blockchain %s at %s:%s started' % (self.node_index, self.blockchain_id,
                                                                              self.ip.address, self.rpc_port))
        new_account_command = 'docker exec -t %s geth --datadir abc account new --password passfile' % self.name  #passfile 在dockerimage里
        sleep(0.1)
        account = self.ip.exec_command(new_account_command).split()[-1][1:-1]
        sleep(0.2)
        if len(account) == 40:    # check if the account is valid
            self.accounts.append(account)

    def rpc_call(self, method, params=[]):
        """Make a rpc call to this geth node."""
        data = json.dumps({  ## json string used in HTTP requests
            'jsonrpc': '2.0',
            'method': method,
            'params': params,
            'id': self.id
        })
        # print("rpcdata=",data)
        url = "http://{}:{}".format(self.ip.address, self.rpc_port)
        SEMAPHORE.acquire()
        with requests.Session() as r:
            response = r.post(url=url, data=data, headers=self._headers, timeout=120)
            content = json.loads(response.content.decode(encoding='utf-8'))
            print(content)
            result = content.get('result')
        SEMAPHORE.release()
        err = content.get('error')
        if err:
            raise RuntimeError(err.get('message'))

        print('%s @%s : %s    %s' % (method, self.ip.address, self.rpc_port, result))
        return result

    def get_enode(self):
        """Return enode information from admin.nodeInfo"""
        return self.enode

    def get_peer_count(self):
        """net.peerCount"""
        method = 'net_peerCount'
        sleep(0.02)
        result = self.rpc_call(method)
        return int(result, 16) if result else 0  # change hex number to dec

    def get_peers(self):
        """admin.peers"""
        method = 'admin_peers'
        return self.rpc_call(method)

    def new_account(self, password='root'):
        """personal.newAccount(password)"""
        method = 'personal_newAccount'
        params = [password]
        account = self.rpc_call(method, params)
        sleep(0.1)
        self.accounts.append(account[2:])

    def key_status(self):
        """admin.key_status()"""
        method = 'admin_keyStatus'
        return self.rpc_call(method)

    def unlock_account(self, account='0', password='root', duration=86400):
        """personal.unlockAccount()"""
        method = 'personal_unlockAccount'
        params = [account, password, duration]
        return self.rpc_call(method, params)

    def send_public_transaction(self, ffrom, to, value):
        """eth.sendPublicTransaction()"""
        if isinstance(value, int):  # if value is int, change it to hex str
            value = hex(value)
        params = [{"from": ffrom, "to": to, "value": value}]
        method = 'eth_sendPublicTransaction'
        sleep(0.2)
        return self.rpc_call(method, params)
    
    # def send_mint_transaction(self, ffrom, value):
    #     """eth.sendMintTransaction"""
    #     if isinstance(value, int):  # if value is int, change it to hex str
    #         value = hex(value)
    #     params = [{"from" : ffrom , "value" : value}]
    #     method = 'eth_sendMintTransaction'
    #     sleep(0.2)
    #     return self.rpc_call(method, params)

    def send_mint_transaction(self, ffrom, value):
        """eth.sendMintTransaction   ipc版本"""
        CMD = ("docker exec -t %s /usr/bin/geth attach ipc://root/abc/geth.ipc --exec \"eth.sendMintTransaction({from:\\\"%s\\\",value:\\\"%s\\\"})\""%(self.name, ffrom, value))
        return exec_command(CMD, self.ip)

    def send_send_transaction(self, ffrom, value, pubkey):
        """eth.sendSendTransaction  ipc"""
        CMD = ("docker exec -t %s /usr/bin/geth attach ipc://root/abc/geth.ipc --exec \"eth.sendSendTransaction({from:\\\"%s\\\",value:\\\"%s\\\",pubKey:\\\"%s\\\"})\""%(self.name, ffrom, value, pubkey))
        return exec_command(CMD, self.ip)

    def get_pubkeyrlp(self, addr, pwd="root"):
        """eth.getPubKeyRLP("0xeac93e13065db05706d7b60e29be532f350a3078","root") """
        params = [addr , pwd]
        method = 'eth_getPubKeyRLP'
        sleep(0.2)
        return self.rpc_call(method, params)

    def send_deposit_transaction(self, ffrom, txHash, key = "root"):
        """eth.sendDepositTransaction  ipc"""
        CMD = ("docker exec -t %s /usr/bin/geth attach ipc://root/abc/geth.ipc --exec \"eth.sendDepositTransaction({from:\\\"%s\\\",txHash:\\\"%s\\\",key:\\\"%s\\\"})\""%(self.name, ffrom, txHash, key))
        print("CMD=",CMD)
        return exec_command(CMD, self.ip)

    def send_redeem_transaction(self, ffrom, value):
        """eth.sendRedeemTransaction  ipc"""
        CMD = ("docker exec -t %s /usr/bin/geth attach ipc://root/abc/geth.ipc --exec \"eth.sendRedeemTransaction({from:\\\"%s\\\",value:\\\"%s\\\"})\""%(self.name, ffrom, value))
        return exec_command(CMD, self.ip)

    def get_transaction(self, tran_hash):
        """eth.getTransaction()"""
        method = 'eth_getTransactionByHash'
        params = [tran_hash]
        print(params)
        return self.rpc_call(method, params)

    def get_accounts(self):
        """eth.accounts"""
        method = 'eth_accounts'
        return self.rpc_call(method)

    def get_balance(self, account):
        """eth.getBalance()"""
        if not account.startswith('0x'):
            account = '0x' + account
        method = 'eth_getBalance'
        params = [account, 'latest']
        return self.rpc_call(method, params)

    def get_block_transaction_count(self, index):
        """eth.getBlockTransactionCount()"""
        method = 'eth_getBlockTransactionCountByNumber'
        params = [hex(index)]
        result = self.rpc_call(method, params)
        return int(result, 16) if result else 0  # change hex number to dec

    def add_peer(self, *args):
        """admin.addPeer()"""
        method = 'admin_addPeer'
        params = list(args)
        # sleep(0.02)
        result = self.rpc_call(method, params)
        return result

#    def addPeer(self, *args, **kwargs):
#        """IPC version"""
#        try:
#            CMD = ("docker exec -t %s geth attach ipc://root/abc/geth.ipc "
#                   "--exec \"admin.addPeer%s\"" %(self.name, args))
#            self.ip.exec_command(CMD)
#            sleep(1)
#        except Exception as e:
#            if self._exception is False:
#                self._exception = True
#                self.ip.exec_command(CMD)
#                sleep(1)
#            else:
#                raise RuntimeError('%s:%s %s %s' % (self.ip, self.ethereum_network_port, self.rpc_port, e))

    def set_enode(self):
        """Set enode info of a node."""
        method = 'admin_nodeInfo'
        result = self.rpc_call(method)  # result from rpc call
        enode = result['enode'].split('@')[0]
        self.enode = '{}@{}:{}'.format(enode, self.ip.address, self.ethereum_network_port)


    def txpool_status(self):
        """txpool.status"""
        method = 'txpool_status'
        result = self.rpc_call(method)
        sleep(0.1)
        print("txpool.status pending:%d, queued:%d" % (int(result['pending'], 16),
                                                       int(result['queued'], 16)))

    def start_miner(self):
        """miner.start()"""
        method = 'miner_start'
        return self.rpc_call(method)

    def stop_miner(self):
        """miner.stop()"""
        method = 'miner_stop'
        return self.rpc_call(method)

    def get_block_by_number(self, block_number):
        """eth.getBlock()"""
        # check if index is greater than or equal 0
        if block_number < 0:
            raise ValueError('blockNumber should be non-negative')

        block_number_hex_string = hex(block_number)
        method = 'eth_getBlockByNumber'
        params = [block_number_hex_string, 'true']
        sleep(0.1)
        return self.rpc_call(method, params)

    def get_transaction_by_block_number_and_index(self, block_number, index):

        block_number_hex_string = hex(block_number)
        index_hex_string = hex(index)
        method = 'eth_getTransactionByBlockNumberAndIndex'
        params = [block_number_hex_string, index_hex_string]
        result = self.rpc_call(method, params)  # result from rpc call
        return result['hash']

    def is_geth_running(self):
        """Check if the client is running."""
        command = 'docker exec -t %s geth attach ipc://root/abc/geth.ipc --exec "admin.nodeInfo"' % self.name
        result = self.ip.exec_command(command)
        return False if result.split(':')[0] == 'Fatal' else True

    def stop(self):
        """Remove the geth-pbft node container on remote server."""
        stop_command = "docker stop %s" % self.name
        self.ip.exec_command(stop_command)
        print('node %s of blockchain %s at %s:%s stopped' % (self.node_index, self.blockchain_id, self.ip.address, self.rpc_port))


if __name__ == "__main__":
    IPlist = IPList('ip.txt')
    n = GethNode(IPlist, 1, 121)
    n.start()
    n.set_enode()
    print(n.accounts)
    n.stop()
    print("success")
