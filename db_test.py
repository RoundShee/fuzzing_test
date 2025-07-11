from sqlalchemy import create_engine, Column, String, DateTime, Text, Boolean, Enum
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base
from sqlalchemy.dialects.mysql import BINARY, INTEGER
import os
from model_source import raw_test_code

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
    usecase = Column(Text, nullable=True)
    count = Column(INTEGER(unsigned=True), nullable=False)
    vuln = Column(Boolean, nullable=True)
    status = Column(Enum('suc', 'fail', 'run', name='task_status'), nullable=True)

class Mutation(Base):
    __tablename__ = 'mutation'
    id = Column(BINARY(16), primary_key=True, nullable=False)
    seq = Column(INTEGER(unsigned=True), primary_key=True, nullable=False)
    usecase = Column(Text, nullable=False)
    result = Column(Enum('suc', 'err', 'vuln', name='mutation_result'), nullable=False, server_default='suc')

Base.metadata.create_all(engine)

import atexit
def shutSession():
    db_session.remove()
atexit.register(shutSession)



if __name__ == '__main__':
    tasks = db_session.query(Task.id).all()
    # 这是遍历给ID
    for task in tasks:
        print(task.id.hex())
    # ???
    task = db_session.query(Task).filter(Task.id == tasks[0].id).first()   # 不一定是 tasks[0].id，并且 id 的类型不是字符串！！！
    if task:
        task.status = 'run'
        db_session.commit()

    # 存入测试用例
    test_code = raw_test_code('java', 'gson')
    if task:
        task.usecase = test_code
        db_session.commit()

    # 变异
    taskID = bytes.fromhex("c1b9ad350c13a120a9e4f3cc2be845ef")
    task = db_session.query(Task).filter(Task.id == taskID).first()   # 不一定是 taskID，并且 id 的类型不是字符串！！！
    if task:
        print(task.usecase)
        print(task.count)
    

    ## 下面是测试变异写入读取
    # taskID = bytes.fromhex("c1b9ad350c13a120a9e4f3cc2be845ef")

    # mutation = Mutation(id=taskID, seq=4, usecase=raw_test_code('java', 'gson'))
    # db_session.add(mutation)
    # db_session.commit()
    # mutations = db_session.query(Mutation).filter(Mutation.id == taskID)
    # for mutation in mutations:
    #     print(f"seq: 第 {mutation.seq} 次变异，usecase: {mutation.usecase}")
