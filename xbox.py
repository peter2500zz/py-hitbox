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

    # 创建 Xbox360Interface 类的实例,这个对象代表我们的虚拟游戏手柄
    gamepad = Xbox360Interface()

    # 获取 USB 设备单例并初始化
    # gamepad: 我们的 HID 接口对象
    # builtin_driver=True: 使用内置的 USB 驱动程序
    usb.device.get().init(gamepad, builtin_driver=True)

    # 等待 USB 连接建立
    # is_open() 返回 True 表示主机已识别并打开了这个 HID 设备
    while not gamepad.is_open():
        time.sleep_ms(100)  # 每 100 毫秒检查一次,避免 CPU 空转

    # 连接成功后打印提示信息
    print("Xbox 360 手柄已连接!")

    # 主循环:不断演示各种手柄操作
    while True:
        # ===== 演示按钮操作 =====

        # 按下 A 键(通常是按钮 1)
        print("按下 A 键 (按钮1)...")
        gamepad.press_button(1)  # 发送按钮 1 按下的报告
        time.sleep(0.5)  # 保持按下状态 0.5 秒
        gamepad.release_all()  # 释放所有按钮和摇杆,回到中立状态
        time.sleep(0.5)  # 等待 0.5 秒再进行下一个操作

        # 按下 B 键(通常是按钮 2)
        print("按下 B 键 (按钮2)...")
        gamepad.press_button(2)  # 发送按钮 2 按下的报告
        time.sleep(0.5)  # 保持按下状态 0.5 秒
        gamepad.release_all()  # 释放所有按钮
        time.sleep(0.5)  # 等待间隔

        # ===== 演示左摇杆操作 =====

        # 左摇杆向右移动(X 轴最大值 127,Y 轴中立位置 0)
        print("左摇杆向右...")
        gamepad.move_left_stick(127, 0)  # X=127(最右), Y=0(中间)
        time.sleep(0.5)  # 保持位置 0.5 秒
        gamepad.move_left_stick(0, 0)  # 回到中心位置 (0, 0)
        time.sleep(0.5)  # 等待间隔

        # 左摇杆向上移动(X 轴中立 0,Y 轴最大值 127)
        print("左摇杆向上...")
        gamepad.move_left_stick(0, 127)  # X=0(中间), Y=127(最上)
        time.sleep(0.5)  # 保持位置 0.5 秒
        gamepad.move_left_stick(0, 0)  # 回到中心位置
        time.sleep(0.5)  # 等待间隔

        # ===== 演示右摇杆画圆 =====

        print("右摇杆画圆...")
        # 通过改变角度让右摇杆沿圆形轨迹移动
        for angle in range(0, 360, 30):  # 从 0 度到 360 度,每次增加 30 度
            import math  # 导入数学模块用于三角函数计算

            # 用三角函数计算圆周上的坐标点
            # cos(角度) 计算 X 坐标,sin(角度) 计算 Y 坐标
            # 乘以 100 控制圆的半径大小
            x = int(100 * math.cos(math.radians(angle)))  # 转换为整数 X 坐标
            y = int(100 * math.sin(math.radians(angle)))  # 转换为整数 Y 坐标
            gamepad.move_right_stick(x, y)  # 移动右摇杆到计算出的位置
            time.sleep(0.1)  # 每个点停留 0.1 秒,形成平滑的圆周运动
        gamepad.move_right_stick(0, 0)  # 画圆结束后回到中心位置

        # 等待 2 秒后重新开始整个演示循环
        time.sleep(2)
        print("重新开始...\n")  # \n 换行,让输出更清晰


class Xbox360Interface(HIDInterface):
    """Xbox 360 游戏手柄 HID 接口类

    继承自 HIDInterface,实现了一个完整的 Xbox 360 手柄模拟器
    """

    def __init__(self):
        """初始化 Xbox 360 手柄接口"""

        # 调用父类 HIDInterface 的初始化方法
        super().__init__(
            _XBOX360_REPORT_DESC,  # 传入 Xbox 360 的 HID 报告描述符(定义在文件末尾)
            set_report_buf=bytearray(
                0
            ),  # 输出报告缓冲区大小为 0,因为手柄不接收来自主机的数据
            protocol=_INTERFACE_PROTOCOL_NONE,  # 协议类型为 None(通用 HID 设备)
            interface_str="Xbox 360 Controller",  # USB 设备显示的名称
        )

        # 创建 6 字节的报告缓冲区,用于存储手柄的当前状态
        # 字节 0-1: 按钮状态(10 个按钮,每个占 1 位)
        # 字节 2: 左摇杆 X 轴(-127 到 127)
        # 字节 3: 左摇杆 Y 轴(-127 到 127)
        # 字节 4: 右摇杆 X 轴(-127 到 127)
        # 字节 5: 右摇杆 Y 轴(-127 到 127)
        self.report = bytearray(6)

    def press_button(self, button_num):
        """按下指定的按钮

        参数:
            button_num: 按钮编号(1-10)
                       1=A, 2=B, 3=X, 4=Y, 5=LB, 6=RB, 7=Back, 8=Start, 9=LS, 10=RS
        """
        # 检查按钮编号是否在有效范围内
        if 1 <= button_num <= 10:
            # 计算按钮对应的字节索引
            # 按钮 1-8 在字节 0,按钮 9-10 在字节 1
            byte_idx = (button_num - 1) // 8  # 整除 8 得到字节索引(0 或 1)

            # 计算按钮在该字节中的位索引
            bit_idx = (button_num - 1) % 8  # 对 8 取余得到位索引(0-7)

            # 使用位或运算将对应位设置为 1(表示按钮被按下)
            # 1 << bit_idx 创建一个只有该位为 1 的掩码
            # |= 表示将该位设置为 1,不影响其他位
            self.report[byte_idx] |= 1 << bit_idx

            # 发送更新后的报告到主机
            self.send_report(self.report)

    def release_button(self, button_num):
        """释放指定的按钮

        参数:
            button_num: 按钮编号(1-10)
        """
        # 检查按钮编号是否有效
        if 1 <= button_num <= 10:
            # 计算字节索引和位索引(与 press_button 相同)
            byte_idx = (button_num - 1) // 8
            bit_idx = (button_num - 1) % 8

            # 使用位与运算将对应位设置为 0(表示按钮被释放)
            # ~(1 << bit_idx) 创建一个只有该位为 0,其他位为 1 的掩码
            # &= 表示将该位设置为 0,不影响其他位
            self.report[byte_idx] &= ~(1 << bit_idx)

            # 发送更新后的报告到主机
            self.send_report(self.report)

    def release_all(self):
        """释放所有按钮并将摇杆复位到中心位置"""

        # 创建一个新的全零字节数组,表示所有输入都处于初始状态
        # 所有按钮未按下(0),所有摇杆在中心位置(0)
        self.report = bytearray(6)

        # 发送重置后的报告
        self.send_report(self.report)

    def move_left_stick(self, x, y):
        """移动左摇杆到指定位置

        参数:
            x: X 轴坐标,范围 -127(最左) 到 127(最右),0 为中心
            y: Y 轴坐标,范围 -127(最下) 到 127(最上),0 为中心
        """
        # 将 X 坐标存入报告的第 3 个字节(索引 2)
        # & 0xFF 确保值在 0-255 范围内(处理负数的补码表示)
        self.report[2] = x & 0xFF

        # 将 Y 坐标存入报告的第 4 个字节(索引 3)
        self.report[3] = y & 0xFF

        # 发送更新后的报告
        self.send_report(self.report)

    def move_right_stick(self, x, y):
        """移动右摇杆到指定位置

        参数:
            x: X 轴坐标,范围 -127 到 127
            y: Y 轴坐标,范围 -127 到 127
        """
        # 将 X 坐标存入报告的第 5 个字节(索引 4)
        self.report[4] = x & 0xFF

        # 将 Y 坐标存入报告的第 6 个字节(索引 5)
        self.report[5] = y & 0xFF

        # 发送更新后的报告
        self.send_report(self.report)

    def set_state(self, buttons=0, lx=0, ly=0, rx=0, ry=0):
        """一次性设置手柄的完整状态

        这个方法允许同时设置所有输入,比分别调用多个方法更高效

        参数:
            buttons: 按钮状态,10 位整数(bit 0-9 对应按钮 1-10)
                    例如: 0b0000000011 表示按钮 1 和 2 被按下
            lx: 左摇杆 X 轴,范围 -127 到 127
            ly: 左摇杆 Y 轴,范围 -127 到 127
            rx: 右摇杆 X 轴,范围 -127 到 127
            ry: 右摇杆 Y 轴,范围 -127 到 127
        """
        # 设置按钮状态的低 8 位到字节 0
        self.report[0] = buttons & 0xFF

        # 设置按钮状态的高 2 位到字节 1
        # >> 8 将整数右移 8 位,取出高位部分
        self.report[1] = (buttons >> 8) & 0xFF

        # 设置左摇杆 X 轴(字节 2)
        self.report[2] = lx & 0xFF

        # 设置左摇杆 Y 轴(字节 3)
        self.report[3] = ly & 0xFF

        # 设置右摇杆 X 轴(字节 4)
        self.report[4] = rx & 0xFF

        # 设置右摇杆 Y 轴(字节 5)
        self.report[5] = ry & 0xFF

        # 发送完整的状态报告
        self.send_report(self.report)


# Xbox 360 控制器 HID 报告描述符
# 这是一个字节数组,用 HID 协议的语言告诉操作系统这个设备的功能和数据格式
# fmt: off 禁用代码格式化,保持原始排列便于阅读
_XBOX360_REPORT_DESC = bytes((
    # ===== 定义设备类型 =====
    0x05, 0x01,        # Usage Page (Generic Desktop) - 使用页:通用桌面控制
    0x09, 0x05,        # Usage (Game Pad) - 用途:游戏手柄
    0xA1, 0x01,        # Collection (Application) - 开始应用集合(所有输入的容器)
    
    # ===== 定义按钮部分 (10 个按钮) =====
    0x05, 0x09,        #   Usage Page (Button) - 使用页:按钮
    0x19, 0x01,        #   Usage Minimum (Button 1) - 最小用途:按钮 1
    0x29, 0x0A,        #   Usage Maximum (Button 10) - 最大用途:按钮 10(0x0A = 10)
    0x15, 0x00,        #   Logical Minimum (0) - 逻辑最小值:0(按钮未按下)
    0x25, 0x01,        #   Logical Maximum (1) - 逻辑最大值:1(按钮被按下)
    0x75, 0x01,        #   Report Size (1) - 报告大小:1 位(每个按钮占 1 位)
    0x95, 0x0A,        #   Report Count (10) - 报告数量:10 个(总共 10 位,对应 10 个按钮)
    0x81, 0x02,        #   Input (Data,Var,Abs) - 输入类型:数据,变量,绝对值
    
    # ===== 填充位(凑齐字节边界) =====
    # 前面 10 个按钮占用 10 位,需要 6 位填充才能凑成 2 个完整字节(16 位)
    0x75, 0x06,        #   Report Size (6) - 报告大小:6 位
    0x95, 0x01,        #   Report Count (1) - 报告数量:1 个(总共 6 位填充)
    0x81, 0x03,        #   Input (Const,Var,Abs) - 输入类型:常量(不变的填充位)
    
    # ===== 定义摇杆部分 (左 X, 左 Y, 右 X, 右 Y) =====
    0x05, 0x01,        #   Usage Page (Generic Desktop) - 使用页:通用桌面控制
    0x09, 0x30,        #   Usage (X) - 用途:X 轴(左摇杆 X)
    0x09, 0x31,        #   Usage (Y) - 用途:Y 轴(左摇杆 Y)
    0x09, 0x33,        #   Usage (Rx) - 用途:Rx 轴(右摇杆 X)
    0x09, 0x34,        #   Usage (Ry) - 用途:Ry 轴(右摇杆 Y)
    0x15, 0x81,        #   Logical Minimum (-127) - 逻辑最小值:-127(0x81 补码表示)
    0x25, 0x7F,        #   Logical Maximum (127) - 逻辑最大值:127(0x7F)
    0x75, 0x08,        #   Report Size (8) - 报告大小:8 位(1 个字节)
    0x95, 0x04,        #   Report Count (4) - 报告数量:4 个(4 个轴,每个 1 字节)
    0x81, 0x02,        #   Input (Data,Var,Abs) - 输入类型:数据,变量,绝对值
    
    0xC0,              # End Collection - 结束应用集合
))
# fmt: on 恢复代码格式化


# 运行示例程序
# 当这个文件被执行时,会自动调用主函数启动手柄模拟
if __name__ == "__main__":
    xbox360_gamepad_example()
