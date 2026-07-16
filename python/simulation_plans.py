# ----
class SimulationParameters:
    name: str

    # 经颅电刺激
    pulse_fs: float  # Hz
    strength: float  # mA
    e_duration: float  # min

    # 经颅光刺激
    power: float  # mW
    fs: float  # Hz
    l_duration: float  # min

    # 通道设置
    positive_chs: list[str]
    negative_chs: list[str]
