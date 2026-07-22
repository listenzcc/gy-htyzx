import time
import numpy as np
from scipy.interpolate import CubicSpline
import mne

# -----------------------
# 假设已有数据
# data.shape = (64, n_times)
# -----------------------
fs = 1000
n_channels = 64
n_times = int(3600 * fs)

# 示例数据（单位：Volt）


def gen_data(n_channels, n_times, seed=None):
    """
    Generate smooth EEG-like signals.

    Parameters
    ----------
    n_channels : int
    n_times : int
    seed : int | None

    Returns
    -------
    data : ndarray, shape (n_channels, n_times)
        Unit: Volt
    """
    rng = np.random.default_rng(seed)

    # 一个控制点对应100个采样点
    n_ctrl = n_times // 100 + 2

    x_ctrl = np.linspace(0, n_times - 1, n_ctrl)
    x = np.arange(n_times)

    data = np.empty((n_channels, n_times), dtype=np.float32)

    for ch in range(n_channels):
        y_ctrl = rng.normal(size=n_ctrl)

        spline = CubicSpline(x_ctrl, y_ctrl, bc_type="natural")
        y = spline(x)

        # 标准化
        y -= y.mean()
        y /= y.std()

        # EEG幅值（约20 µV）
        y *= 20e-6

        data[ch] = y

    return data


data = gen_data(n_channels, n_times, seed=int(time.time()*1000))

# -----------------------
# 使用标准1020中的64导名称
# -----------------------
montage = mne.channels.make_standard_montage("standard_1020")

# 从1020中取前64个电极
ch_names = montage.ch_names[:n_channels]

info = mne.create_info(
    ch_names=ch_names,
    sfreq=fs,
    ch_types="eeg"
)

raw = mne.io.RawArray(data, info)

raw.set_montage(montage)

# -----------------------
# 随机生成100个events
# event格式:
# [sample, 0, event_id]
# -----------------------
rng = np.random.default_rng(42)

event_samples = np.sort(
    rng.choice(
        np.arange(fs, n_times - fs),
        size=100,
        replace=False
    )
)

event_ids = rng.integers(1, 6, size=100)

events = np.column_stack([
    event_samples,
    np.zeros(100, dtype=int),
    event_ids
])

event_dict = {
    "Stim1": 1,
    "Stim2": 2,
    "Stim3": 3,
    "Stim4": 4,
    "Stim5": 5
}

annotations = mne.annotations_from_events(
    events,
    sfreq=raw.info["sfreq"],
    event_desc={v: k for k, v in event_dict.items()}
)
raw.set_annotations(annotations)
raw.save(f"test-1hr-{n_channels}-raw.fif", overwrite=True)
