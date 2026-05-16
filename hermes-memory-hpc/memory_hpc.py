#!/usr/bin/env python3
"""
Hermes memory-hpc 海马体 - 供应商长期记忆
Phase 3: 长出海马体

供应商记忆：
- 每笔采购结束后自动提炼摘要，存入 ChromaDB
- 询价时自动检索历史，生成"想起上次..."
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import chromadb
import json
import time
from datetime import datetime

MEMORY_PATH = os.path.expanduser("~/.hermes/supplier_memory")

# ─────────────────────────────────────────
# ChromaDB 初始化
# ─────────────────────────────────────────
_client = None

def get_client():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=MEMORY_PATH)
    return _client


def get_supplier_collection():
    """获取供应商记忆库"""
    client = get_client()
    return client.get_or_create_collection(
        name="suppliers",
        metadata={"description": "供应商记忆库"}
    )


def get_conversation_collection():
    """获取对话记忆库"""
    client = get_client()
    return client.get_or_create_collection(
        name="conversations",
        metadata={"description": "对话历史记忆"}
    )


# ─────────────────────────────────────────
# 供应商记忆 CRUD
# ─────────────────────────────────────────
def remember_supplier(
    supplier_name: str,
    product: str = None,
    price: float = None,
    delivery_days: int = None,
    attitude: str = None,   # 积极/一般/推脱
    notes: str = None,
    source: str = "1688"
):
    """
    存入一条供应商记忆
    """
    collection = get_supplier_collection()

    fact = json.dumps({
        "supplier": supplier_name,
        "product": product,
        "price": price,
        "delivery_days": delivery_days,
        "attitude": attitude,
        "notes": notes,
        "source": source,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M")
    }, ensure_ascii=False)

    doc_id = f"{supplier_name}_{int(time.time())}"
    collection.add(
        documents=[fact],
        metadatas=[{
            "supplier": supplier_name,
            "product": product,
            "price": price,
            "attitude": attitude,
            "source": source
        }],
        ids=[doc_id]
    )
    print(f"[memory] 已记住：{supplier_name} - {product} - ¥{price}")
    return doc_id


def recall_supplier(supplier_name: str, query: str = None, top_k: int = 3) -> list:
    """
    检索某供应商的历史记忆
    """
    collection = get_supplier_collection()

    if query:
        results = collection.query(
            query_texts=[query],
            n_results=top_k,
            where={"supplier": supplier_name}
        )
    else:
        results = collection.get(
            where={"supplier": supplier_name}
        )

    if not results or not results.get("documents"):
        return []

    memories = []
    # ChromaDB query() 返回嵌套 [[...]]，get() 返回扁平 [...]
    docs = results["documents"]
    metas = results.get("metadatas")
    if docs and isinstance(docs[0], list):
        docs = docs[0]
    if metas and isinstance(metas[0], list):
        metas = metas[0]
    if not metas:
        metas = [{}] * len(docs)

    for doc, meta in zip(docs, metas):
        try:
            # 兼容单引号 JSON（Qwen/旧数据问题）
            if isinstance(doc, str) and doc.startswith("{"):
                clean_doc = doc.replace("'", '"')
            else:
                clean_doc = doc
            data = json.loads(clean_doc)
            memories.append(data)
        except (json.JSONDecodeError, TypeError):
            if isinstance(meta, dict):
                memories.append({"raw": doc, **meta})
            else:
                memories.append({"raw": doc, "supplier": supplier_name})
    return memories


def get_supplier_summary(supplier_name: str) -> str:
    """
    生成供应商摘要（给老板看的格式）
    """
    memories = recall_supplier(supplier_name, top_k=10)
    if not memories:
        return f"还没有 {supplier_name} 的记忆"

    prices = [m.get("price") for m in memories if m.get("price")]
    attitudes = [m.get("attitude") for m in memories if m.get("attitude")]

    summary = f"【{supplier_name}】历史记录 {len(memories)} 条\n"
    if prices:
        summary += f"  价格区间：¥{min(prices)} ~ ¥{max(prices)}\n"
        summary += f"  最近报价：¥{prices[-1]}\n"
    if attitudes:
        attitude_count = {a: attitudes.count(a) for a in set(attitudes)}
        dominant = max(attitude_count, key=attitude_count.get)
        summary += f"  态度：{dominant}（累计 {attitude_count[dominant]} 次）\n"

    # 找最新笔记
    notes = [m.get("notes") for m in reversed(memories) if m.get("notes")]
    if notes:
        summary += f"  最新备注：{notes[0]}"

    return summary


def compare_suppliers(supplier_a: str, supplier_b: str, product: str) -> str:
    """
    对比两个供应商的历史价格
    """
    a_mem = recall_supplier(supplier_a, top_k=10)
    b_mem = recall_supplier(supplier_b, top_k=10)

    # 按产品名过滤
    a_mem = [m for m in a_mem if product in str(m.get("product", ""))]
    b_mem = [m for m in b_mem if product in str(m.get("product", ""))]

    a_prices = [m.get("price") for m in a_mem if m.get("price")]
    b_prices = [m.get("price") for m in b_mem if m.get("price")]

    lines = [f"【{supplier_a} vs {supplier_b}】"]
    if a_prices:
        lines.append(f"  {supplier_a}：¥{min(a_prices)}~¥{max(a_prices)}（{len(a_prices)}条记录）")
    else:
        lines.append(f"  {supplier_a}：暂无记录")

    if b_prices:
        lines.append(f"  {supplier_b}：¥{min(b_prices)}~¥{max(b_prices)}（{len(b_prices)}条记录）")
    else:
        lines.append(f"  {supplier_b}：暂无记录")

    return "\n".join(lines)


# ─────────────────────────────────────────
# 对话记忆（老板的消息模式）
# ─────────────────────────────────────────
def remember_conversation(role: str, content: str, tags: list = None):
    """记录一次对话摘要"""
    collection = get_conversation_collection()
    doc = json.dumps({
        "role": role,
        "content": content[:200],  # 只存前200字
        "tags": tags or [],
        "time": datetime.now().strftime("%Y-%m-%d %H:%M")
    }, ensure_ascii=False)

    collection.add(
        documents=[doc],
        ids=[f"msg_{int(time.time())}"]
    )


def recall_conversations(query: str, top_k: int = 5) -> list:
    """检索历史对话"""
    collection = get_conversation_collection()
    results = collection.query(
        query_texts=[query],
        n_results=top_k
    )
    return [json.loads(d) for d in results.get("documents", []) if d]


# ─────────────────────────────────────────
# 自检
# ─────────────────────────────────────────
if __name__ == "__main__":
    print("=== Hermes memory-hpc 自检 ===")

    # 存入一条测试记忆
    remember_supplier(
        supplier_name="义乌星火包装",
        product="纸箱 50*40*30",
        price=5.2,
        delivery_days=3,
        attitude="积极",
        notes="老板姓王，说话直接"
    )

    # 查询
    print("\n查询结果：")
    print(get_supplier_summary("义乌星火包装"))

    # 对比
    remember_supplier("温州华鑫纸业", "纸箱 50*40*30", 5.5, 2, "一般")
    print("\n对比：")
    print(compare_suppliers("义乌星火包装", "温州华鑫纸业", "纸箱"))
