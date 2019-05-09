#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from const import USERNAME, PASSWD, SEMAPHORE
from gethnode import GethNode
from iplist import IPList
from conf import generate_genesis
from functools import wraps
import time
import subprocess
import threading
import re


# class SetGenesis():
#     """Decorator. Set genesis.json file for a chain."""
#     def __init__(self, func):
#         self.func = func
#     def __call__(self, *args):
#         pass
#     def __repr__(self):
#         """Return the function's docstring."""
#         return self.func.__doc__
#     def __get__(self, obj, objtype):
#         """Support instance methods."""
#         return functools.partial(self.__call__, obj)


# def add_peer(node1: GethNode, node2: GethNode, label: int):
#     # Use semaphore to limit number of concurrent threads
#     SEMAPHORE.acquire()
#     node1.add_peer(node2.get_enode(), label)
#     # time.sleep(0.5)
#     SEMAPHORE.release()
#     # print(threading.active_count())


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
            self.accounts.append(self.nodes[index].accounts[0])
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
#                        node._ifSetGenesis = True
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
        generate_genesis(self.blockchain_id, self.accounts, self.config_file)
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
        for node in self.nodes:
            start_geth_command = ('geth --datadir abc --networkid 55661 --cache 512 --port 30303 --rpcport 8545 --rpcapi '
                   'admin,eth,miner,web3,net,personal,txpool --rpc --rpcaddr \"0.0.0.0\" '
                   '--unlock %s --password \"passfile\" --maxpeers 4096 --maxpendpeers 4096 --syncmode \"full\" --nodiscover') % (node.accounts[0])
            command = 'docker exec -td %s %s' % (node.name, start_geth_command) #主机内执行的完整命令
            # print(start_geth_command)
            t = threading.Thread(target=node.ip.exec_command, args=(command,))  #通过ip执行
            t.start()
            threads.append(t)
            time.sleep(0.5)
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
            t = threading.Thread(target=node.set_enode) #设置client的 enode信息
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
                # for j in range(node_count):
                for j in range(i+1, node_count):
                    # add_peer(self.nodes[i], self.nodes[j], 0)  ### limit number of concurrent threads

                    # tmpEnode = self.nodes[j].getEnode()
                    # self.nodes[i].add_peer(tmpEnode, 0) #########
                    # t1 = threading.Thread(target=add_peer, args=(self.nodes[i], self.nodes[j], 0))
                    print("______________________addpeer______________________")
                    t1 = threading.Thread(target=self.nodes[i].add_peer, args=(self.nodes[j].get_enode(),))
                    t1.start()
                    time.sleep(0.05)    # if fail. add this line.
                    # t2 = threading.Thread(target=add_peer, args=(self.nodes[j], self.nodes[i], 0))
                    # t2.start()
                    # time.sleep(0.1)    # O(n)
                    threads.append(t1)
                    # threads.append(t2)
                    # time.sleep(0.3)
                break
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


if __name__ == "__main__":
    ip_list = IPList('ip.txt')
    node_count = 3  #节点数量
    c = SingleChain('vnt', node_count,  121, ip_list)
    c.singlechain_start()
    c.config_consensus_chain()
    c.run_nodes()  #节点互联成功    
    c.get_node_by_index(1).start_miner()
    time.sleep(10)
    pubk = c.get_node_by_index(3).get_pubkeyrlp(str(c.get_node_by_index(3).get_accounts()[0])) 
    mint_hash = c.get_node_by_index(2).send_mint_transaction(c.get_node_by_index(2).get_accounts()[0],"0x100")
    mint_hash=mint_hash.split("\"")[1]
    print("mint-hash=",mint_hash)
    time.sleep(1)     
    send_hash = c.get_node_by_index(2).send_send_transaction(c.get_node_by_index(2).get_accounts()[0],"0x10",str(pubk))
    send_hash=send_hash.split("\"")[1]
    print("send-hash=",send_hash)
    time.sleep(20)
    c.get_node_by_index(1).get_transaction(send_hash)
    deposit_hash=c.get_node_by_index(3).send_deposit_transaction(c.get_node_by_index(3).get_accounts()[0],send_hash)
    print("deposit_hash",deposit_hash)
    redeem_hash=c.get_node_by_index(2).send_redeem_transaction(c.get_node_by_index(2).get_accounts()[0],"0x10") 
    print("redeem_hash",redeem_hash)
    time.sleep(10)
    c.get_node_by_index(1).stop_miner()
    c.destruct_chain()
    



