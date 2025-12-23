import queue
import threading
from typing import Optional
from .events import Event

class EventBus:
    """线程安全的优先级事件总线"""
    def __init__(self):
        # 使用 PriorityQueue，小的数字优先级高？不，Event dataclass 默认按字段顺序比较。
        # 我们在 Event 中把 priority 放在第一位。
        # 为了让高数字代表高优先级（符合直觉），我们需要反转，或者在 Event 定义时调整。
        # 为简单起见，这里约定：priority 数字越大，优先级越高。
        # 但 Python PriorityQueue 是最小堆（数字越小越先出）。
        # 所以存入时存 (-priority, event) 或者调整 Event 定义。
        # 为了代码清晰，我将在 put 时取反。
        self._queue = queue.PriorityQueue()
        self._stop_event = threading.Event()

    def put(self, event: Event):
        # 优先级取反，实现大数优先
        self._queue.put((-event.priority, event))

    def get(self, block: bool = True, timeout: Optional[float] = None) -> Optional[Event]:
        try:
            _, event = self._queue.get(block=block, timeout=timeout)
            return event
        except queue.Empty:
            return None

    def empty(self) -> bool:
        return self._queue.empty()
