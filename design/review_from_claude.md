

\## 架构评审结论 (Review by 大蜜薯喵)



\### 1. 方案对比



\*\*大蜜薯酱的判断：方案 B 更适合长期自主重构系统喵～\*\*



| 维度 | 方案 A (微内核急救) | 方案 B (蓝绿部署) |

|------|---------------------|-------------------|

| 修复能力上限 | 低 (硬编码逻辑) | 高 (完整 Agent 智力) |

| 故障隔离性 | 差 (原地修改有污染风险) | 好 (版本目录物理隔离) |

| 复盘能力 | 弱 | 强 (可读取完整崩溃上下文) |

| 实现复杂度 | 低 | 中 |

| 长期可维护性 | 差 | 好 |



\*\*核心论点\*\*: 自进化系统的"修复"本质上是一个需要\*\*推理能力\*\*的任务，而非简单的模式匹配。方案 A 的"急救医生"天生残疾——它没有上下文、没有工具链、没有记忆，只能做最浅层的语法修复。而方案 B 让"最强形态的旧版本"来担任修复者，这符合"用强者修复弱者失败"的工程直觉喵。



---



\### 2. 方案 B 在单机 Python 环境下的潜在风险



\*\*(这部分很重要喵，Python 的动态特性是双刃剑呢)\*\*



\#### 2.1 `sys.modules` 缓存污染

\- \*\*问题\*\*: Python 模块一旦 `import` 就会被缓存在 `sys.modules`。如果 Slot A 和 Slot B 有同名模块但不同实现，简单的 `import` 会拿到旧缓存。

\- \*\*缓解\*\*: 使用 `subprocess` 启动全新进程而非 `os.execv`；或使用 `importlib.reload()` + 手动清理 `sys.modules`（但这很脆弱）。



\#### 2.2 文件锁与资源句柄

\- \*\*问题\*\*: 如果 Slot B 崩溃时持有文件锁、数据库连接、socket 等资源，可能导致 Slot A 重启后无法获取这些资源。

\- \*\*缓解\*\*:

&nbsp; - 使用 `with` 语句确保资源释放

&nbsp; - 文件锁使用超时机制 (`fcntl.flock` with timeout)

&nbsp; - 数据库连接使用连接池 + 心跳检测



\#### 2.3 持久化数据的版本迁徙 (Schema Migration)

\- \*\*问题\*\*: v2 可能修改了数据库结构或配置文件格式，v2 崩溃后 v1 回滚时可能无法读取被 v2 修改过的数据。

\- \*\*缓解\*\*:

&nbsp; - 持久化层使用\*\*向前兼容\*\*的序列化格式（如 Protocol Buffers, MessagePack）

&nbsp; - 数据库变更使用可逆的 migration 脚本

&nbsp; - 敏感数据写入前先备份



\#### 2.4 全局状态与单例污染

\- \*\*问题\*\*: Python 中大量使用全局变量和单例模式，进程级切换可能导致状态不一致。

\- \*\*缓解\*\*: 尽量使用\*\*进程隔离\*\*而非目录切换；状态持久化到外部存储。



---



\### 3. 方案 C: 分层容错 + 进程隔离 (Layered Fault Tolerance)



\*\*大蜜薯酱提出一个结合 A 的轻量与 B 的稳健的混合方案喵～\*\*



```

┌─────────────────────────────────────────────────────────┐

│  Level 0: Watchdog (绝对不可变, 100行以内)              │

│  - 纯 Python 标准库, 无任何项目依赖                      │

│  - 职责: 监控子进程存活, 记录崩溃日志, 触发回滚/重试     │

│  - 不做任何修复逻辑! (这是关键区别)                      │

└─────────────────────────────────────────────────────────┘

&nbsp;                          │

&nbsp;                          │ subprocess.Popen()

&nbsp;                          ▼

┌─────────────────────────────────────────────────────────┐

│  Level 1: Version Router (版本路由器)                   │

│  - 管理 Slot A (stable) / Slot B (candidate) 的切换     │

│  - 实现健康检查 (heartbeat / readiness probe)           │

│  - 崩溃时: 写入 crash\_context.json → 重启 Slot A        │

└─────────────────────────────────────────────────────────┘

&nbsp;                          │

&nbsp;                          │ 进程间通信 (Unix Socket / Named Pipe)

&nbsp;                          ▼

┌─────────────────────────────────────────────────────────┐

│  Level 2: Agent Core (完整的自进化 Agent)               │

│  - 拥有完整的 LLM 调用、RAG、工具链能力                  │

│  - 启动时检查 crash\_context.json 是否存在               │

│  - 若存在: 进入"修复模式", 分析上次崩溃并生成 v\_new      │

│  - 修复完成后: 通知 Level 1 尝试切换到新版本             │

└─────────────────────────────────────────────────────────┘

```



\*\*借鉴的工业界模式\*\*:

\- \*\*Erlang OTP Supervisor\*\*: "Let it crash" 哲学 + 监督树自动重启

\- \*\*Kubernetes Pod\*\*: Liveness/Readiness Probe + 滚动更新

\- \*\*Chromium 双分区\*\*: A/B System Update (Android 也用这个)

\- \*\*systemd\*\*: 服务依赖管理 + 自动重启策略



---



\### 4. 最终建议：高层伪代码



```python

\# === Level 0: watchdog.py (绝对不可变) ===

import subprocess, json, time, sys

from pathlib import Path



STABLE\_SLOT = Path("./slots/stable")

CANDIDATE\_SLOT = Path("./slots/candidate")

CRASH\_LOG = Path("./crash\_context.json")

MAX\_CANDIDATE\_FAILURES = 3



def run\_agent(slot: Path) -> tuple\[int, str]:

&nbsp;   """启动 Agent 进程, 返回 (exit\_code, stderr)"""

&nbsp;   proc = subprocess.Popen(

&nbsp;       \[sys.executable, slot / "main.py"],

&nbsp;       stderr=subprocess.PIPE,

&nbsp;       cwd=slot

&nbsp;   )

&nbsp;   \_, stderr = proc.communicate()

&nbsp;   return proc.returncode, stderr.decode()



def main():

&nbsp;   candidate\_failures = 0

&nbsp;   current\_slot = STABLE\_SLOT



&nbsp;   while True:

&nbsp;       exit\_code, stderr = run\_agent(current\_slot)



&nbsp;       if exit\_code == 0:  # 正常退出 (主动升级)

&nbsp;           if (CANDIDATE\_SLOT / "main.py").exists():

&nbsp;               current\_slot = CANDIDATE\_SLOT

&nbsp;               candidate\_failures = 0

&nbsp;           continue



&nbsp;       # 崩溃处理

&nbsp;       crash\_context = {

&nbsp;           "slot": str(current\_slot),

&nbsp;           "exit\_code": exit\_code,

&nbsp;           "stderr": stderr\[-10000:],  # 截断防止过大

&nbsp;           "timestamp": time.time()

&nbsp;       }

&nbsp;       CRASH\_LOG.write\_text(json.dumps(crash\_context, indent=2))



&nbsp;       if current\_slot == CANDIDATE\_SLOT:

&nbsp;           candidate\_failures += 1

&nbsp;           if candidate\_failures >= MAX\_CANDIDATE\_FAILURES:

&nbsp;               # 候选版连续失败, 回滚到稳定版

&nbsp;               current\_slot = STABLE\_SLOT

&nbsp;               candidate\_failures = 0



&nbsp;       time.sleep(1)  # 防止崩溃风暴



\# === Level 2: Agent 启动时的修复模式检测 ===

\# (在 Agent 的 main.py 中)



def on\_startup():

&nbsp;   crash\_log = Path("../crash\_context.json")

&nbsp;   if crash\_log.exists():

&nbsp;       context = json.loads(crash\_log.read\_text())

&nbsp;       # 进入修复模式: 用完整的 LLM + 工具链分析崩溃

&nbsp;       analysis = llm.analyze\_crash(

&nbsp;           stderr=context\["stderr"],

&nbsp;           failed\_slot=context\["slot"],

&nbsp;           codebase=read\_codebase(context\["slot"])

&nbsp;       )

&nbsp;       fix\_patch = llm.generate\_fix(analysis)

&nbsp;       apply\_patch\_to\_candidate(fix\_patch)

&nbsp;       crash\_log.unlink()  # 清理, 防止重复修复

```



---



\### 5. 总结



| 建议 | 说明 |

|------|------|

| \*\*采用方案 B 为基础\*\* | 蓝绿部署的版本隔离是正确的方向 |

| \*\*Level 0 绝对精简\*\* | 守护进程不做修复，只做监控和切换 |

| \*\*进程隔离优于目录切换\*\* | 使用 `subprocess` 而非 `os.execv` |

| \*\*崩溃上下文结构化\*\* | 使用 JSON 记录完整的崩溃信息供后续分析 |

| \*\*设置失败阈值\*\* | 候选版连续崩溃 N 次后强制回滚 |

| \*\*持久化层向前兼容\*\* | 使用 Protocol Buffers 等版本兼容的序列化格式 |



##### \*\*大蜜薯酱的核心观点\*\*: 自进化系统的"不死"机制，本质是\*\*分层解耦\*\* + \*\*最小信任原则\*\*。Level 0 只信任自己；Level 1 只信任 Level 0；Level 2 的新版本谁都不信任，必须先证明自己。这种"不信任驱动"的架构才是真正稳健的喵～ (๑•̀ㅂ•́)و✧

##### 

##### ---



