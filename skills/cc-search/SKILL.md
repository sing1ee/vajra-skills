---
name: cc-search
description: >
  搜索当前 Claude Code 项目的历史对话记录。使用 ripgrep 在 ~/.claude/projects/ 的 JSONL 文件中全文检索，
  展示匹配的会话信息（标题、时间、消息摘要、匹配上下文），并提供 resume 命令。
  触发词：搜索历史、search history、cc-search、找对话、查对话
user_invocable: true
---

# cc-search — Claude Code 对话历史搜索

搜索当前项目（或所有项目）的 Claude Code 对话历史，快速找到之前的会话。

## 使用方法

```
/cc-search <搜索词> [搜索词2 ...]
/cc-search authentication
/cc-search deploy docker
/cc-search -p myproject pricing
```

用户提供一个或多个搜索词（AND 逻辑，所有词必须同时出现在同一会话中）。

### 参数解析

从用户输入中提取：
- **搜索词**：所有非 flag 参数，作为搜索关键词
- **`-p <project>`**：可选，按项目名过滤（子串匹配）
- **`-n <number>`**：可选，最大显示结果数，默认 20
- **`-c <number>`**：可选，每个会话显示的匹配行数，默认 3
- **`--agents`**：可选，包含 agent 子会话（默认排除）

---

## 执行流程

### Step 1: 确定搜索目录

Claude Code 的对话数据存储在 `~/.claude/projects/` 下，每个项目一个子目录，目录名是工作路径用 `-` 连接（如 `-Users-cheng-code-myapp`）。

**当前项目目录**：根据当前工作目录（CWD）推算对应的项目目录名。将 CWD 的路径分隔符替换为 `-`，加上前缀 `-`。例如 CWD 为 `/Users/cheng/code/myapp`，则项目目录名为 `-Users-cheng-code-myapp`。

搜索范围规则（**严格按此顺序判断**）：
1. 如果用户指定了 `-p <project>`，在 `~/.claude/projects/` 下按子串匹配目录名
2. 如果用户明确说"搜索所有项目"、"全局搜索"、"all projects"，则搜索整个 `~/.claude/projects/` 目录
3. **否则，默认只搜索当前项目对应的目录**（即 `~/.claude/projects/<当前项目目录名>/`）

### Step 2: 用 ripgrep 查找匹配文件

使用 Bash 工具执行 ripgrep 命令查找包含所有搜索词的 JSONL 文件：

```bash
# 第一个搜索词找到候选文件
rg --files-with-matches --no-messages -i --glob '*.jsonl' '<term1>' <search_dir>

# 如果有多个搜索词，在候选文件中逐步过滤
# 将上一步结果作为输入，用下一个搜索词过滤
rg --files-with-matches --no-messages -i '<term2>' <file1> <file2> ...
```

**过滤规则**：
- 默认排除 `agent-*.jsonl` 文件（除非用户指定 `--agents`）
- 使用 `-i` 进行大小写不敏感搜索

### Step 3: 提取会话元数据

对每个匹配的 JSONL 文件，使用 ripgrep + 简单的 bash 命令提取关键信息：

```bash
# 获取会话标题（custom-title 类型的条目）
rg '"type":"custom-title"' <file> --no-line-number | tail -1

# 获取第一条和最后一条时间戳
rg '"timestamp"' <file> --no-line-number | head -1
rg '"timestamp"' <file> --no-line-number | tail -1

# 获取 cwd
rg '"cwd"' <file> --no-line-number | head -1

# 统计消息数
rg -c '"role":"user"' <file>
rg -c '"role":"assistant"' <file>

# 检测是否被 compacted
rg -c 'continued from a previous conversation' <file>

# 获取匹配的上下文行（用户和助手消息中的匹配）
rg -i '<term>' <file> --no-line-number | head -<context_lines>
```

**注意**：上面的命令是逻辑说明，实际执行时应合并为尽量少的 Bash 调用以提高效率。可以用一个 bash 脚本或管道组合来一次性提取所有信息。

### Step 4: 高效批量提取（推荐方式）

为了减少 Bash 调用次数，对匹配到的文件用一个 bash 脚本批量处理：

```bash
for f in <matched_files>; do
  session_id=$(basename "$f" .jsonl)
  
  # 标题
  title=$(rg --no-line-number '"type":"custom-title"' "$f" 2>/dev/null | tail -1 | sed 's/.*"customTitle":"\([^"]*\)".*/\1/' || echo "(no title)")
  
  # CWD
  cwd=$(rg --no-line-number '"cwd"' "$f" 2>/dev/null | head -1 | sed 's/.*"cwd":"\([^"]*\)".*/\1/' || echo "")
  
  # 时间范围
  first_ts=$(rg --no-line-number '"timestamp"' "$f" 2>/dev/null | head -1 | sed 's/.*"timestamp":"\([^"]*\)".*/\1/')
  last_ts=$(rg --no-line-number '"timestamp"' "$f" 2>/dev/null | tail -1 | sed 's/.*"timestamp":"\([^"]*\)".*/\1/')
  
  # 消息统计
  user_count=$(rg -c '"role":"user"' "$f" 2>/dev/null || echo 0)
  asst_count=$(rg -c '"role":"assistant"' "$f" 2>/dev/null || echo 0)
  
  # Compaction
  compact=$(rg -c 'continued from a previous conversation' "$f" 2>/dev/null || echo 0)
  
  # 输出分隔格式
  echo "===SESSION==="
  echo "FILE:$f"
  echo "ID:$session_id"
  echo "TITLE:$title"
  echo "CWD:$cwd"
  echo "FIRST_TS:$first_ts"
  echo "LAST_TS:$last_ts"
  echo "USER_MSGS:$user_count"
  echo "ASST_MSGS:$asst_count"
  echo "COMPACTED:$compact"
done
```

对于匹配上下文，单独获取：

```bash
# 获取匹配行中的用户/助手消息文本
rg -i '<term>' <file> --no-line-number | rg '"role":"(user|assistant)"' | head -<n>
```

### Step 5: 格式化输出

将提取的信息格式化为可读的结果卡片，按最后时间戳倒序（最近的在前）。

每个会话显示为：

```
────────────────────────────────────────────────────────────────────────────────
#1  会话标题
  项目名  session-uuid
  /path/to/working/directory
  from 2026-03-08 11:30 to 2026-03-21 01:07  (12d 13h)
  177 user / 246 assistant msgs | COMPACTED (2x) 或 not compacted
  MATCHES:
    [user] ...匹配关键词周围的上下文...
    [asst] ...助手消息中的匹配...
  RESUME: cd /path/to/cwd && claude --resume session-uuid
────────────────────────────────────────────────────────────────────────────────
```

**项目名美化**：将目录名中的 home 路径前缀去掉，例如 `-Users-cheng-Downloads-Projects-myapp` 显示为 `Downloads-Projects-myapp` 或更短的形式。

**匹配上下文**：从匹配行的 JSON 中提取 `message.content` 的文本部分，截取关键词前后约 75 个字符作为上下文片段。标注消息角色 `[user]` 或 `[asst]`。

### Step 6: 显示汇总

在所有结果之后显示汇总：

```
>> 显示 20/47 个结果 (用 -n 显示更多)
>> 47 sessions, 10 compacted, 15182 total messages
```

---

## 执行原则

1. **速度优先**：使用 ripgrep 而非逐行读取，尽量减少 Bash 调用次数
2. **批量处理**：将多个文件的元数据提取合并到一个 bash 脚本中执行
3. **智能过滤**：自动过滤 agent 会话、系统消息、task-notification 等噪音
4. **默认当前项目**：没有指定项目时只搜索当前项目，避免全局搜索耗时过长
5. **实用输出**：每个结果提供可直接复制粘贴的 `claude --resume` 命令
6. **匹配上下文中提取可读文本**：从 JSONL 的 JSON 结构中提取人类可读的消息文本，而不是显示原始 JSON
