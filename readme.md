## 20250703

大模型问AI的通用模板有连接错误  
于是直接使用针对Xinference的方法  
先进行安装  
```bash
pip install --no-cache-dir xinference[all] pandas
```
上面的不用装

查看模型是 Qwen2.5-Coder-14B-Instruct-AWQ  

放弃安装xinference库，直接使用request请求直接干  

## 20250704
1. 停止词不要，输出结果  
2. 关于提示词的问题

这是之前的提示：
```
作为资深的{language}开发专家，请严格按照以下要求编写测试代码：
    1. 使用{library}库编写针对其中的任意函数写测试代码
    2. 仅输出一份可直接执行的源代码，不包含任何注释或解释性文字
    3. 测试代码必须符合{language}的最佳实践和{library}的规范
    4. 代码格式整洁，使用适当的空行分隔不同测试用例
    5. 请不要使用任何Markdown格式，仅输出代码。
    生成{language}代码使用{library}：
```


下面的提示词输出够简单
```
作为资深{language}开发专家，请严格遵守以下要求编写基础代码：

    **核心要求**
    1. 编写针对`{library}`库中任意一个函数的使用
    2. 只使用`{library}`库
    3. 仅输出可直接执行的{language}源代码
    4. 严格禁止包含任何形式的：
    - Markdown代码块(```)
    - 注释或解释性文字
    - 被测试函数的实现代码
```

记录：
变异需要使用：
```bash
pip install langdetect
```

### VScode中环境名出现俩
关闭conda的自动激活,或者关闭VScode的自动激活插件
```bash
conda config --set auto_activate_base False
```

## 20250707-周一

### 环境匹配  
多版本gcc指定默认版本，方法一：直接更改连接将gcc指定为特定版本。  
方法二： 
```bash
# 将gcc-9添加到备选项​
update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-9 90 --slave /usr/bin/g++ g++ /usr/bin/g++-9

# 配置默认版本
update-alternatives --config gcc
```
  
Java8的命名问题：  
1.8.0_161 就是 ​​Java SE 8 Update 161​​  
0_161 表示这是第 161 个更新版本（实际更新号是161）  
因此根据甲骨文官网，选择8u452版本，同时也是apt提供的默认8版本  


记录一次libgflags-dev库的安装使用，安装到环境：
```bash
# 解压源码
tar -xvzf gflags-2.2.2.tar.gz  # 从GitHub上下载
cd gflags-2.2.2

# 创建构建目录
mkdir build && cd build

# 使用CMake配置编译
cmake -DCMAKE_INSTALL_PREFIX=/usr/local ..  # 安装到/usr/local

# 编译并安装
make -j$(nproc)
make install

# 更新共享库缓存
ldconfig
```

## 20250708-周二
查看执行模块，完善gson库的配置，配合执行部分，运行成功；  
查看c++问题?
  
关于数据库的端口映射问题，端口范围是0到65535，而映射直连端口83306不合法  
故，使用lsy的web工具以及本地工具ssh隧道方式。  

## 20250711-周五
细节：promote使用英文试试??  
后期要将markdown的代码块给去掉    
