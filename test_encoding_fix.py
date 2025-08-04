#!/usr/bin/env python3
"""
测试编码修复的脚本
"""

import sys
import os
import codecs
import locale

# 设置编码环境变量
os.environ['PYTHONIOENCODING'] = 'utf-8'

# 检测操作系统并设置适当的编码
def setup_encoding():
    """设置适当的编码以处理不同操作系统的输出"""
    if os.name == 'nt':  # Windows
        # Windows系统特殊处理
        try:
            # 尝试设置控制台代码页为UTF-8
            os.system('chcp 65001 > nul 2>&1')
        except:
            pass
        
        # 设置环境变量
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        
        # 对于Python 3.7+，使用reconfigure
        if hasattr(sys.stdout, 'reconfigure'):
            try:
                sys.stdout.reconfigure(encoding='utf-8', errors='replace')
                sys.stderr.reconfigure(encoding='utf-8', errors='replace')
            except:
                pass
        else:
            # 对于较老的Python版本，使用codecs包装
            try:
                sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
                sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())
            except:
                pass
    else:
        # Unix/Linux系统
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')

# 应用编码设置
setup_encoding()

def test_encoding():
    """测试编码是否正确设置"""
    print("=" * 50)
    print("编码测试")
    print("=" * 50)
    
    # 测试中文字符
    print("测试中文字符: 你好世界")
    print("测试特殊字符: 🚀✨🎉")
    print("测试数字和英文: 123 ABC")
    
    # 测试错误输出
    print("测试错误输出", file=sys.stderr)
    
    # 显示编码信息
    print(f"PYTHONIOENCODING: {os.environ.get('PYTHONIOENCODING', 'Not set')}")
    print(f"stdout encoding: {sys.stdout.encoding}")
    print(f"stderr encoding: {sys.stderr.encoding}")
    print(f"default encoding: {sys.getdefaultencoding()}")
    print(f"locale encoding: {locale.getpreferredencoding()}")
    
    print("=" * 50)
    print("编码测试完成")
    print("=" * 50)

if __name__ == "__main__":
    test_encoding() 