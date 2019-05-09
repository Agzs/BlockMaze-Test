import requests
import json
from time import sleep
import threading
import paramiko

ipaddr="172.25.170.170"

def rpc_call(method, params=[]):
    """Make a rpc call to this geth node."""
    data = json.dumps({  ## json string used in HTTP requests
        'jsonrpc': '2.0',
        'method': method,
        'params': params,
        'id': 121
    })
    url = "http://{}:{}".format(ipaddr, 8545)
    # _headers = {'Content-Type': 'application/json', 'Connection': 'close'}
    _headers = {'Content-Type': 'application/json'}
    SEMAPHORE = threading.BoundedSemaphore(10)
    SEMAPHORE.acquire()
    with requests.Session() as r:
        response = r.post(url=url, data=data, headers=_headers, timeout=300)
        content = json.loads(response.content.decode(encoding='utf-8'))
        print(content)
        result = content.get('result')
    SEMAPHORE.release()
    err = content.get('error')
    if err:
        raise RuntimeError(err.get('message'))

    print('%s @%s : %s    %s' % (method,ipaddr, 8545, result))
    return result

def get_pubkeyrlp(addr, pwd="root"):
    """eth.getPubKeyRLP("0xeac93e13065db05706d7b60e29be532f350a3078","root")     success"""
    #params = [{"from":addr , "pwd":pwd}]
    params = [addr , pwd]
    method = 'eth_getPubKeyRLP'
    sleep(0.2)
    return rpc_call(method, params)

def send_public_transaction(ffrom, to, value):
    """eth.sendPublicTransaction()"""
    if isinstance(value, int):  # if value is int, change it to hex str
        value = hex(value)
    params = [{"from": ffrom, "to": to, "value": value}]
    method = 'eth_sendPublicTransaction'
    sleep(0.2)
    return rpc_call(method, params)

# def send_mint_transaction(ffrom, value):
#     """eth.sendMintTransaction"""
#     if isinstance(value, int):  # if value is int, change it to hex str
#         value = hex(value)
#     params = [{"from" : ffrom , "value" : value}]
#     method = 'eth_sendMintTransaction'
#     sleep(0.2)
#     return rpc_call(method, params)

def send_mint_transaction(ffrom, value):
    """eth.sendMintTransaction   ipc版本"""
    #       /home/fzqa/gopath/bin/geth attach ipc:/home/fzqa/gopath/src/github.com/ethereum/test/pow/signer1/data/geth.ipc --exec "eth.sendMintTransaction({from:\"0xd9308512e4a748888c17cc60157c3899fc8cd8a7\",value:\"0x100\"})"
    CMD = ("/home/fzqa/gopath/bin/geth attach ipc:/home/fzqa/gopath/src/github.com/ethereum/test/pow/signer1/data/geth.ipc --exec \"eth.sendMintTransaction({from:\\\"%s\\\",value:\\\"%s\\\"})\""%(ffrom,value))
    return exec_command(CMD)



def exec_command(cmd, ip_address=ipaddr, port=22, username="fzqa", password="123150"):
    """Exec a command on remote server using SSH connection."""
    with paramiko.SSHClient() as client:
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(ip_address, port, username, password)
        sleep(0.2)
        print("cmd=",cmd)
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        sleep(0.1)
        out = stdout.read().strip().decode(encoding='utf-8')
        err = stderr.read().strip().decode(encoding='utf-8')
        if not err:
            result = out
        else:
            result = err
        print("result",result)
    return result

def get_balance(account):
    """eth.getBalance()"""
    if not account.startswith('0x'):
        account = '0x' + account
    method = 'eth_getBalance'
    params = [account, 'latest']
    return rpc_call(method, params)


if __name__ == "__main__":
    #test get_pubkeyrlp
    get_pubkeyrlp("0xd9308512e4a748888c17cc60157c3899fc8cd8a7")
    # print(len("0x60d66677c9d7713dbecd739b302f38c86b84d1bb"))
    #
    # send_public_transaction("0x60d66677c9d7713dbecd739b302f38c86b84d1bb","0x34c09031d03b935c569def72ae8116357bda3169","0x5")
    #
    send_mint_transaction("0xd9308512e4a748888c17cc60157c3899fc8cd8a7","0x100")
    #get_balance("0xd9308512e4a748888c17cc60157c3899fc8cd8a7")
    #send_public_transaction("0xd9308512e4a748888c17cc60157c3899fc8cd8a7","0x34c09031d03b935c569def72ae8116357bda3169","0x5")


