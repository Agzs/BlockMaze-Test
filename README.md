### 配置环境

#### 安装python3.7

查看版本： `python3 --version`

1、使用wget下载安装包
```
wget https://www.python.org/ftp/python/3.7.1/Python-3.7.1rc2.tgz
```
> 这个地址可以在：`https://www.python.org/downloads/source/`找到对应的版本。

2、解压该压缩文件: `tar zxvf Python-3.7.1rc2.tgz`

3、进去py这个目录，并编译安装
```
cd Python-3.7.1rc2
./configure
make
make install
```
编译问题参考[No module named '_ctypes'](https://blog.csdn.net/wang725/article/details/79905612)

4、创建软连接
```
rm -rf /usr/bin/python3
rm -rf /usr/bin/pip3
ln -s /usr/local/python3/bin/python3.7 /usr/bin/python3
ln -s /usr/local/python3/bin/pip3.7 /usr/bin/pip3
```

参考[升级文档](https://www.cnblogs.com/wongyi/p/9824236.html)

#### 安装环境依赖

```
sudo pip3 requests paramiko
sudo apt-get install openssh-server sshpass
```
安装问题参考[error](https://blog.csdn.net/zxd675816777/article/details/39119767)

#### docker
1、安装
```sh
sudo apt-get update
sudo apt-get install apt-transport-https ca-certificates
sudo apt-get install docker.io
````
可参考[官方指南](https://docs.docker.com/install/linux/docker-ce/ubuntu/)

2、添加docker用户组
```sh
sudo groupadd docker

sudo gpasswd -a USER docker \\USER换成自己的账户名

sudo service docker restart

newgrp - docker

```

3、通过Dockerfile生成镜像（不需要做）
```
进入Dockerfile所在目录
docker build -t fzqa/gethzy:latest .   在本地生成镜像
docker push fzqa/gethzy:latest    上传到官方仓库 需注册帐号
```

4、获取docker  vnttest 镜像
```
docker pull fzqa/gethzy:latest

docker配置结束   
docker images  查看镜像
docker ps 查看运行容器
docker ps -a  查看所有容器
docker rm containerid 删除容器
docker rmi imageid 删除镜像
```

### 文件介绍
* ip.txt  存放多主机ip地址
* const.py  ssh使用需要的用户名和密码
* conf.py   对json文件的处理
* iplist.py   对ip的处理，端口的一些分配，rpc端口和以太坊监听端口
* gethnode.py   单个节点的操作，通过rpc执行的addpeer等，通过ipc执行的send、Mint、update等
* singlechain.py   整条链的节点启动、连接、测试等所有的操作都是在该文件内
* localtest.py   用于本地rpc、ipc脚本测试

> mint、send等交易通过rpc执行时，执行成功但无返回值，使用ipc来执行交易，ssh连接到主机ip再通过docker exec （目前无法解决）

### 运行脚本
修改`const.py`中的用户名和密码

1、执行：
```
python3 iplist.py && python3 singlechain.py
```
如果报` No such file or directory: '/home/ethtest/.ssh/known_hosts'`，根据目录创建一个空文件即可。

> 如果程序出错崩溃，`docker container`依然存在，通过 `python3 iplist.py`销毁所有容器，启动挖矿后sleep一段时间以初始化

2、坑
* `c.get_node_by_index(3).get_pubkeyrlp(str(c.get_node_by_index(3).get_accounts()[0]))`，`get_pubkeyrlp`成功
* `mint_hash=c.get_node_by_index(2).send_mint_transaction(c.get_node_by_index(2).get_accounts()[0],"0x100")`，`mint` 成功
* 交易返回的`hash`值需要进行处理, 有多余字符, `mint_hash=mint_hash.split("\"")[1]`
* `c.get_node_by_index(1).get_transaction(mint_hash)`, 交易未写入块, 需要等待！！！！！！`get_transaction`
* `send_hash = c.get_node_by_index(2).send_send_transaction(c.get_node_by_index(2).get_accounts()[0],"0x10",str(pubk))`，`send` 成功
