
class KeyState:
    Release = 0  # 稳定未按
    Press = 1  # 刚按下（第一帧）
    Pressing = 2  # 持续按下
    Releasing = 3  # 松开后的稳定态


class KeyMgr:
    def __init__(self) -> None:
        # id -> (last_pressing: bool, state: KeyState)
        self._keys: dict[str, tuple[bool, int]] = {}

    def update(self, id: str, pressing: bool) -> int:
        last_pressing, last_state = self._keys.get(id, (False, KeyState.Releasing))

        if pressing:
            if last_pressing:
                state = KeyState.Pressing
            else:
                state = KeyState.Press
        else:
            if last_pressing:
                state = KeyState.Release
            else:
                state = KeyState.Releasing

        self._keys[id] = (pressing, state)
        return state

    def state(self, id: str) -> int:
        return self._keys.get(id, (False, KeyState.Releasing))[1]
