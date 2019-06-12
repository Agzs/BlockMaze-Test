# !/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
from iplist import IPList
from iplist import exec_command
from const import USERNAME, PASSWD, SEMAPHORE
from time import sleep,time


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
        # --ulimit nofile=<soft limit>:<hard limit> set the limit for open files  docker image name   fzqa/gethzy
        docker_run_command = ('docker run --ulimit nofile=65535:65535 -td -p %d:8545 -p %d:30303 --rm --name %s '
                              'fzqa/gethzy:6.6' % (self.rpc_port, self.ethereum_network_port, self.name))
        sleep(0.4)
        result = self.ip.exec_command(docker_run_command)
        if result:
            if result.startswith('docker: Error'):
                print('error', self.ip.address)
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
            response = r.post(url=url, data=data, headers=self._headers)
            content = json.loads(response.content.decode(encoding='utf-8'))
            #print(content)
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

    def send_public_transaction(self, ffrom, to, value , test_node):
        """eth.sendPublicTransaction()"""
        if isinstance(value, int):  # if value is int, change it to hex str
            value = hex(value)
        params = [{"from": ffrom, "to": to, "value": value, "gasPrice":"0x0"}]  #0x1800000000
        method = 'eth_sendPublicTransaction'
        res = self.rpc_call(method, params)
        t1 = time()
        try:
            t2 = test_transaction(test_node, res)
        except:
            t2 = t1
        return res, t2 - t1

    def send_batch_public_transaction(self, ffrom, to, value, numTx, test_node):
        """eth.sendPublicTransaction()"""
        pub_con_time=[]
        for i in range(numTx):
            pub_hash,t_con=self.send_public_transaction(ffrom, to, value ,test_node)
            pub_con_time.append(t_con)
            # sleep(0.01)
        return pub_con_time

    def send_batch_public_transaction_eth(self, ffrom, to, value, numTx ):
        """eth.sendBatchTransactions({from:eth.accounts[0],to:"156669f9f391aa6a77c494ec6bd4a7761a6541b7",value:web3.toWei(0.05, "ether")}, 1)"""
        if isinstance(numTx, int):  # if value is int, change it to hex str
            numTx = hex(numTx)
        CMD = ("docker exec -t %s /usr/bin/geth attach ipc://root/abc/geth.ipc --exec \"eth.sendBatchPublicTransaction({from:\\\"%s\\\",to:\\\"%s\\\",value:\\\"%s\\\"},\\\"%s\\\")\""%(self.name, ffrom, to, value, numTx))
        print(CMD)
        return exec_command(CMD, self.ip)

    def send_mint_transaction(self, ffrom, value, test_node):
        """eth.sendMintTransaction   ipc版本"""
        CMD = ("docker exec -t %s /usr/bin/geth attach ipc://root/abc/geth.ipc --exec \"eth.sendMintTransaction({from:\\\"%s\\\",value:\\\"%s\\\"})\""%(self.name, ffrom, value))
        mint_hash = exec_command(CMD, self.ip)
        try:
            mint_hash = mint_hash.split("\"")[1]
            t1 = time()
            t2 = test_transaction(test_node, mint_hash)
        except:
            mint_hash = "0x1"
            t1 = 0
            t2 = 0
        return mint_hash, t2 - t1

    def send_send_transaction(self, ffrom, value, pubkey, test_node):
        """eth.sendSendTransaction  ipc"""
        CMD = ("docker exec -t %s /usr/bin/geth attach ipc://root/abc/geth.ipc --exec \"eth.sendSendTransaction({from:\\\"%s\\\",value:\\\"%s\\\",pubKey:\\\"%s\\\"})\""%(self.name, ffrom, value, pubkey))
        send_hash = exec_command(CMD, self.ip)
        try:
            send_hash = send_hash.split("\"")[1]
            print("send_hash" , send_hash)
            t1 = time()
            t2 = test_transaction(test_node, send_hash)
        except:
            send_hash = "0x1"
            t1 = 0
            t2 = 0
        return send_hash, t2 - t1

    def get_pubkeyrlp(self, addr, pwd="root"):
        """eth.getPubKeyRLP("0xeac93e13065db05706d7b60e29be532f350a3078","root") """
        params = [addr , pwd]
        method = 'eth_getPubKeyRLP'
        sleep(0.2)
        return self.rpc_call(method, params)

    def send_deposit_transaction(self, ffrom, txHash, test_node, key = "root"):
        """eth.sendDepositTransaction  ipc"""
        CMD = ("docker exec -t %s /usr/bin/geth attach ipc://root/abc/geth.ipc --exec \"eth.sendDepositTransaction({from:\\\"%s\\\",txHash:\\\"%s\\\",key:\\\"%s\\\"})\""%(self.name, ffrom, txHash, key))
        deposit_hash = exec_command(CMD, self.ip)
        try:
            deposit_hash = deposit_hash.split("\"")[1]
            print("deposit_hash", deposit_hash)
            t1 = time()
            t2 = test_transaction(test_node, deposit_hash)
        except:
            deposit_hash = "0x1"
            t1 = 0
            t2 = 0
        return deposit_hash, t2 - t1

    def send_redeem_transaction(self, ffrom, value, test_node):
        """eth.sendRedeemTransaction  ipc"""
        CMD = ("docker exec -t %s /usr/bin/geth attach ipc://root/abc/geth.ipc --exec \"eth.sendRedeemTransaction({from:\\\"%s\\\",value:\\\"%s\\\"})\""%(self.name, ffrom, value))
        redeem_hash = exec_command(CMD, self.ip)
        try:
            redeem_hash = redeem_hash.split("\"")[1]
            t1 = time()
            t2 = test_transaction(test_node, redeem_hash)
        except:
            redeem_hash = "0x1"
            t1 = 0
            t2 = 0
        return redeem_hash, t2 - t1

    def get_transaction(self, tran_hash):
        """eth.getTransaction()"""
        method = 'eth_getTransactionByHash'
        params = [tran_hash]
        #print(params)
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

    def get_blocknum(self):
        method = 'eth_blockNumber'
        result = self.rpc_call(method)
        return int(result, 16) if result else 0

    def add_peer(self, *args):
        """admin.addPeer()"""
        method = 'admin_addPeer'
        params = list(args)
        # sleep(0.02)
        result = self.rpc_call(method, params)
        return result

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


def test_transaction(node, tran):
    t_b = time()
    while True:
        # if node.get_transaction(tran) != "":
        if node.get_transaction(tran) != None:
            # print(node.get_transaction(tran))
            tran_info = node.get_transaction(tran)
            if tran_info['blockNumber'] !=  None:
                return time()
        t_e=time()
        if t_e-t_b > 500:
            return 0
        sleep(0.5)

if __name__ == "__main__":
    IPlist = IPList('ip.txt')
    n = GethNode(IPlist, 1, 121)
    n.start()
    n.set_enode()
    print(n.accounts)
    n.stop()
    print("success")
