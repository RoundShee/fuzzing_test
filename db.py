from sqlalchemy import create_engine, Column, String, DateTime, Text, Boolean, Enum
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base
from sqlalchemy.dialects.mysql import BINARY, INTEGER, LONGTEXT
import os

engine = create_engine('mysql+pymysql://yb:88888888@172.17.0.12/sfp', echo=False)

Session = sessionmaker(bind=engine)
db_session = scoped_session(Session)

Base = declarative_base()
Base.query = db_session.query_property()

class Task(Base):
    __tablename__ = 'task'
    
    id = Column(BINARY(16), primary_key=True, default=lambda: os.urandom(16))
    name = Column(String(50), nullable=False)
    time = Column(DateTime, nullable=False, server_default='CURRENT_TIMESTAMP')
    lang = Column(String(50), nullable=False)
    lib = Column(String(50), nullable=False)
    usecase = Column(LONGTEXT, nullable=True)
    count = Column(INTEGER(unsigned=True), nullable=False)
    vuln = Column(Boolean, nullable=True)
    status = Column(Enum('suc', 'fail', 'run'), nullable=True)
    

class Mutation(Base):
    __tablename__ = 'mutation'
    id = Column(BINARY(16), primary_key=True, nullable=False)
    seq = Column(INTEGER(unsigned=True), primary_key=True, nullable=False)
    usecase = Column(LONGTEXT, nullable=False)
    result = Column(Enum('suc', 'err', 'vuln'), nullable=False, server_default='suc')
    output = Column(Text, nullable=False)

Base.metadata.create_all(engine)

import atexit
def shutSession():
    db_session.remove()
atexit.register(shutSession)

'''上面的别动！！！'''
''' 如果自己操作坏了增加了乱七八糟的数据，到 http://192.168.1.19:45993 网页，点击清理全部，清空数据库 task 表和 mutation 表所有数据'''
''' 数据库操作教程 '''
# 安装依赖 pip install sqlalchemy pymysql
# 调用该文件时将此文件放入当前目录下，然后 from db import db_session, Task, Mutation
if __name__ == '__main__':
    ''' 生成模块须看！'''
    # 后端只提供 id，进入 http://192.168.1.19:45993/ 网页点击新建任务，传参问题后期合并后面再说，先手动传参
    # 此时新任务的 id 已经存入数据库 task 表中，前端只展示前 8 位数字
    # 运行下面代码可查看所有任务 ID， 结合前端的展示的 8 位 ID 可以找到刚刚新建任务的 id
    tasks = db_session.query(Task.id).all()
    for task in tasks:
        print(task.id.hex())
    # 刚运行时需要该模块根据任务 id 把任务状态改成 run（字符固定好的，不要自己设定），前端不会变化，因为要循环监控，我把这一块暂时关闭了
    task = db_session.query(Task).filter(Task.id == tasks[0].id).first()   # 不一定是 tasks[0].id，并且 id 的类型不是字符串！！！
    if task:
        task.status = 'run'
        db_session.commit()
    # 生成结束后产生一个原始测试用例，将用例存入数据库 task 表
    task = db_session.query(Task).filter(Task.id == tasks[0].id).first()   # 不一定是 tasks[0].id，并且 id 的类型不是字符串！！！
    if task:
        task.usecase = '生成的测试用例'
        db_session.commit()
    
    ''' 变异模块须看！'''
    # 生成模块结束后，传入特定的任务 id 给变异模块，传参问题后期合并后面再说，先手动传参
    # 通过任务 id 获取原始测试用例和变异总数
    taskID = bytes.fromhex("cbcfccf88f0122ffdf718125d940a65f")
    task = db_session.query(Task).filter(Task.id == taskID).first()   # 不一定是 taskID，并且 id 的类型不是字符串！！！
    if task:
        print(task.usecase)
        print(task.count)
    # 变异结束后产生变异用例，将任务 id、变异用例和变异的顺序存入数据库 mutation 表
    # mutation = Mutation(id=taskID, seq=57, usecase="变异测试用例")  # 将第 57 次变异的测试用例存入数据库，不能有第二条数据 id 和 seq 同时一模一样(id1 == id2 && seq1 == seq2)，否则报错
    # db_session.add(mutation)
    # db_session.commit()

    ''' 执行模块须看！ '''
    # 变异模块结束后，传入特定的任务 id 给行模块，传参问题后期合并后面再说，先手动传参
    # 通过任务 id 获取原始测试用例
    taskID = bytes.fromhex("cbcfccf88f0122ffdf718125d940a65f")
    task = db_session.query(Task).filter(Task.id == taskID).first()
    if task:
        print(task.usecase)
    # 通过任务 id 获取所有的变异测试用例和对应的变异顺序
    mutations = db_session.query(Mutation).filter(Mutation.id == taskID)
    for mutation in mutations:
        print(f"seq: 第 {mutation.seq} 次变异，usecase: {mutation.usecase}")
    # 执行模块完成后，将变异用例执行结果存入 mutation 表，将有无漏洞情况和运行状态存入 task表（对于数据库来说，是改操作不是增操作，不要 db_session.add！！！）
    mutation = db_session.query(Mutation).filter(Mutation.id == taskID and Mutation.seq == 57).first() # 修改第 57 次变异用例执行结果
    if mutation:
        mutation.result = 'suc'    # suc 是成功执行，err 是语法错误，vuln 是触发漏洞（这三个字符全部固定的，不要自己设定）
        mutation.output = 'xxxxxxxxxxxxxxxxxxxxxxx'
        db_session.commit()
    task = db_session.query(Task).filter(Task.id == taskID).first()
    if task:
        task.vuln = False
        task.status = 'suc' # run 是正在运行，suc 是测试结束，fail 是测试失败，出现意外中断了测试（这三个字符全部固定的，不要自己设定）
        db_session.commit()

