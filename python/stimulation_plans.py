class SimulationParameters:
    """刺激参数类，按照协议规则设计"""

    def __init__(self):
        # 刺激方案选择 (对应协议第2个字段)
        # 可选值: '方案A', '方案B', '方案C'
        self.mode: str = '方案A'

        # 通道选择 (对应协议第3个字段)
        # 可选值: '通道1', '通道2', '双通道'
        self.channel: str = '通道1'

        # 光刺激参数 (对应协议第4-6个字段)
        self.light_wavelength: int = 810  # 可选值: 810, 1060
        self.light_frequency: int = 0     # 可选值: 0, 1, 10, 20, 30, 40, 50
        self.light_power: int = 0         # 可选值: 0, 30, 60, 90, 120, 150

        # 电刺激参数 (对应协议第7-8个字段)
        self.current_intensity: float = 0  # 可选值: 0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5
        self.elec_frequency: int = 0       # 可选值: 0, 1, 10, 20, 30, 40, 50

        # 治疗时间 (对应协议第9个字段)
        # 可选值: 20, 30, 40, 50, 60, 80
        self.stimulation_duration: int = 20

    def translate_into_bytes(self):
        """
        将参数转换为字节数组，按照协议格式：
        帧头(2字节) + 模式(2字节) + 通道(2字节) + 波长(2字节) + 
        光频率(2字节) + 光功率(2字节) + 电流(3字节) + 
        电频率(2字节) + 时长(1字节) + 帧尾(2字节)
        """
        frame = bytearray()

        # 1. 帧头: AA11
        frame.extend(bytes.fromhex('AA11'))

        # 2. 刺激方案选择 (2字节)
        mode_map = {
            '模式A': '000A',
            '模式B': '000B',
            '模式C': '000C'
        }
        frame.extend(bytes.fromhex(mode_map[self.mode]))

        # 3. 通道选择 (2字节)
        channel_map = {
            '通道1': 'FF01',
            '通道2': 'FF02',
            '双通道': 'FF03'
        }
        frame.extend(bytes.fromhex(channel_map[self.channel]))

        # 4. 光刺激波长 (2字节) - 格式: 0xxx
        wavelength_map = {
            810: '032A',   # 810 = 0x032A
            1060: '0424'   # 1060 = 0x0424
        }
        frame.extend(bytes.fromhex(
            wavelength_map.get(int(self.light_wavelength), '0000')))

        # 5. 光刺激频率 (2字节) - 格式: 00xx
        frame.extend(bytes.fromhex(f'{int(self.light_frequency):04X}'))

        # 6. 光刺激功率 (2字节) - 格式: 00xx
        frame.extend(bytes.fromhex(f'{int(self.light_power):04X}'))

        # 7. 电流强度 (3字节) - 格式: 0x0yyy (int+float)
        current_int = int(self.current_intensity)
        current_float = int((self.current_intensity % 1) * 1000)
        # 1.5mA -> 01 + 0500 = '010500'
        # 直接拼接十进制数字字符串，然后转十六进制
        # 1.5 -> '01' + '0500' = '010500'
        current_str = f'{current_int:02d}{current_float:04d}'
        frame.extend(bytes.fromhex(current_str))

        # 8. 电刺激频率 (2字节) - 格式: 00xx
        frame.extend(bytes.fromhex(f'{int(self.elec_frequency):04X}'))

        # 9. 治疗时间 (1字节) - 格式: xx
        frame.extend(bytes.fromhex(f'{int(self.stimulation_duration):02X}'))

        # 10. 帧尾: 11FF
        frame.extend(bytes.fromhex('11FF'))

        return frame

    def validate(self) -> tuple[bool, str]:
        """验证参数是否符合协议规则"""
        # 验证刺激方案
        if self.mode not in ['方案A', '方案B', '方案C']:
            return False, f"无效的刺激方案: {self.mode}，必须是 '方案A', '方案B' 或 '方案C'"

        # 验证通道
        if self.channel not in ['通道1', '通道2', '双通道']:
            return False, f"无效的通道: {self.channel}，必须是 '通道1', '通道2' 或 '双通道'"

        # 验证光刺激波长
        if self.light_wavelength not in [810, 1060]:
            return False, f"无效的光刺激波长: {self.light_wavelength}，必须是 810 或 1060"

        # 验证光刺激频率
        if self.light_frequency not in [0, 1, 10, 20, 30, 40, 50]:
            return False, f"无效的光刺激频率: {self.light_frequency}，必须是 0, 1, 10, 20, 30, 40 或 50"

        # 验证光刺激功率
        if self.light_power not in [0, 30, 60, 90, 120, 150]:
            return False, f"无效的光刺激功率: {self.light_power}，必须是 0, 30, 60, 90, 120 或 150"

        # 验证电流强度
        if self.current_intensity not in [0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5]:
            return False, f"无效的电流强度: {self.current_intensity}，必须是 0, 0.5, 1, 1.5, 2, 2.5, 3 或 3.5"

        # 验证电刺激频率
        if self.elec_frequency not in [0, 1, 10, 20, 30, 40, 50]:
            return False, f"无效的电刺激频率: {self.elec_frequency}，必须是 0, 1, 10, 20, 30, 40 或 50"

        # 验证治疗时间
        if self.stimulation_duration not in [20, 30, 40, 50, 60, 80]:
            return False, f"无效的治疗时间: {self.stimulation_duration}，必须是 20, 30, 40, 50, 60 或 80"

        return True, "参数验证通过"

    def __str__(self):
        """字符串表示"""
        return (f"SimulationParameters(\n"
                f"  模式={self.mode},\n"
                f"  通道={self.channel},\n"
                f"  光波长={self.light_wavelength}nm,\n"
                f"  光频率={self.light_frequency}Hz,\n"
                f"  光功率={self.light_power}mW,\n"
                f"  电流={self.current_intensity}mA,\n"
                f"  电频率={self.elec_frequency}Hz,\n"
                f"  持续时间={self.stimulation_duration}min\n"
                f")")


# 使用示例
if __name__ == '__main__':
    # 创建参数实例
    params = SimulationParameters()

    # 设置参数 (匹配示例)
    params.mode = '方案A'
    params.channel = '通道1'
    params.light_wavelength = 810
    params.light_frequency = 50
    params.light_power = 30
    params.current_intensity = 1.5
    params.elec_frequency = 20
    params.stimulation_duration = 40

    # 验证参数
    valid, msg = params.validate()
    if not valid:
        print(f"参数错误: {msg}")
    else:
        print("✓ 参数验证通过")
        print(params)

        # 生成字节帧
        frame = params.translate_into_bytes()
        generated_hex = frame.hex().upper()
        expected_hex = 'AA11000AFF01032A0032001E01050000142811FF'

        print(f"生成的帧: {generated_hex}")
        print(f"期望的帧: {expected_hex}")

        if generated_hex == expected_hex:
            print("✓ 帧格式正确！")
        else:
            print("✗ 帧格式错误！")
