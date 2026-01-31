# Notion · Obsidian · Neo4j 联动方案

目标：把书签知识图谱作为系统核心（Neo4j），让 Obsidian 承担思考写作、Notion 承担结构化运营，三者分层协作而非全量同步。

## 0. 设计哲学

一句话原则：

- **Neo4j = 真相源（Source of Truth）**
- **Obsidian = 思考与写作界面**
- **Notion = 结构化任务与运营界面**

| 系统 | 核心职责 | 不做什么 |
| --- | --- | --- |
| Neo4j | 知识关系、推理、全局结构 | 不写长文、不管理任务 |
| Obsidian | 思考、沉淀、概念演化 | 不负责全局一致性 |
| Notion | 项目、进度、清单、视图 | 不做深层语义推理 |

## 1. 总体架构

```
                 ┌─────────────┐
                 │   Chrome    │
                 │  Bookmarks  │
                 └──────┬──────┘
                        │
                        ▼
                ┌─────────────────┐
                │  Ingest Pipeline │
                │ (Python / LLM)   │
                └──────┬──────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼                              ▼
┌──────────────┐               ┌──────────────┐
│   Neo4j KG   │◄──────────────│  Embeddings  │
│ (Truth Core) │               │  / Similar   │
└──────┬───────┘               └──────────────┘
       │
       │ Graph API
       ▼
┌──────────────┐     双向轻同步     ┌──────────────┐
│   Obsidian   │◄────────────────►│    Notion     │
│ (Markdown)   │                   │ (Database)   │
└──────────────┘                   └──────────────┘
```

## 2. Neo4j：核心知识图谱层

### 2.1 唯一真实模型

Neo4j 不迁就前端工具的结构限制。推荐节点/关系示例：

**节点**
- `(:Bookmark)`
- `(:Concept)`
- `(:Topic)`
- `(:Note)`
- `(:Project)`
- `(:Person)`

**关系**
- `(:Bookmark)-[:MENTIONS]->(:Concept)`
- `(:Concept)-[:RELATED_TO]->(:Concept)`
- `(:Note)-[:REFINES]->(:Concept)`
- `(:Project)-[:USES]->(:Concept)`

### 2.2 保留 Obsidian / Notion 锚点

```
(:Note {
  obsidian_path: "concepts/transformer.md",
  notion_page_id: "abc-123"
})
```

这是三端联动的关键索引。

## 3. Obsidian：思考与概念演化层

### 3.1 定位

- 写：概念解释、个人理解、长期沉淀
- 链接：双链 ≈ 图谱局部投影
- Obsidian 是 Neo4j 的“人类可写接口”

### 3.2 Markdown 规范（建议）

```
---
type: concept
neo4j_id: Concept:Transformer
tags: [ai, nlp, attention]
---

# Transformer

## Definition
...

## Related Concepts
- [[Self-Attention]]
- [[Positional Encoding]]

## Open Questions
- ...
```

### 3.3 Obsidian → Neo4j 同步规则

| 事件 | 行为 |
| --- | --- |
| 新建概念笔记 | 创建 Concept 节点 |
| 新增双链 | 创建 RELATED_TO |
| 修改正文 | 更新摘要 / embedding |
| 删除笔记 | 标记 deprecated |

实现方式：Python watcher + Neo4j driver（或 Obsidian 插件）。

## 4. Notion：结构化与执行层

### 4.1 定位

Notion 仅保存：
- 项目
- 阅读状态
- 任务
- 进度与视图

### 4.2 数据库设计示例

**Bookmark Inbox**

| 字段 | 类型 |
| --- | --- |
| Title | Title |
| URL | URL |
| Topics | Relation |
| Status | Select |
| Neo4j ID | Text |
| Summary | Text |

**Project DB**

| 字段 | 类型 |
| --- | --- |
| Project | Title |
| Concepts | Relation |
| Notes | Relation |
| Status | Select |

### 4.3 Notion → Neo4j 同步逻辑

| Notion 行为 | Neo4j 行为 |
| --- | --- |
| 新任务 | 创建 Project |
| 关联概念 | 创建 USES |
| 状态变更 | 更新属性 |
| 删除 | soft delete |

实现方式：Notion Webhook + Python Sync Worker。

## 5. 三端协作的黄金路径

**场景：收藏一个新链接**

Chrome → Ingest → Neo4j  
                     │  
        ┌────────────┴────────────┐  
        ▼                         ▼  
   Notion Inbox             Obsidian Draft

**场景：写深度理解笔记**

Obsidian → Concept Refinement → Neo4j → Project View (Notion)

**场景：AI 查询**

“我最近半年读过的与向量数据库相关的内容，哪些已经形成概念？”  
Query → Neo4j Graph + Time Filter → Result

## 6. 冲突解决策略

| 冲突类型 | 策略 |
| --- | --- |
| Obsidian vs Neo4j | Obsidian 胜（内容源） |
| Notion vs Neo4j | Neo4j 胜（结构源） |
| Obsidian vs Notion | Neo4j 仲裁 |

## 7. 技术实现建议

### 7.1 同步服务结构

```
sync/
 ├── ingest/
 ├── obsidian_watcher/
 ├── notion_sync/
 ├── neo4j_client/
 └── embeddings/
```

### 7.2 技术栈

| 层 | 技术 |
| --- | --- |
| Sync | Python + FastAPI |
| Graph | Neo4j |
| Vector | FAISS / Milvus |
| LLM | GPT / Claude |
| Frontend | Obsidian / Notion |

## 8. 常见错误（避坑）

- ❌ 把 Notion 当知识库
- ❌ 试图三端完全同步
- ❌ 让 Obsidian 承担结构一致性
- ❌ 不设单一真相源

## 9. 最终形态

你最终会得到一个分层协作系统：

- **Neo4j**：外置大脑结构
- **Obsidian**：思考皮层
- **Notion**：执行与管理系统
