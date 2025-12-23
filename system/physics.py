from what.schema import Intent

class Physics:
    """物理引擎 (权限校验、安全边界)"""
    def check_intent(self, intent: Intent) -> bool:
        """
        验证意图是否符合当前的“物理规律”（安全规则）。
        目前阶段，我们允许所有内部反射。
        """
        # 禁止删除根目录等危险操作
        if intent.target_module == "shell" and "rm -rf /" in intent.params.get("command", ""):
            return False
        return True
