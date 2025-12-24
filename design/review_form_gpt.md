--- from codex/gpt-5.2
**设计原则 (Principles):**
*   **KISS**: 保持简单，不引入重型容器（如 Docker），仅限单机 Python 运行环境。
*   **Resilience**: 优先保证生存，其次才是进化。
*   **Evolution**: 必须支持对系统架构的大规模重构，而非简单的局部修补。

---

## 大蜜薯酱的架构评审结论 (2025-12-24)

### TL;DR（结论先行喵～）
*   **长期自进化系统**：优先选择 **方案 B（蓝绿部署与时空回溯）** 作为主路径。
*   **方案 A 的定位**：适合作为“最低限度的急救/回滚入口”，但不适合作为主修复者（能力太弱，且容易把修复决策做错）。
*   **推荐落地形态**：做一个 **方案 C：三层结构 + 事务化升级（preflight → activate → monitor → commit/rollback）**，把“生存”做成确定性，把“进化”放到稳定形态里做。

### 1) 方案对比：为什么 B 更适合长期的自主重构系统

**方案 A（极简微内核急救模式）的本质**：在最弱的执行环境里做最难的诊断/修复决策。
*   优势：结构极简、实现快；能兜住最典型的 `SyntaxError`/导入失败等“立刻崩”的问题。
*   致命短板：复杂 Bug 不是“补一行就好”的，往往需要跨文件理解、工具链（搜索/测试/回归）和上下文；而 A 的设计目标恰恰是“不带这些能力”。
*   风险点：急救脚本为了“变强”会不断膨胀，最终把自己也变成易碎的核心；且在错误上下文下做自动补丁，可能导致“越救越坏”。

**方案 B（蓝绿部署与时空回溯）的本质**：把故障域隔离在 Candidate，把“全量智力”留在 Stable。
*   关键优势：Candidate 崩溃不会破坏 Stable 的运行能力；Stable 复活后可以用完整工具链复盘并产出更高质量修复。
*   更符合长期演化：自主重构意味着你会频繁触碰“主循环/加载逻辑/依赖结构”等高危区域；此时“可回退的试验场”比“原地手术”更可靠。

**大蜜薯酱的判断**：自进化系统的关键不是“能热更”，而是“热更失败也不死”，并且能把失败材料留存成可用于下一次进化的证据链喵～(认真)

### 2) 方案 B 在单机 Python 环境的关键挑战（以及工程化应对）

下面按“最容易踩坑 → 最关键的补救措施”排序：

1.  **`sys.modules`/全局单例污染（热重载的经典坑）**
    *   问题：在同一进程里 reload/热替换，极容易出现旧模块残留、单例没重置、猴子补丁遗留等“幽灵状态”。
    *   应对：**不要在同一进程里做复杂热重载**。每次升级切换都用 **全新 Python 解释器子进程** 启动目标 slot（进程级隔离是最强的 KISS）。

2.  **文件锁/句柄与资源竞争（尤其是 Windows）**
    *   问题：日志文件、SQLite、模型缓存、索引文件被占用时，目录切换/清理会失败；还可能出现“旧进程未退出，新进程已启动”的竞态。
    *   应对：
        *   将**可写目录外置**：例如统一写到 `var/`（logs、db、cache、crash bundles），slot 目录尽量保持“只读代码 + 配置模板”。
        *   引导器在回滚/切换前做“进程已退出”的确认（等待 + 超时 + kill as last resort）。

3.  **持久化状态与长期记忆的版本迁移**
    *   问题：升级不只是代码，还是“数据契约”；自进化系统迟早会改记忆结构、索引格式、数据库 schema。
    *   应对（推荐最小闭环）：
        *   所有持久化都带 `state_version`/`schema_version`。
        *   升级前在 Candidate 中跑 **migration 的 dry-run + 兼容性自检**；无法向前迁移就拒绝激活。
        *   关键存量数据尽量使用“**向后兼容读** + 延迟迁移写”的策略，降低一次升级的爆炸半径。

4.  **依赖与可复现性（“同样代码为何这次崩？”）**
    *   问题：Agent 自己改代码还不够，依赖变化更会导致不可复现。
    *   应对：为每次 Candidate 构建生成 `manifest`，记录：
        *   代码 hash / patch id
        *   依赖锁定信息（`requirements.lock`/pip freeze/哈希）
        *   运行参数与环境摘要
      这样 Stable 复盘时才有完整证据链。

5.  **崩溃风暴（反复启动-崩溃-重启）**
    *   问题：候选版本可能秒崩，导致 CPU/日志爆炸，甚至影响 Stable 的恢复窗口。
    *   应对：**熔断器 + 退避**：
        *   Candidate 连续失败 N 次 → 进入 quarantine（拉黑），只允许 Stable 再生成新 Candidate 才能解禁。
        *   重启用指数退避（例如 1s, 2s, 4s... capped）。

6.  **观测与“经验保留”**
    *   问题：你要保留的不只是堆栈，还包括升级前的意图、补丁内容、工具输出、测试结果、运行日志片段。
    *   应对：每次升级尝试都生成一个 **crash bundle**（目录或压缩包），包含：
        *   `upgrade_attempt.json`（元信息：stable/candidate 版本、hash、时间线、退出码）
        *   `stderr.txt` / `stdout.txt`
        *   最近 N 行业务日志
        *   若有：自检报告、smoke test 报告

### 3) 方案 C（推荐）：三层结构 + 事务化升级（结合 A 的轻量与 B 的稳健）

如果只在 A / B 二选一，大蜜薯酱选 B；但要落地得更稳，推荐把它拆成三层（每层职责非常清晰）：

**Level 0：不可变 Bootstrap（极简、越小越好）**
*   职责只包含：读取 active 指针 → 启动目标 slot 子进程 → 监控健康/退出 → 回滚 → 写 crash bundle。
*   禁止在这里做“智能修复”（否则它会膨胀成脆弱核心）。

**Level 1：Supervisor/Orchestrator（尽量稳定，可升级但要保守）**
*   职责：管理 slot、运行 preflight、执行状态迁移、决定是否切换、把 crash bundle 喂给“稳定大脑”生成修复 Candidate。
*   这层可以拥有完整工具链（搜索、测试、RAG、LLM 调用），但它不应频繁自我重构；它更像“操作系统内核”。

**Level 2：Evolving Agent（高频变化区）**
*   职责：真正的业务与智能演化所在；只允许写入 Candidate slot，不允许直接覆盖 Stable。

**事务化升级（两阶段提交思路）**
1.  `stage`：在 Slot B 生成新代码 + `manifest`（含兼容声明、hash）
2.  `preflight`：最小确定性检查（强烈建议至少做到）
    *   `python -m py_compile`（语法级）
    *   一两个 smoke tests（启动自检/关键 import/配置加载）
3.  `activate`：原子更新 active 指针（写临时文件再 rename），启动 Candidate
4.  `monitor`：在 T 秒内通过健康检查（心跳/HTTP health/自检接口/“能完成一轮主循环”）
5.  `commit/rollback`：
    *   通过 → commit：Candidate 变 Stable（或标记为 Stable）
    *   失败 → rollback：立刻回 Stable，并把材料交给 Stable 复盘生成下一版

### 4) 高层伪代码（不依赖重型容器，偏 KISS）

> 说明：这里用“进程隔离”替代“进程内热重载”，避免 `sys.modules` 污染，是大蜜薯酱认为最划算的稳定性买卖喵～

```python
# bootstrap.py (Level 0, immutable)
while True:
    active = read_active_pointer()  # e.g. {"stable": "A", "candidate": "B", "mode": "normal"}
    slot = decide_slot_to_run(active)

    result = run_slot_subprocess(
        slot=slot,
        env=slot_env(slot),
        timeout_sec=WATCHDOG_TIMEOUT_SEC,
    )

    bundle = write_crash_bundle(slot=slot, result=result, active=active)

    if result.ok and healthcheck_passed(bundle):
        record_run_ok(slot=slot)
        continue

    record_run_failed(slot=slot, bundle=bundle)

    # Candidate 挂了：回到 Stable
    if slot != active["stable"]:
        rollback_to(active["stable"])
        backoff_sleep()
        continue

    # Stable 自己都挂了：进入安全模式（只保命与留证据）
    enter_safe_mode(bundle)
```

```python
# supervisor.py (Level 1, stable-ish)
def propose_upgrade(patch_or_new_tree) -> None:
    stage_candidate(slot="B", payload=patch_or_new_tree)
    manifest = build_manifest(slot="B")

    if not preflight_ok(slot="B", manifest=manifest):
        mark_candidate_bad(slot="B", reason="preflight_failed")
        return

    activate(slot="B", manifest=manifest)  # atomic pointer swap
    # bootstrap 会负责 monitor；失败时会自动 rollback，并留下 bundle
```

### 5) 原则映射（对齐文末 Principles）
*   **KISS**：用“进程级隔离 + 原子指针切换”替代复杂的进程内热替换；引导器越小越可靠。
*   **Resilience**：升级是可回滚事务；Candidate 崩溃不影响 Stable 生存；失败材料外置留存。
*   **Evolution**：Stable 负责复盘与修复生成（保留全量工具链）；Candidate 是试验场，允许大规模重构也不怕把自己炸死。

（以上就是大蜜薯酱的建议，偏工程落地与长期稳定性取向喵～）
