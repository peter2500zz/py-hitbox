# 从 micropython 模块导入 const 函数,用于定义常量(提高性能和减少内存占用)
from micropython import const

# 导入 time 模块,用于延时操作
import time

# 导入 usb.device 模块,用于初始化 USB 设备
import usb.device

# 从 usb.device.hid 模块导入 HIDInterface 类,这是创建 HID 设备的基类
from usb.device.hid import HIDInterface

# 定义接口协议常量,0x00 表示没有特定的 HID 子协议
_INTERFACE_PROTOCOL_NONE = const(0x00)


def xbox360_gamepad_example():
    """Xbox 360 手柄示例主函数"""

    # 创建 Xbox360Interface 类的实例
    gamepad = Xbox360Interface()

    # 获取 USB 设备单例并初始化
    usb.device.get().init(gamepad, builtin_driver=True)

    # 等待 USB 连接建立
    while not gamepad.is_open():
        time.sleep_ms(100)

    print("Xbox 360 手柄已连接 (含扳机支持)!")

    # 主循环:不断演示各种手柄操作
    while True:
        # ===== 演示按钮操作 =====
        print("按下 A 键...")
        gamepad.press_button(1)
        time.sleep(0.5)
        gamepad.release_all()
        time.sleep(0.5)

        # ===== 演示摇杆操作 =====
        print("左摇杆动作...")
        gamepad.move_left_stick(127, 0)  # 向右
        time.sleep(0.5)
        gamepad.release_all()
        time.sleep(0.5)

        # ===== 演示扳机键 (Triggers) 操作 =====
        # 扳机键是模拟量，范围 0 (未按下) 到 255 (完全按下)

        # 1. 渐进按下左扳机 (LT)
        print("线性按下左扳机 (LT)...")
        for i in range(0, 256, 10):  # 从 0 到 255
            gamepad.move_triggers(left=i, right=0)
            time.sleep(0.02)

        time.sleep(0.5)  # 保持完全按下状态

        # 释放左扳机
        gamepad.move_triggers(left=0, right=0)
        time.sleep(0.5)

        # 2. 瞬间按下右扳机 (RT)
        print("按下右扳机 (RT)...")
        gamepad.move_triggers(left=0, right=255)  # 255 表示压满
        time.sleep(0.5)
        gamepad.move_triggers(left=0, right=0)  # 松开
        time.sleep(0.5)

        # 3. 组合动作：左摇杆推前 + 右扳机射击
        print("组合动作: 前进 + 射击...")
        # move_triggers 只更新扳机，不影响摇杆；set_state 可以同时更新所有
        # 这里演示分别调用保持状态
        gamepad.move_left_stick(0, 127)  # 向前
        time.sleep(0.2)
        gamepad.move_triggers(left=0, right=255)  # 开火
        time.sleep(0.5)
        gamepad.release_all()  # 全部复位

        time.sleep(2)
        print("重新开始...\n")


class Xbox360Interface(HIDInterface):
    """Xbox 360 游戏手柄 HID 接口类 (包含扳机支持)"""

    def __init__(self):
        super().__init__(
            _XBOX360_REPORT_DESC,
            set_report_buf=bytearray(0),
            protocol=_INTERFACE_PROTOCOL_NONE,
            interface_str="Xbox 360 Controller",
        )

        # 创建 8 字节的报告缓冲区 (原为 6 字节)
        # 字节 0-1: 按钮状态
        # 字节 2: 左摇杆 X
        # 字节 3: 左摇杆 Y
        # 字节 4: 右摇杆 X
        # 字节 5: 右摇杆 Y
        # 字节 6: 左扳机 (LT) - 新增 (0-255)
        # 字节 7: 右扳机 (RT) - 新增 (0-255)
        self.report = bytearray(8)

    def press_button(self, button_num):
        """按下指定的按钮"""
        if 1 <= button_num <= 10:
            byte_idx = (button_num - 1) // 8
            bit_idx = (button_num - 1) % 8
            self.report[byte_idx] |= 1 << bit_idx
            self.send_report(self.report)

    def release_button(self, button_num):
        """释放指定的按钮"""
        if 1 <= button_num <= 10:
            byte_idx = (button_num - 1) // 8
            bit_idx = (button_num - 1) % 8
            self.report[byte_idx] &= ~(1 << bit_idx)
            self.send_report(self.report)

    def release_all(self):
        """释放所有按钮、摇杆和扳机"""
        self.report = bytearray(8)  # 重置为 8 个 0
        self.send_report(self.report)

    def move_left_stick(self, x, y):
        """移动左摇杆"""
        self.report[2] = x & 0xFF
        self.report[3] = y & 0xFF
        self.send_report(self.report)

    def move_right_stick(self, x, y):
        """移动右摇杆"""
        self.report[4] = x & 0xFF
        self.report[5] = y & 0xFF
        self.send_report(self.report)

    def move_triggers(self, left, right):
        """移动/按压扳机键 (新增功能)

        参数:
            left: 左扳机 (LT) 力度, 范围 0-255
            right: 右扳机 (RT) 力度, 范围 0-255
        """
        # 将左扳机值存入字节 6
        self.report[6] = left & 0xFF
        # 将右扳机值存入字节 7
        self.report[7] = right & 0xFF

        self.send_report(self.report)

    def set_state(self, buttons=0, lx=0, ly=0, rx=0, ry=0, lt=0, rt=0):
        """一次性设置手柄的完整状态 (更新)

        参数新增:
            lt: 左扳机 (0-255)
            rt: 右扳机 (0-255)
        """
        self.report[0] = buttons & 0xFF
        self.report[1] = (buttons >> 8) & 0xFF
        self.report[2] = lx & 0xFF
        self.report[3] = ly & 0xFF
        self.report[4] = rx & 0xFF
        self.report[5] = ry & 0xFF
        # 新增扳机设置
        self.report[6] = lt & 0xFF
        self.report[7] = rt & 0xFF

        self.send_report(self.report)


# Xbox 360 控制器 HID 报告描述符 (更新版)
# 增加了 Z 轴 (LT) 和 Rz 轴 (RT)
# fmt: off
_XBOX360_REPORT_DESC = bytes((
    # ===== 定义设备类型 =====
    0x05, 0x01,        # Usage Page (Generic Desktop)
    0x09, 0x05,        # Usage (Game Pad)
    0xA1, 0x01,        # Collection (Application)
    
    # ===== 1. 按钮部分 (10 个按钮) =====
    0x05, 0x09,        #   Usage Page (Button)
    0x19, 0x01,        #   Usage Minimum (Button 1)
    0x29, 0x0A,        #   Usage Maximum (Button 10)
    0x15, 0x00,        #   Logical Minimum (0)
    0x25, 0x01,        #   Logical Maximum (1)
    0x75, 0x01,        #   Report Size (1)
    0x95, 0x0A,        #   Report Count (10)
    0x81, 0x02,        #   Input (Data,Var,Abs)
    
    # ===== 填充位 (6 位) =====
    0x75, 0x06,        #   Report Size (6)
    0x95, 0x01,        #   Report Count (1)
    0x81, 0x03,        #   Input (Const,Var,Abs)
    
    # ===== 2. 摇杆部分 (左 X/Y, 右 X/Y) =====
    # 范围 -127 到 127 (有符号)
    0x05, 0x01,        #   Usage Page (Generic Desktop)
    0x09, 0x30,        #   Usage (X)  - 左摇杆 X
    0x09, 0x31,        #   Usage (Y)  - 左摇杆 Y
    0x09, 0x33,        #   Usage (Rx) - 右摇杆 X
    0x09, 0x34,        #   Usage (Ry) - 右摇杆 Y
    0x15, 0x81,        #   Logical Minimum (-127)
    0x25, 0x7F,        #   Logical Maximum (127)
    0x75, 0x08,        #   Report Size (8)
    0x95, 0x04,        #   Report Count (4) - 4个轴
    0x81, 0x02,        #   Input (Data,Var,Abs)

    # ===== 3. 扳机部分 (LT/RT) - 新增 =====
    # 范围 0 到 255 (无符号)，对应 Z 轴和 Rz 轴
    0x05, 0x01,        #   Usage Page (Generic Desktop)
    0x09, 0x32,        #   Usage (Z)  - 映射为左扳机 (LT)
    0x09, 0x35,        #   Usage (Rz) - 映射为右扳机 (RT)
    0x15, 0x00,        #   Logical Minimum (0)
    0x26, 0xFF, 0x00,  #   Logical Maximum (255)
    0x75, 0x08,        #   Report Size (8)
    0x95, 0x02,        #   Report Count (2) - 2个轴
    0x81, 0x02,        #   Input (Data,Var,Abs)
    
    0xC0,              # End Collection
))
# fmt: on


if __name__ == "__main__":
    xbox360_gamepad_example()
