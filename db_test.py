from sqlalchemy import create_engine, Column, String, DateTime, Text, Boolean, Enum
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base
from sqlalchemy.dialects.mysql import BINARY, INTEGER
import os
from model_source import raw_test_code  # 生成导入
from text32 import mutate_test_case  # 变异导入


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


def one_click(id, lang, lib, mutate_count):
    """
    前端用户一次请求:原始生成,多次变异执行
    输入id, lang, lib是字符串  mutate_count为int型
    """
    taskID = bytes.fromhex(id)
    task = db_session.query(Task).filter(Task.id == taskID).first()  # 这里应该不考虑找不到的情况
    task.status = 'run'
    raw_code = raw_test_code(lang, lib)  # 生成测试用例
    task.usecase = raw_code
    db_session.commit()  # 提交task表的statues以及usecase

    # 以下内容应为相同ID,不同次数的变异次数时:变异-执行写入
    temp_mutate_code = ""  # 迭代变异代码
    for seq in range(1,mutate_count+1):
        if seq == 1:
            temp_mutate_code = raw_code
        while 1:  # 防止返回空值,但存在模型一直不响应的死循环问题
            temp = mutate_test_case(temp_mutate_code)
            if temp:
                break
        temp_mutate_code = temp
        # 建立表,暂存入变异,提交
        mutation = Mutation(id=taskID, seq=seq, usecase=temp_mutate_code)
        db_session.add(mutation)
        db_session.commit()
        # 执行
        # 没给接口,只有代码存放路径,且没有正确清除上一次执行后所有原始以及中间文件
        # TODO 增加执行接口
        # 这里执行完
        mutation.result = 'suc'
        # mutation.output =   ## 这里定义没有，但数据库有？
        db_session.commit()
    # 上面应该是try语句,根据运行情况写入task表
    task.vuln = False
    task.status = 'suc' # run 是正在运行，suc 是测试结束，fail 是测试失败
    db_session.commit()
    
if __name__ == '__main__':
    id = "06E4BE02D0C81FF097499DEB5C9FBA29"
    one_click(id=id, lang='C++', lib="libgflags-dev", mutate_count=100)
