#!/bin/bash

echo "========================================"
echo "Patent-DeepScientist Strategist Graph"
echo "========================================"
echo ""

# 检查虚拟环境是否存在
if [ ! -f ".venv/bin/activate" ]; then
    echo "[错误] 虚拟环境不存在！"
    echo "正在创建虚拟环境..."
    python3 -m venv .venv
    if [ $? -ne 0 ]; then
        echo "[失败] 无法创建虚拟环境"
        exit 1
    fi
    echo "[成功] 虚拟环境已创建"
    echo ""
fi

# 激活虚拟环境
echo "[1/3] 激活虚拟环境..."
source .venv/bin/activate
if [ $? -ne 0 ]; then
    echo "[失败] 无法激活虚拟环境"
    exit 1
fi
echo "[成功] 虚拟环境已激活"
echo ""

# 安装/更新依赖
echo "[2/3] 检查并安装依赖..."
pip install -r requirements.txt --quiet
if [ $? -ne 0 ]; then
    echo "[警告] 部分依赖安装失败，但继续运行..."
else
    echo "[成功] 依赖已安装"
fi
echo ""

# 运行主程序
echo "[3/3] 运行 Strategist Graph..."
echo "========================================"
echo ""
python strategist_graph.py

echo ""
echo "========================================"
echo "执行完成！"
echo "========================================"
