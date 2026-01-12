# 从 micropython 模块导入 const 函数,用于定义常量
from micropython import const
import time
import usb.device
from usb.device.hid import HIDInterface
import math

_INTERFACE_PROTOCOL_NONE = const(0x00)

class KeyCode:
    A = const(1)
    B = const(2)
    X = const(3)
    Y = const(4)

    LB = const(5)
    RB = const(6)

    LT = const(7)
    RT = const(8)

    BACK = const(9)
    START = const(10)

    LS = const(11)
    RS = const(12)

    UP = const(13)
    DOWN = const(14)
    LEFT = const(15)
    RIGHT = const(16)

def gamepad_demo():
    """通用游戏手柄示例主函数"""

    # 实例化新的手柄接口
    gamepad = Xbox360Interface()

    # 初始化 USB
    usb.device.get().init(gamepad, builtin_driver=True)

    # 等待连接
    while not gamepad.is_open():
        time.sleep_ms(100)

    print("游戏手柄已连接! (Report ID: 4)")

    while True:
        # ===== 1. 演示按钮 (支持 1-16) =====

        # 按下按钮 1 (通常是 A 键或扳机)
        print("按下按钮 1...")
        gamepad.press_button(1)
        time.sleep(0.5)
        gamepad.release_all()
        time.sleep(0.2)

        # 按下按钮 16 (最大按钮编号)
        print("按下按钮 16...")
        gamepad.press_button(16)
        time.sleep(0.5)
        gamepad.release_all()
        time.sleep(0.2)

        # 同时按下按钮 1, 2, 3, 4
        print("同时按下按钮 1-4...")
        # 0x0F = 二进制 00001111 (表示前4个按钮)
        gamepad.set_state(buttons=0x0F)
        time.sleep(0.5)
        gamepad.release_all()
        time.sleep(0.5)

        # ===== 2. 演示左摇杆 (X, Y 轴) =====
        print("移动左摇杆 (X/Y 轴)...")
        # 向左上
        gamepad.move_left_stick(-127, -127)
        time.sleep(0.5)
        # 向右下
        gamepad.move_left_stick(127, 127)
        time.sleep(0.5)
        gamepad.release_all()
        time.sleep(0.5)

        # ===== 3. 演示右摇杆 (Z, Rz 轴) - 画圆 =====
        print("右摇杆 (Z/Rz 轴) 画圆...")
        for angle in range(0, 360, 20):
            # 半径设为 127 (最大值)
            z = int(127 * math.cos(math.radians(angle)))
            rz = int(127 * math.sin(math.radians(angle)))

            # 更新 Z, Rz 轴
            gamepad.move_right_stick(z, rz)
            time.sleep(0.05)

        gamepad.release_all()

        print("演示循环重新开始...\n")
        time.sleep(1)


class Xbox360Interface(HIDInterface):
    """基于自定义描述符的游戏手柄接口类"""

    def __init__(self):
        super().__init__(
            _GAMEPAD_REPORT_DESC,
            set_report_buf=bytearray(0),
            protocol=_INTERFACE_PROTOCOL_NONE,
            interface_str="Generic Gamepad",
        )

        # 初始化报告缓冲区
        # 大小计算:
        # 1 字节 (Report ID)
        # 2 字节 (16个按钮, 16 bits)
        # 4 字节 (X, Y, Z, Rz 四个轴, 每个8 bits)
        # 总计: 7 字节
        self.report = bytearray(7)

        # **重要**: 根据描述符 0x85 0x04，报告的第一个字节必须是 ID 4
        self.report[0] = 0x04

    def press_button(self, button_num):
        """按下指定按钮 (1-16)"""
        if 1 <= button_num <= 16:
            # 按钮数据从缓冲区的索引 1 开始 (索引 0 是 Report ID)
            # 按钮 1-8 在索引 1，按钮 9-16 在索引 2
            byte_offset = (button_num - 1) // 8
            bit_offset = (button_num - 1) % 8

            # 注意：self.report[1 + ...] 因为第0位是ID
            self.report[1 + byte_offset] |= 1 << bit_offset
            self.send_report(self.report)

    def release_button(self, button_num):
        """释放指定按钮 (1-16)"""
        if 1 <= button_num <= 16:
            byte_offset = (button_num - 1) // 8
            bit_offset = (button_num - 1) % 8

            self.report[1 + byte_offset] &= ~(1 << bit_offset)
            self.send_report(self.report)

    def release_all(self):
        """重置所有状态"""
        # 保留 Report ID (索引0)，清除其他所有数据
        for i in range(1, 7):
            self.report[i] = 0
        self.send_report(self.report)

    def move_left_stick(self, x, y):
        """移动左摇杆 (对应描述符中的 X, Y)
        范围: -127 到 127
        """
        # 限制范围
        x = max(-127, min(127, x))
        y = max(-127, min(127, y))

        # X 在索引 3
        self.report[3] = x & 0xFF
        # Y 在索引 4
        self.report[4] = y & 0xFF

        self.send_report(self.report)

    def move_right_stick(self, z, rz):
        """移动右摇杆 (对应描述符中的 Z, Rz)
        范围: -127 到 127
        """
        # 限制范围
        z = max(-127, min(127, z))
        rz = max(-127, min(127, rz))

        # Z 在索引 5
        self.report[5] = z & 0xFF
        # Rz 在索引 6
        self.report[6] = rz & 0xFF

        self.send_report(self.report)

    def set_state(self, buttons=0, x=0, y=0, z=0, rz=0):
        """一次性设置所有状态"""
        # 设置按钮 (16位整数拆分为2个字节)
        self.report[1] = buttons & 0xFF  # 按钮 1-8
        self.report[2] = (buttons >> 8) & 0xFF  # 按钮 9-16

        # 设置轴
        self.report[3] = x & 0xFF
        self.report[4] = y & 0xFF
        self.report[5] = z & 0xFF
        self.report[6] = rz & 0xFF

        self.send_report(self.report)


# 您提供的报告描述符
_GAMEPAD_REPORT_DESC = bytes((
    0x05, 0x01,        # Usage Page (Generic Desktop)
    0x09, 0x05,        # Usage (Game Pad)
    0xA1, 0x01,        # Collection (Application)
    0x85, 0x04,        #   Report ID (4)  <-- 关键：这决定了数据包的第一个字节必须是 4
    0x05, 0x09,        #   Usage Page (Button)
    0x19, 0x01,        #   Usage Minimum (Button 1)
    0x29, 0x10,        #   Usage Maximum (Button 16)
    0x15, 0x00,        #   Logical Minimum (0)
    0x25, 0x01,        #   Logical Maximum (1)
    0x75, 0x01,        #   Report Size (1)
    0x95, 0x10,        #   Report Count (16) -> 2 bytes
    0x81, 0x02,        #   Input (Data,Var,Abs)
    0x05, 0x01,        #   Usage Page (Generic Desktop)
    0x15, 0x81,        #   Logical Minimum (-127)
    0x25, 0x7F,        #   Logical Maximum (127)
    0x09, 0x30,        #   Usage (X)
    0x09, 0x31,        #   Usage (Y)
    0x09, 0x32,        #   Usage (Z)
    0x09, 0x35,        #   Usage (Rz)
    0x75, 0x08,        #   Report Size (8)
    0x95, 0x04,        #   Report Count (4) -> 4 bytes
    0x81, 0x02,        #   Input (Data,Var,Abs)
    0xC0               # End Collection
))

if __name__ == "__main__":
    gamepad_demo()
