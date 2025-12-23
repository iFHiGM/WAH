from typing import List, Optional
from what.schema import ContextSnapshot
from system.config import Config
import time
import os

class Memory:
    """
     (Hippocampus)
    负责存储短期记忆 (Observations) 和 状态快照 (Snapshots)。
    """
    def __init__(self, capacity: int = 50):
        self.capacity = capacity
        self.snapshots: List[ContextSnapshot] = []
        self.short_term_observations: List[str] = [] 
        self.active_objective: Optional[str] = None
        self._load_objective()

    def _load_objective(self):
        """Load active objective from disk if exists."""
        if os.path.exists(Config.OBJECTIVE_FILE):
            try:
                with open(Config.OBJECTIVE_FILE, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        self.active_objective = content
            except Exception:
                pass

    def set_objective(self, objective: str):
        self.active_objective = objective
        try:
            with open(Config.OBJECTIVE_FILE, 'w', encoding='utf-8') as f:
                f.write(objective)
        except Exception:
            pass

    def clear_objective(self):
        self.active_objective = None
        if os.path.exists(Config.OBJECTIVE_FILE):
            try:
                os.remove(Config.OBJECTIVE_FILE)
            except Exception:
                pass

    def save_snapshot(self, snapshot: ContextSnapshot):
        """保存当前上下文快照"""
        self.snapshots.append(snapshot)
        # 保持 Snapshot 历史记录不要无限增长，保留最近 40 个
        if len(self.snapshots) > 40:
            self.snapshots.pop(0)

    def add_observation(self, observation: str):
        """
        察记录。
        执行 FIFO 裁剪，但保留足够多的上下文供 Brain 思考。
        """
        # 添加时间戳前缀，增加时序感
        timestamp = time.strftime("%H:%M:%S", time.localtime())
        entry = f"[{timestamp}] {observation}"
        
        self.short_term_observations.append(entry)
        
        # 自动裁剪 (Pruning)
        if len(self.short_term_observations) > self.capacity:
            # TODO: 未来发“记忆压缩” (Summarization)，将旧记忆压缩为摘要
            # 目前仅做简单的 FIFO 移除
            self.short_term_observations.pop(0)
    
    def get_recent_observations(self) -> List[str]:
        return self.short_term_observations

    def get_state_summary(self) -> str:
        """获取当前状态的文本摘要"""
        return f"Objective: {self.active_objective or 'None'}\nRecent Events: {len(self.short_term_observations)}"
