class Memory:
    """海马体 (RAM Snapshot & Vector DB)"""
    def __init__(self):
        self.snapshots = []
        self.short_term_observations = [] # 存储最近的操作反馈（如文件读取结果）

    def save_snapshot(self, snapshot):
        self.snapshots.append(snapshot)
        # 保持内存精简
        if len(self.snapshots) > 100:
            self.snapshots.pop(0)

    def add_observation(self, observation: str):
        """添加一条观察记录 (FIFO)"""
        self.short_term_observations.append(observation)
        if len(self.short_term_observations) > 5:
            self.short_term_observations.pop(0)
    
    def get_recent_observations(self) -> list:
        return self.short_term_observations
