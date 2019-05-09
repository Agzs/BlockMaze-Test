1.安装docker
sudo apt-get update
sudo apt-get install apt-transport-https ca-certificate
ssudo apt-get install docker-engine

2.通过Dockerfile生成镜像  （不需要做）
进入Dockerfile所在目录
docker build -t rkdghd/gethzy:latest .   在本地生成镜像
docker push rkdghd/gethzy:latest    上传到官方仓库 需注册帐号

3.获取docker  vnttest 镜像
docker pull rkdghd/gethzy:latest

docker配置结束   
docker images  查看镜像
docker ps 查看运行容器
docker ps -a  查看所有容器
docker rm containerid 删除容器
docker rmi imageid 删除镜像


测试脚本介绍：  基于python3
ip.txt  存放多主机ip地址
const.py  ssh使用需要的用户名和密码
conf.py   对json文件的处理
iplist.py   对ip的处理，端口的一些分配，rpc端口和以太坊监听端口
gethnode.py   单个节点的操作，通过rpc执行的addpeer等，通过ipc执行的send、Mint、update等
singlechain.py   整条链的节点启动、连接、测试等所有的操作都是在该文件内
localtest.py   用于本地rpc、ipc脚本测试

mint、send等交易通过rpc执行时，执行成功但无返回值，使用ipc来执行交易，ssh连接到主机ip再通过docker exec （目前无法解决）


执行：
python singlechain.py
如果程序出错崩溃  docker container依然存在  通过 python iplist.py销毁所有容器
启动挖矿后sleep一段时间以初始化

# c.get_node_by_index(3).get_pubkeyrlp(str(c.get_node_by_index(3).get_accounts()[0]))                        get_pubkeyrlp成功
# mint_hash=c.get_node_by_index(2).send_mint_transaction(c.get_node_by_index(2).get_accounts()[0],"0x100")   mint 成功
# 交易返回的hash值需要进行处理   有多余字符    mint_hash=mint_hash.split("\"")[1]
# c.get_node_by_index(1).get_transaction(mint_hash)  交易未写入块   需要等待   ！！！！！！                        get_transaction
# send_hash = c.get_node_by_index(2).send_send_transaction(c.get_node_by_index(2).get_accounts()[0],"0x10",str(pubk)) send 成功