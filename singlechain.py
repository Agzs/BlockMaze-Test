#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from const import USERNAME, PASSWD, SEMAPHORE, MAXPAYLOAD, NODE_COUNT, PUB_COUNT, MINER_COUNT
from gethnode import GethNode
from iplist import IPList
from conf import generate_genesis_poa,generate_genesis_pow
from functools import wraps
import time
import subprocess
import threading
from resultthread import MyThread
import shutil



class SingleChain():
    """
    Data structure for a set of Geth-pbft clients for a single blockchain.
    """
    #SingleChain(     'zzzz', node_count,  121, ip_list)
    def __init__(self, name, node_count, blockchain_id, ip_list, username=USERNAME, password=PASSWD):

        # Check if the input params are legal.
        if node_count > ip_list.get_full_count():
            raise ValueError("not enough IPs")

        self.username = username
        self.password = password
        self.chain_id = name    # chain id
        self.node_count = node_count
        self.blockchain_id = blockchain_id
        self.ip_list = ip_list
        self.nodes = []
        self.ips = set()
        self.if_set_number = False
        self.if_set_id = False
        self.is_terminal = False
        self.config_file = None
        self.accounts = []

    def singlechain_start(self):
        """Start all containers for a single chain."""
        threads = []
        for index in range(self.node_count):
            node_index = index + 1
            tmp = GethNode(self.ip_list, node_index, self.blockchain_id, self.username, self.password)
            self.ips.add(tmp.ip)
            self.nodes.append(tmp)
            # xq start a thread， target stand for a function that you want to run ,args stand for the parameters
            t = threading.Thread(target=tmp.start)
            t.start()
            threads.append(t)
            time.sleep(0.3)

        for t in threads:
            # xq threads must run the join function, because the resources of main thread is needed
            t.join()

        for index in range(self.node_count):
            print(index,self.nodes[index].accounts[0])
            self.accounts.append(self.nodes[index].accounts[0])
        print('The corresponding accounts are as follows:')
        print(self.accounts)

    def set_genesis(config):
        """Decorator for setting genesis.json file for a chain."""

        @wraps(config)
        def func(self, *args):
            config(self, *args)
            for server_ip in self.ips:
                #ssh登陆不能在命令行中指定密码 sshpass 可以   
                #sshpass和ssh配合远程登录  sshpass -p [passwd] ssh -p [port] root@192.168.X.X
                #sshpass和scp配合发送文件到服务器   sshpass -p 123456 scp mkssh.txt root@slave1:/root/
                #将config_file远程发送到主机里
                subprocess.run(['sshpass -p %s scp %s %s@%s:%s' % (self.password, self.config_file,
                               self.username, server_ip.address, self.config_file)], stdout=subprocess.PIPE, shell=True)
                time.sleep(0.2)
                threads = []
                for node in self.nodes:
                    if node.ip == server_ip:
                        #对于每个容器  将config_file 从主机copy到容器/root/目录下
                        command = 'docker cp %s %s:/root/%s' % (self.config_file, node.name, self.config_file)
                        t = threading.Thread(target=server_ip.exec_command, args=(command,))
                        t.start()
                        threads.append(t)
                        print('copying genesis file')
                        #node._ifSetGenesis = True
                        time.sleep(0.1)
                for t in threads:
                    t.join()
            time.sleep(0.5)
        return func

    @set_genesis
    def config_consensus_chain(self):
        """Set genesis.json for a blockchain & init with genesis.json."""
        if self.chain_id is "":
            self.config_file = '0.json'
        else:
            self.config_file = '%s.json' % self.chain_id
        generate_genesis_pow(self.blockchain_id, self.accounts, self.config_file)
        time.sleep(0.02)

    @set_genesis
    def config_terminal(self):
        """Set genesis.json for terminal equipments."""
        if len(self.chain_id) == 4:
            self.config_file = '0.json'
        else:
            self.config_file = '%s.json' % self.chain_id[:-4]

    def run_nodes(self):
        """Run nodes on a chain."""
        self.init_geth()
        self.run_geth_nodes()
        self.construct_chain()

    def init_geth(self):
        """
        run geth init command for nodes in a chain
        """
        print("self.config_file=",self.config_file)
        if self.config_file is None:
            raise ValueError("initID is not set")
        threads = []
        for server_ip in self.ips:
            for node in self.nodes:
                if node.ip == server_ip:
                    init_geth_command = 'docker exec -t %s geth --datadir abc init %s' % (node.name, self.config_file)
                    t = threading.Thread(target=server_ip.exec_command, args=(init_geth_command,))
                    t.start()
                    threads.append(t)
                    time.sleep(0.1)
        for t in threads:
            t.join()

    def run_geth_nodes(self):
        threads = []
        for i,node in enumerate(self.nodes):
            if i in list(range(0, MINER_COUNT * MAXPAYLOAD, MAXPAYLOAD)):
                print("full", node.ip , node.rpc_port)
                start_geth_command = ('geth --datadir abc --networkid 55661 --cache 2048 --port 30303 --rpcport 8545 --rpcapi '
                       'admin,eth,miner,web3,net,personal,txpool --rpc --rpcaddr 0.0.0.0 '
                       '--unlock %s --password passfile --gasprice 0 --maxpeers 4096 --maxpendpeers 4096 --syncmode full --nodiscover 2>>%s.log') % (node.accounts[0], node.name)
            else:
                start_geth_command = ('geth --datadir abc --networkid 55661 --cache 2048 --port 30303 --rpcport 8545 --rpcapi '
                                     'admin,eth,miner,web3,net,personal,txpool --rpc --rpcaddr 0.0.0.0 '
                                     '--unlock %s --password passfile --gasprice 0 --maxpeers 4096 --maxpendpeers 4096 --syncmode fast --nodiscover 2>>%s.log') % (node.accounts[0], node.name)
            command = 'docker exec -d %s bash -c \"%s\" ' % (node.name, start_geth_command) 
            t = threading.Thread(target=node.ip.exec_command, args=(command,))  
            t.start()
            threads.append(t)
            time.sleep(0.1)
        for t in threads:
            t.join()
        print('node starting')
        # must wait here
        for _ in range(3):
            print('.', end='')
            time.sleep(1)
        print()
        threads = []
        for node in self.nodes:
            t = threading.Thread(target=node.set_enode) 
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
        print("-------------------------set node----------------")
        # for node in self.nodes:
        #     node.set_enode()
        time.sleep(0.1)

    def get_chain_id(self):
        """return chain id of the chain."""
        return self.chain_id

    def get_primer_node(self):
        """Return the primer node of the set of Geth-pbft clients."""
        return self.nodes[0]

    def get_node_by_index(self, node_index):
        """Return the node of a given index."""
        if node_index <= 0 or node_index > len(self.nodes):
            raise ValueError("node index out of range")
        return self.nodes[node_index-1]

    def construct_chain(self):
        """Construct a single chain.  节点互联"""
        if not self.is_terminal:
            print("constructing single chain")
            start_time = time.time()
            threads = []
            node_count = len(self.nodes)

            # connect nodes in a single chain with each other
            for i in range(node_count):
                if i in list(range(0, MINER_COUNT * MAXPAYLOAD, MAXPAYLOAD)):
                    num = 1
                else:
                    num = 20
                for j in range(i+1, node_count, num):
                    print("______________________addpeer______________________")
                    t1 = threading.Thread(target=self.nodes[i].add_peer, args=(self.nodes[j].get_enode(),))
                    t1.start()
                    time.sleep(0.01)    # if fail. add this line.
                    threads.append(t1)
                # break
            for t in threads:
                t.join()
            print('active threads:', threading.active_count())
            end_time = time.time()
            print('%.3fs' % (end_time - start_time))
            print("-------------------------")
            time.sleep(len(self.nodes)//10)

    def destruct_chain(self):
        """Stop containers to destruct the chain."""
        threads = []
        for node in self.nodes:
            t = threading.Thread(target=node.stop)
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

    def get_node_count(self):
        """Return the number of nodes of the blockchain."""
        return len(self.nodes)

    def start_miner(self):
        """Start miners of all nodes on the chain."""
        if not self.is_terminal:
            threads = []
            for node in self.nodes:
                t = threading.Thread(target=node.start_miner)
                t.start()
                threads.append(t)
                time.sleep(0.02)
            for t in threads:
                t.join()

#批量普通交易
def send_mul_pub(pub_nodes , pub_accounts , numTx,test_node):
    threads = []
    for i in range(PUB_COUNT):
        t = MyThread(pub_nodes[i].send_batch_public_transaction, args=(pub_accounts[i], "0x9d59d8f0092a391caacdebbc3e944ea200e2b41b","0x1000000000000000000000000000000000000", numTx//PUB_COUNT,test_node[i%query_num]))
        threads.append(t)
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    for t in threads:
        t_consen = t.get_result()
        pub_tran_time.extend(t_consen)
    print(pub_tran_time)
    return pub_tran_time

def send_mul_pub_eth(pub_nodes , pub_accounts , numTx):
    '''用于后台发送交易'''
    threads = []
    for i in range(PUB_COUNT):
        t = MyThread(pub_nodes[i].send_batch_public_transaction_eth, args=(pub_accounts[i], "0x9d59d8f0092a391caacdebbc3e944ea200e2b41b","0x100000000000000000000000000000", numTx//PUB_COUNT))
        threads.append(t)
    for t in threads:
        t.start()
    for t in threads:
        t.join()



def fn_back_1(pub_nodes , pub_accounts, nums = 200 ):
    send_mul_pub_eth(pub_nodes , pub_accounts , nums)  # 难度值 1000000
    threading.Timer(1 , fn_back_1, args=(pub_nodes, pub_accounts)).start()

# def fn_back_2(pub_nodes , pub_accounts ,test_node , nums = 200):
#     send_mul_pub(pub_nodes , pub_accounts , nums , test_node)  # 难度值 1000000
#     threading.Timer(0 , fn_back_2, args=(pub_nodes, pub_accounts,test_node )).start()

# 批量发送mint交易
def send_mul_mint(mint_num , nodes , accos , pub_nodes , pub_accounts , numTx , test_node):
    mint_tran_time = []
    pub_time = []
    threads = []
    t1=time.time()
    for i in range(mint_num):
        t = MyThread(nodes[i].send_mint_transaction , args=(accos[i],"0x1000",test_node[i%query_num]))
        threads.append(t)
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    t2 = time.time()
    if numTx != 0:
        send_mul_pub_eth(pub_nodes, pub_accounts, numTx)
    print("mint_time",t2-t1)
    mint_hash_list = []
    for t in threads:
        try:
            mint_hash, t_consen = t.get_result()
        except:
            mint_hash="0x1"
            t_consen=0
        mint_hash_list.append(mint_hash)
        mint_tran_time.append(t_consen)
    print(mint_hash_list)
    print(mint_tran_time)
    mint_tran_time.sort()
    pub_time.sort()
    return t2-t1, pub_time, mint_tran_time

def get_mul_pubkey(pk_num , nodes , accos):
    """可用于测试节点是否工作 ， 除去不工作的节点"""
    threads = []
    t1=time.time()
    for i in range(pk_num):
        t = MyThread(nodes[i].get_pubkeyrlp , args=(accos[i] , "root"))
        threads.append(t)
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    t2=time.time()
    print("time_pubkeyrlp",t2-t1)  #1s
    pkrlp = []
    for i,t in enumerate(threads):
        if(t.get_result() == None):
            nodes.remove(nodes[i])
            accos.remove(accos[i])
        elif(t.get_result().startswith("0x")):
            pkrlp.append(t.get_result())
        else:
            nodes.remove(nodes[i])
    print(pkrlp)
    return pkrlp

def send_mul_send(send_num , pk_num , pkrlp , nodes , accos, pub_nodes , pub_accounts , numTx , test_node):
    send_tran_time = []
    pub_time = []
    threads = []
    t1=time.time()
    for i in range(send_num):
        t = MyThread(nodes[i].send_send_transaction , args=(accos[i], "0x10", pkrlp[pk_num-i-1],test_node[i%query_num]))
        threads.append(t)
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    t2=time.time()
    if numTx != 0:
        send_mul_pub_eth(pub_nodes, pub_accounts, numTx)
    print("send_time",t2-t1) 
    send_hash_list = []
    for t in threads:
        try:
            send_hash, t_consen = t.get_result()
        except:
            send_hash="0x1"
            t_consen=0
        send_hash_list.append(send_hash)
        send_tran_time.append(t_consen)
    print(send_hash_list)
    print(send_tran_time)
    send_tran_time.sort()
    pub_time.sort()
    return send_hash_list,pub_time,send_tran_time

def send_mul_deposit(send_hash_list , deposit_num , pk_num , nodes , accos , pub_nodes , pub_accounts , numTx , test_node):
    deposit_tran_time = []
    pub_time = []
    threads = []
    t1=time.time()
    for i in range(deposit_num):
        t = MyThread(nodes[i].send_deposit_transaction , args=(accos[i], send_hash_list[pk_num-i-1],test_node[i%query_num]))
        threads.append(t)
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    t2=time.time()
    if numTx != 0:
        # pub_time = send_mul_pub(pub_nodes, pub_accounts, numTx,test_node)
        send_mul_pub_eth(pub_nodes, pub_accounts, numTx)
    print("deposit_time",t2-t1)  #80s
    deposit_hash_list = []
    for t in threads:
        try:
            deposit_hash, t_consen = t.get_result()
        except:
            deposit_hash="0x1"
            t_consen=0
        deposit_hash_list.append(deposit_hash)
        deposit_tran_time.append(t_consen)
    print(deposit_hash_list)
    print(deposit_tran_time)
    deposit_tran_time.sort()
    pub_time.sort()
    return t2-t1,pub_time,deposit_tran_time

def send_mul_redeem(redeem_num , nodes , accos ,pub_nodes , pub_accounts , numTx , test_node):
    redeem_tran_time = []
    pub_time = []
    threads = []
    t1=time.time()
    for i in range(redeem_num):
        t = MyThread(nodes[i].send_redeem_transaction , args=(accos[i] , "0x10",test_node[i%query_num]))
        threads.append(t)
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    t2=time.time()
    if numTx != 0:
        # pub_time = send_mul_pub(pub_nodes, pub_accounts, numTx,test_node)
        send_mul_pub_eth(pub_nodes, pub_accounts, numTx)
    print("redeem_time", t2 - t1)  # 30s
    redeem_hash_list = []
    for t in threads:
        try:
            redeem_hash, t_consen = t.get_result()
        except:
            redeem_hash="0x1"
            t_consen=0
        redeem_hash_list.append(redeem_hash)
        redeem_tran_time.append(t_consen)
    print(redeem_hash_list)
    print(redeem_tran_time)
    redeem_tran_time.sort()
    pub_time.sort()
    return t2-t1,pub_time,redeem_tran_time

def mul_miner_start( nodes ):
    threads = []
    for i in range(len(nodes)):
        t = threading.Thread(nodes[i].start_miner())
        threads.append(t)
    for t in threads:
        t.start()
    for t in threads:
        t.join()


query_num = 10

pub_tran_time = []

if __name__ == "__main__":
    f = IPList('ip.txt')
    print("success")
    f.stop_all_containers()
    time.sleep(1)
    f.remove_all_containers() 

    shutil.copyfile("vnt-pow.json","vnt.json")  
    ip_list = IPList('ip.txt') 
    print("ip_nums=",len(ip_list.ips))
    
    c = SingleChain('vnt', NODE_COUNT,  121, ip_list)
    c.singlechain_start() 
    c.config_consensus_chain() 
    c.run_nodes()  

    miner_nums = MINER_COUNT  
    miner_nodes = [] 
    for i in range(miner_nums):
        miner_nodes.append(c.nodes[ i * MAXPAYLOAD])
    miner_accounts = [i.get_accounts()[0] for i in miner_nodes]

    pub_nums = PUB_COUNT 
    pub_nodes = [] 
    for i in range(pub_nums):
        pub_nodes.append(c.nodes[1 + i * MAXPAYLOAD])
    pub_accounts = [] 
    for i in pub_nodes:
        pub_accounts.append(i.get_accounts()[0])


    send_nums = NODE_COUNT - miner_nums - pub_nums  
    send_nodes = [i for i in c.nodes if i not in miner_nodes and i not in pub_nodes] 
    send_accounts = []
    for i in send_nodes:
        send_accounts.append(i.get_accounts()[0])
    
    print("pub",pub_accounts)
    print("send",send_accounts)

    for i in miner_nodes:
        i.start_miner()

    time.sleep(100)
    print('success')