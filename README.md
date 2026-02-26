# 混合加密演示项目（NTRU + SM4 + DNA/混沌）

## 项目简介
这是一个基于 Python 的混合加密演示项目，核心思路是：

1. 用 **NTRU** 对 SM4 密钥进行加密传输  
2. 用解出的 SM4 密钥对业务明文进行对称加密  
3. 在 SM4 前后叠加 **DNA 混淆** 与 **混沌序列/S 盒** 处理

项目当前实现可完整跑通“加密 -> 解密 -> 还原原文”的端到端流程。

## 主要流程

### Alice（发送方）
1. 生成/设置 SM4 密钥（16 字节）
2. 将 SM4 密钥字符串编码为多项式（Koblitz + Cantor + 三进制映射）
3. 生成 NTRU 密钥对，并逐多项式加密 SM4 密钥
4. 用户输入明文，执行 DNA 混淆
5. 根据密钥生成混沌 S 盒，执行 SM4-CBC 加密

### Bob（接收方）
1. 使用 NTRU 私钥解密恢复 SM4 密钥
2. 生成相同混沌 S 盒，执行 SM4-CBC 解密
3. 执行 DNA 解混淆，恢复原始明文

## 代码结构
- `main.py`：主程序入口，包含混沌参数、DNA 混淆、SM4 封装与完整流程
- `NtruEncrypt.py`：NTRU 相关实现（密钥生成、加密、解密、模逆）
- `Polynomial.py`：多项式对象与基础运算
- `num_to_polynomial.py`：字符到多项式编码/解码（Koblitz 编码链路）
- `character_wise_koblitz_encoding.py`：独立实验脚本（非主流程必需）
- `polynomial_inverter.py`：多项式逆元实验脚本（非主流程必需）
- `Hash/`：本地虚拟环境目录

## 运行环境
- Python 3.13（已在当前项目环境验证）
- 依赖：
  - `cryptography`
  - `sympy`

安装依赖示例（在虚拟环境中）：

```powershell
pip install cryptography sympy
```

## 快速开始
在项目根目录执行：

```powershell
python main.py
```

运行中会提示输入明文：
- 直接回车：使用默认明文 `helloworldfromwx`
- 输入任意字符串：使用你的自定义明文

程序会输出：
- NTRU 公钥
- DNA 混淆后的中间数据
- SM4 密文
- 最终解密还原出的明文

