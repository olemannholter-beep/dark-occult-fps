import math
import os
import random
import struct
import wave
import numpy as np

try:
    import scipy.signal as _scipy_signal
    HAS_SCIPY: bool = True
except ImportError:
    _scipy_signal = None
    HAS_SCIPY = False

SAMPLE_RATE: int = 44100


def _dsp_lowpass(x: np.ndarray, cutoff_hz: float, order: int = 2) -> np.ndarray:
    if len(x) == 0:
        return x
    nyq: float = 0.5 * SAMPLE_RATE
    fc: float = float(np.clip(cutoff_hz, 20.0, nyq * 0.96))
    if HAS_SCIPY and _scipy_signal is not None:
        sos = _scipy_signal.butter(order, fc / nyq, btype="low", output="sos")
        return _scipy_signal.sosfilt(sos, x).astype(np.float64)
    freqs = np.fft.rfftfreq(len(x), d=1.0 / SAMPLE_RATE)
    h = 1.0 / np.sqrt(1.0 + (freqs / fc) ** (2.0 * order))
    phase = -np.arctan2(freqs, fc) * order
    transfer = h * np.exp(1j * phase)
    return np.fft.irfft(np.fft.rfft(x) * transfer, n=len(x)).astype(np.float64)


def _dsp_highpass(x: np.ndarray, cutoff_hz: float, order: int = 2) -> np.ndarray:
    if len(x) == 0:
        return x
    nyq: float = 0.5 * SAMPLE_RATE
    fc: float = float(np.clip(cutoff_hz, 20.0, nyq * 0.96))
    if HAS_SCIPY and _scipy_signal is not None:
        sos = _scipy_signal.butter(order, fc / nyq, btype="high", output="sos")
        return _scipy_signal.sosfilt(sos, x).astype(np.float64)
    freqs = np.fft.rfftfreq(len(x), d=1.0 / SAMPLE_RATE)
    safe_f = np.maximum(freqs, 1e-3)
    h = 1.0 / np.sqrt(1.0 + (fc / safe_f) ** (2.0 * order))
    h[0] = 0.0
    phase = np.arctan2(fc, safe_f) * order
    transfer = h * np.exp(1j * phase)
    return np.fft.irfft(np.fft.rfft(x) * transfer, n=len(x)).astype(np.float64)


def _dsp_bandpass(x: np.ndarray, low_hz: float, high_hz: float, order: int = 2) -> np.ndarray:
    if len(x) == 0:
        return x
    nyq: float = 0.5 * SAMPLE_RATE
    lo: float = float(np.clip(low_hz, 20.0, nyq * 0.92))
    hi: float = float(np.clip(max(high_hz, lo + 25.0), lo + 25.0, nyq * 0.96))
    if HAS_SCIPY and _scipy_signal is not None:
        sos = _scipy_signal.butter(order, [lo / nyq, hi / nyq], btype="band", output="sos")
        return _scipy_signal.sosfilt(sos, x).astype(np.float64)
    return _dsp_lowpass(_dsp_highpass(x, lo, order=order), hi, order=order)


def _dsp_fftconvolve(x: np.ndarray, h: np.ndarray) -> np.ndarray:
    if len(x) == 0 or len(h) == 0:
        return np.zeros(max(len(x), 1), dtype=np.float64)
    if HAS_SCIPY and _scipy_signal is not None:
        return _scipy_signal.fftconvolve(x, h, mode="full")[: len(x)].astype(np.float64)
    n_conv: int = len(x) + len(h) - 1
    n_fft: int = 1 << (n_conv - 1).bit_length()
    X = np.fft.rfft(x, n=n_fft)
    H = np.fft.rfft(h, n=n_fft)
    y = np.fft.irfft(X * H, n=n_fft)
    return y[: len(x)].astype(np.float64)


def save_stereo_wav(filepath: str, left: np.ndarray, right: np.ndarray) -> None:
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    n_samples: int = min(len(left), len(right))
    l_ch = np.asarray(left[:n_samples], dtype=np.float64)
    r_ch = np.asarray(right[:n_samples], dtype=np.float64)
    stereo = np.vstack((l_ch, r_ch)).T
    peak: float = float(np.max(np.abs(stereo))) if stereo.size > 0 else 1e-6
    scale: float = (0.97 * 32767.0) / max(peak, 1e-6)
    pcm16 = np.clip(np.round(stereo * scale), -32767, 32767).astype("<i2")

    with wave.open(filepath, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm16.tobytes())
    print(f"[Audio] Wrote STEREO {filepath} ({n_samples / SAMPLE_RATE:.2f}s, nchannels=2, peak=0.97)")


def asymmetric_wavefold_growl(x: np.ndarray, drive: float = 2.8, asym: float = 0.28) -> np.ndarray:
    driven = x * drive + asym
    folded = np.tanh(driven) + 0.32 * np.sin(driven * 2.1) - np.tanh(asym)
    return np.tanh(folded * 1.15)


def time_varying_air_damping(audio: np.ndarray, transient_ms: float = 6.5) -> np.ndarray:
    n: int = len(audio)
    t = np.arange(n, dtype=np.float64) / float(SAMPLE_RATE)
    transient_s: float = transient_ms * 0.001
    w_bright = np.exp(-np.maximum(0.0, t - transient_s) * 85.0)
    w_mid = (1.0 - w_bright) * np.exp(-np.maximum(0.0, t - 0.035) * 14.0)
    w_dark = np.clip(1.0 - w_bright - w_mid, 0.0, 1.0)

    mid_band = _dsp_lowpass(audio, 4800.0, order=2)
    dark_band = _dsp_lowpass(audio, 1350.0, order=2)
    return (audio * w_bright + mid_band * w_mid + dark_band * w_dark).astype(np.float64)


def waveguide_steel_impact(
    dur_s: float,
    base_freq: float,
    stiffness: float,
    decay_rate: float,
    scrape_ms: float,
    rng: np.random.Generator,
) -> np.ndarray:
    n: int = max(1, int(dur_s * SAMPLE_RATE))
    out = np.zeros(n, dtype=np.float64)
    scrape_s: float = max(0.0, scrape_ms * 0.001)
    scrape_samples: int = min(n - 1, int(scrape_s * SAMPLE_RATE))

    # 1. Pre-Impact Metallic Burr Scrape (scrape_ms)
    if scrape_samples > 4:
        ts = np.arange(scrape_samples, dtype=np.float64) / float(SAMPLE_RATE)
        prog = ts / max(scrape_s, 1e-4)
        noise_scr = rng.standard_normal(scrape_samples)
        bp_scr = _dsp_bandpass(noise_scr, 2600.0, 12500.0, order=2)
        chirp_freq = 1800.0 + (4200.0 - 1800.0) * (prog ** 1.35)
        chirp_phase = 2.0 * np.pi * np.cumsum(chirp_freq) / float(SAMPLE_RATE)
        am_mod = 0.55 + 0.45 * np.sin(chirp_phase)
        scr_env = np.sin(prog * np.pi) * (0.38 + 0.62 * prog)
        out[:scrape_samples] += bp_scr * am_mod * scr_env * 0.42

    # 2. Primary + Secondary Micro-Bounce (0.0ms and +1.9ms at 0.48x gain) relative to impact start
    impact_idx: int = scrape_samples
    rem: int = n - impact_idx
    if rem > 4:
        ti = np.arange(rem, dtype=np.float64) / float(SAMPLE_RATE)
        ratios = [1.0, 1.593, 2.136, 2.918, 3.842, 5.117, 6.731, 8.490]
        nyq_limit: float = SAMPLE_RATE * 0.46

        def _synth_single_bounce(t_vec: np.ndarray) -> np.ndarray:
            w_noise = rng.standard_normal(len(t_vec))
            hi_imp = _dsp_bandpass(w_noise, 3200.0, 15500.0, order=2) * np.exp(-t_vec * 950.0) * 0.85
            mass_punch = _dsp_bandpass(w_noise, 950.0, 3200.0, order=2) * np.exp(-t_vec * 380.0) * 0.90
            modes_sum = np.zeros(len(t_vec), dtype=np.float64)
            fm_chirp = 1.0 + 0.085 * np.exp(-t_vec * 720.0)
            for m_idx, r in enumerate(ratios):
                f_mode: float = base_freq * (r ** stiffness)
                if f_mode >= nyq_limit:
                    continue
                mode_decay: float = decay_rate * (1.0 + 0.34 * m_idx)
                mode_amp: float = 1.0 / (1.0 + 0.42 * m_idx)
                phase_m = 2.0 * np.pi * f_mode * t_vec * fm_chirp + float(rng.uniform(0.0, 2.0 * np.pi))
                modes_sum += mode_amp * np.sin(phase_m) * np.exp(-t_vec * mode_decay)
            return hi_imp + mass_punch + modes_sum * 0.72

        primary = _synth_single_bounce(ti)
        out[impact_idx:] += primary

        bounce_offset: int = int(0.0019 * SAMPLE_RATE)
        if impact_idx + bounce_offset < n - 4:
            tb = np.arange(n - (impact_idx + bounce_offset), dtype=np.float64) / float(SAMPLE_RATE)
            secondary = _synth_single_bounce(tb) * 0.48
            out[impact_idx + bounce_offset :] += secondary

    peak: float = float(np.max(np.abs(out))) if len(out) > 0 else 1.0
    if peak > 1e-6:
        out = out / peak
    return out


def stereo_catacomb_acoustics(
    mono_dry: np.ndarray,
    stereo_width: float,
    sub_tail_wet: float,
    decay_sec: float,
    pan_bias: float = 0.0,
) -> tuple[np.ndarray, np.ndarray]:
    n: int = len(mono_dry)
    ir_len: int = max(int(min(decay_sec, 1.6) * SAMPLE_RATE), int(0.25 * SAMPLE_RATE))
    rng_l = np.random.default_rng(9101)
    rng_r = np.random.default_rng(9209)

    # Uncorrelated stone-wall Haas early reflection taps
    early_l = np.zeros(ir_len, dtype=np.float64)
    early_r = np.zeros(ir_len, dtype=np.float64)
    left_taps_ms = [8.0, 19.0, 33.0, 51.0, 74.0, 105.0]
    right_taps_ms = [12.0, 24.0, 39.0, 58.0, 83.0, 116.0]
    tap_gains = [0.58, 0.44, 0.34, 0.25, 0.18, 0.12]
    tap_signs_l = [1.0, -1.0, 1.0, 1.0, -1.0, 1.0]
    tap_signs_r = [1.0, 1.0, -1.0, 1.0, -1.0, -1.0]

    for ms, g, sgn in zip(left_taps_ms, tap_gains, tap_signs_l):
        idx = int(ms * 0.001 * SAMPLE_RATE)
        if idx < ir_len:
            early_l[idx] += g * sgn
    for ms, g, sgn in zip(right_taps_ms, tap_gains, tap_signs_r):
        idx = int(ms * 0.001 * SAMPLE_RATE)
        if idx < ir_len:
            early_r[idx] += g * sgn

    early_l = _dsp_bandpass(early_l, 240.0, 3800.0, order=2)
    early_r = _dsp_bandpass(early_r, 240.0, 3800.0, order=2)

    # Decorrelated stereo dark catacomb late tails (42Hz-680Hz)
    t_ir = np.arange(ir_len, dtype=np.float64) / float(SAMPLE_RATE)
    late_env = (1.0 - np.exp(-t_ir * 42.0)) * np.exp(-t_ir * (3.2 / max(decay_sec, 0.15)))
    late_l = _dsp_bandpass(rng_l.standard_normal(ir_len) * late_env, 42.0, 680.0, order=2) * 0.045
    late_r = _dsp_bandpass(rng_r.standard_normal(ir_len) * late_env, 42.0, 680.0, order=2) * 0.045

    refl_l = _dsp_fftconvolve(mono_dry, early_l * stereo_width + late_l * sub_tail_wet)
    refl_r = _dsp_fftconvolve(mono_dry, early_r * stereo_width + late_r * sub_tail_wet)

    pan_l: float = float(np.clip(1.0 - max(0.0, pan_bias), 0.25, 1.25))
    pan_r: float = float(np.clip(1.0 + min(0.0, pan_bias), 0.25, 1.25))
    if pan_bias > 0.0:
        pan_r = float(np.clip(1.0 + pan_bias * 0.35, 0.25, 1.35))
    elif pan_bias < 0.0:
        pan_l = float(np.clip(1.0 - pan_bias * 0.35, 0.25, 1.35))

    left_out = mono_dry * pan_l + refl_l
    right_out = mono_dry * pan_r + refl_r
    return left_out[:n], right_out[:n]


def _mix_at(buf: np.ndarray, clip: np.ndarray, start_s: float, gain: float = 1.0) -> None:
    idx: int = max(0, int(start_s * SAMPLE_RATE))
    if idx >= len(buf):
        return
    avail: int = min(len(clip), len(buf) - idx)
    if avail > 0:
        buf[idx : idx + avail] += clip[:avail] * gain



def write_wav_mono(filepath: str, samples: list[float], peak_amp: float = 0.85) -> None:
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    max_val: float = max((abs(s) for s in samples), default=1e-6)
    scale: float = (peak_amp * 32767.0) / max(max_val, 1e-6)

    with wave.open(filepath, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        raw_bytes = bytearray()
        for s in samples:
            v = int(max(-32767.0, min(32767.0, s * scale)))
            raw_bytes.extend(struct.pack("<h", v))
        wf.writeframes(raw_bytes)
    print(f"[Audio] Wrote {filepath} ({len(samples) / SAMPLE_RATE:.2f}s, peak={peak_amp:.2f})")


def make_seamless_loop(raw_samples: list[float], target_len: int, fade_len: int) -> list[float]:
    """
    Takes `target_len + fade_len` samples and crossfades the trailing `fade_len` samples
    into the leading `fade_len` samples using an equal-power sin/cos window so LOOP_FORWARD is click-free,
    with a micro endpoint tie so abs(sample[0] - sample[-1]) < 0.001.
    """
    out: list[float] = list(raw_samples[:target_len])
    for i in range(fade_len):
        t: float = i / float(fade_len)
        w_in: float = math.sin(0.5 * t * math.pi)
        w_out: float = math.cos(0.5 * t * math.pi)
        out[i] = out[i] * w_in + raw_samples[target_len + i] * w_out
    # Smoothly tie the final 64 samples and first 64 samples to their exact midpoint
    tie_len: int = min(64, target_len // 8)
    mid_val: float = 0.5 * (out[0] + out[-1])
    for k in range(tie_len):
        alpha: float = k / float(tie_len)
        out[k] = mid_val * (1.0 - alpha) + out[k] * alpha
        out[target_len - 1 - k] = mid_val * (1.0 - alpha) + out[target_len - 1 - k] * alpha
    return out


class CascadedThreePoleLowPass:
    """
    3-pole cascaded one-pole RC low-pass filter (-18 dB/octave rolloff)
    that completely eliminates high-frequency white/pink noise radio static.
    """

    def __init__(self) -> None:
        self.y1: float = 0.0
        self.y2: float = 0.0
        self.y3: float = 0.0

    def process(self, x: float, cutoff_hz: float) -> float:
        c: float = min(max(cutoff_hz, 20.0), 275.0)
        rc: float = 1.0 / (2.0 * math.pi * c)
        dt: float = 1.0 / float(SAMPLE_RATE)
        alpha: float = dt / (rc + dt)
        self.y1 += alpha * (x - self.y1)
        self.y2 += alpha * (self.y1 - self.y2)
        self.y3 += alpha * (self.y2 - self.y3)
        return self.y3


class StateVariableBandpass:
    def __init__(self, q: float = 2.5) -> None:
        self.low: float = 0.0
        self.band: float = 0.0
        self.q: float = q

    def process(self, x: float, cutoff_hz: float) -> tuple[float, float]:
        f: float = 2.0 * math.sin(math.pi * min(cutoff_hz, SAMPLE_RATE * 0.42) / SAMPLE_RATE)
        self.low += f * self.band
        high: float = x - self.low - (self.band / self.q)
        self.band += f * high
        return self.low, self.band


def generate_ambient_moor_wind_loop(out_dir: str) -> None:
    """
    10.0s seamless loop: soft, deep, low-frequency air rumble using a 3-pole cascaded
    low-pass filter (cutoff < 280 Hz) on integrated brown noise with slow sinusoidal swells
    and low amplitude (max_amp = 0.12). Zero high-frequency hiss/static!
    """
    rng = random.Random(101)
    dur_samples = int(10.0 * SAMPLE_RATE)
    fade_samples = int(2.0 * SAMPLE_RATE)
    total = dur_samples + fade_samples

    lp3 = CascadedThreePoleLowPass()
    brown: float = 0.0
    raw: list[float] = []

    for i in range(total):
        t = i / float(SAMPLE_RATE)
        white = rng.uniform(-1.0, 1.0)
        # Integrated brown noise (leaky integrator)
        brown = (brown + 0.025 * white) * 0.992

        # Slow sinusoidal cutoff modulation strictly below 280 Hz (110 Hz to 255 Hz)
        lfo1 = 0.5 + 0.5 * math.sin(t * 2.0 * math.pi * 0.10)
        lfo2 = 0.5 + 0.5 * math.cos(t * 2.0 * math.pi * 0.20 + 0.7)
        cutoff = 110.0 + (0.65 * lfo1 + 0.35 * lfo2) * 145.0  # Max 255 Hz < 280 Hz

        deep_wind = lp3.process(brown, cutoff)
        swell = 0.48 + 0.52 * (0.6 * lfo1 + 0.4 * lfo2)
        sub_undertone = 0.06 * math.sin(t * 2.0 * math.pi * 58.0 + 0.4 * math.sin(t * 2.0 * math.pi * 0.10))
        raw.append(deep_wind * swell + sub_undertone)

    looped = make_seamless_loop(raw, dur_samples, fade_samples)
    write_wav_mono(os.path.join(out_dir, "ambient_moor_wind_loop.wav"), looped, peak_amp=0.12)


def generate_ambient_church_draft_loop(out_dir: str) -> None:
    """
    10.0s seamless loop: deep, hollow stone-hall air resonance using a 3-pole cascaded
    low-pass filter (cutoff < 240 Hz) on brown noise with low amplitude (max_amp = 0.12).
    """
    rng = random.Random(202)
    dur_samples = int(10.0 * SAMPLE_RATE)
    fade_samples = int(2.0 * SAMPLE_RATE)
    total = dur_samples + fade_samples

    lp3 = CascadedThreePoleLowPass()
    brown: float = 0.0
    raw: list[float] = []

    for i in range(total):
        t = i / float(SAMPLE_RATE)
        white = rng.uniform(-1.0, 1.0)
        brown = (brown + 0.022 * white) * 0.993

        # Slow cavity air swell (cutoff strictly between 85 Hz and 215 Hz < 280 Hz)
        lfo_cav = 0.5 + 0.5 * math.sin(t * 2.0 * math.pi * 0.10)
        cutoff = 85.0 + lfo_cav * 130.0
        filtered = lp3.process(brown, cutoff)

        # Subtle stone room modal hum (98Hz & 147Hz fifth)
        modal = 0.12 * math.sin(t * 2.0 * math.pi * 98.0) + 0.07 * math.sin(t * 2.0 * math.pi * 147.0)
        swell = 0.50 + 0.50 * lfo_cav
        raw.append(filtered * swell + modal)

    looped = make_seamless_loop(raw, dur_samples, fade_samples)
    write_wav_mono(os.path.join(out_dir, "ambient_church_draft_loop.wav"), looped, peak_amp=0.12)


def generate_ambient_crypt_drone_loop(out_dir: str) -> None:
    """
    12.0s seamless loop: pure, smooth low-passed air hum (55Hz-140Hz, amplitude <= 0.12)
    with a 0.25-second equal-power crossfade at the loop boundary so there are zero clicks, pops, or bangs.
    """
    rng = random.Random(303)
    dur_samples = int(12.0 * SAMPLE_RATE)
    fade_samples = int(0.25 * SAMPLE_RATE)
    total = dur_samples + fade_samples

    lp3 = CascadedThreePoleLowPass()
    brown: float = 0.0
    raw: list[float] = []

    for i in range(total):
        t = i / float(SAMPLE_RATE)
        white = rng.uniform(-1.0, 1.0)
        brown = (brown + 0.018 * white) * 0.994

        hum_fund = math.sin(t * 2.0 * math.pi * 64.0)
        hum_fifth = math.sin(t * 2.0 * math.pi * 96.0 + 0.25 * math.sin(t * 2.0 * math.pi * 0.083333))
        hum_oct = math.sin(t * 2.0 * math.pi * 128.0)

        air_hum = lp3.process(brown, 125.0)
        sample = hum_fund * 0.36 + hum_fifth * 0.28 + hum_oct * 0.16 + air_hum * 0.28
        raw.append(sample)

    filtered_arr = _dsp_bandpass(np.asarray(raw, dtype=np.float64), 55.0, 140.0, order=2)
    looped = make_seamless_loop(filtered_arr.tolist(), dur_samples, fade_samples)
    write_wav_mono(os.path.join(out_dir, "ambient_crypt_drone_loop.wav"), looped, peak_amp=0.12)
    write_wav_mono(os.path.join(out_dir, "ambient_drone.wav"), looped, peak_amp=0.12)
    write_wav_mono(os.path.join(out_dir, "crypt_ambience.wav"), looped, peak_amp=0.12)


def generate_torch_fire_loop(out_dir: str) -> None:
    """6.0s seamless loop: warm low flame rumble + subtle wood resin ember pops."""
    rng = random.Random(404)
    dur_samples = int(6.0 * SAMPLE_RATE)
    fade_samples = int(1.0 * SAMPLE_RATE)
    total = dur_samples + fade_samples

    lp_flame = CascadedThreePoleLowPass()
    bp_snap = StateVariableBandpass(q=4.2)
    brown: float = 0.0
    crackle_env: float = 0.0
    raw: list[float] = []

    for i in range(total):
        t = i / float(SAMPLE_RATE)
        white = rng.uniform(-1.0, 1.0)
        brown = (brown + 0.03 * white) * 0.99

        flutter = 0.65 + 0.35 * math.sin(t * 2.0 * math.pi * 3.8 + 1.2 * math.sin(t * 2.0 * math.pi * 1.5))
        low_f = lp_flame.process(brown, 165.0 + 55.0 * flutter)

        if rng.random() < 0.0012:
            crackle_env = rng.uniform(0.4, 0.9)
        crackle_env *= 0.990
        _, snap = bp_snap.process(white, rng.uniform(1800.0, 3600.0))

        sample = low_f * 0.75 * flutter + snap * crackle_env * 0.45
        raw.append(sample)

    looped = make_seamless_loop(raw, dur_samples, fade_samples)
    write_wav_mono(os.path.join(out_dir, "torch_fire_loop.wav"), looped, peak_amp=0.38)


def generate_footsteps(out_dir: str) -> None:
    """
    Synthesizes warm, natural, non-metallic footstep audio banks:
    - footstep_stone_01..04.wav: Deep warm leather-boot heel thud (120Hz-450Hz low-mid thump + soft 900Hz sole tap, max_amp = 0.45)
    - footstep_gravel_01..04.wav: Soft low-mid dirt/pebble crunch (400Hz-1,800Hz filtered crunch, max_amp = 0.40)
    - footstep_grass_01..04.wav: Soft muffled earth step + low swish (max_amp = 0.35)
    - footstep_wood_01..04.wav: Warm hollow plank step (130Hz & 260Hz, max_amp = 0.40)
    """
    dur = int(0.32 * SAMPLE_RATE)

    # 1. STONE FOOTSTEPS (120Hz-450Hz warm leather boot thud + soft 900Hz sole tap, max_amp = 0.45)
    for idx in range(1, 5):
        rng = random.Random(700 + idx)
        bp_low_mid = StateVariableBandpass(q=1.8)
        bp_sole_tap = StateVariableBandpass(q=2.2)
        samples: list[float] = []
        f_heel = 122.0 + idx * 6.0
        f_mid = 240.0 + idx * 14.0
        for i in range(dur):
            t = i / float(SAMPLE_RATE)
            white = rng.uniform(-1.0, 1.0)
            heel_env = math.exp(-t * 38.0) * (1.0 - math.exp(-t * 650.0))
            t2 = max(0.0, t - 0.045)
            sole_env = (math.exp(-t2 * 48.0) * (1.0 - math.exp(-t2 * 550.0))) if t >= 0.045 else 0.0

            heel_thud = (
                math.sin(2.0 * math.pi * f_heel * t * math.exp(-t * 6.0)) * 0.75
                + math.sin(2.0 * math.pi * f_mid * t * math.exp(-t * 10.0)) * 0.35
            ) * heel_env
            _, warm_body = bp_low_mid.process(white, 310.0 + idx * 25.0)
            _, sole_tap = bp_sole_tap.process(white, 860.0 + idx * 20.0)

            sample = heel_thud * 0.90 + warm_body * heel_env * 0.35 + sole_tap * sole_env * 0.22
            samples.append(sample)
        write_wav_mono(os.path.join(out_dir, f"footstep_stone_0{idx}.wav"), samples, peak_amp=0.45)

    # 2. GRAVEL FOOTSTEPS (400Hz-1,800Hz soft low-mid dirt/pebble crunch, max_amp = 0.40)
    for idx in range(1, 5):
        rng = random.Random(800 + idx)
        bp_dirt = StateVariableBandpass(q=1.6)
        bp_pebble = StateVariableBandpass(q=2.0)
        samples = []
        grain_env: float = 0.0
        for i in range(dur):
            t = i / float(SAMPLE_RATE)
            white = rng.uniform(-1.0, 1.0)
            heel_env = math.exp(-t * 30.0) * (1.0 - math.exp(-t * 500.0))
            if t < 0.16 and rng.random() < 0.028:
                grain_env = rng.uniform(0.45, 0.85)
            grain_env *= 0.968
            thud = math.sin(2.0 * math.pi * (95.0 + idx * 5.0) * t * math.exp(-t * 6.0)) * heel_env
            _, dirt_body = bp_dirt.process(white, 540.0 + idx * 45.0)
            _, pebble_crunch = bp_pebble.process(white, 1150.0 + idx * 95.0)
            sample = (
                thud * 0.75
                + dirt_body * (heel_env * 0.45 + grain_env * 0.40) * math.exp(-t * 9.0)
                + pebble_crunch * grain_env * 0.28 * math.exp(-t * 11.0)
            )
            samples.append(sample)
        write_wav_mono(os.path.join(out_dir, f"footstep_gravel_0{idx}.wav"), samples, peak_amp=0.40)

    # 3. GRASS FOOTSTEPS (Soft muffled earth step + low swish, max_amp = 0.35)
    for idx in range(1, 5):
        rng = random.Random(900 + idx)
        bp_earth = StateVariableBandpass(q=1.4)
        bp_swish = StateVariableBandpass(q=1.6)
        samples = []
        for i in range(dur):
            t = i / float(SAMPLE_RATE)
            white = rng.uniform(-1.0, 1.0)
            thump_env = math.exp(-t * 34.0) * (1.0 - math.exp(-t * 450.0))
            swish_env = math.sin(min(1.0, t / 0.22) * math.pi) * math.exp(-t * 8.5)
            thump = math.sin(2.0 * math.pi * (78.0 + idx * 4.0) * t * math.exp(-t * 5.0)) * thump_env
            _, earth_low = bp_earth.process(white, 260.0 + idx * 20.0)
            _, low_swish = bp_swish.process(white, 680.0 + idx * 45.0)
            samples.append(thump * 0.85 + earth_low * thump_env * 0.35 + low_swish * swish_env * 0.28)
        write_wav_mono(os.path.join(out_dir, f"footstep_grass_0{idx}.wav"), samples, peak_amp=0.35)

    # 4. WOOD FOOTSTEPS (Warm hollow timber step, max_amp = 0.40)
    for idx in range(1, 5):
        rng = random.Random(1000 + idx)
        bp_wood = StateVariableBandpass(q=3.2)
        samples = []
        f1 = 128.0 + idx * 8.0
        f2 = f1 * 2.05
        for i in range(dur):
            t = i / float(SAMPLE_RATE)
            white = rng.uniform(-1.0, 1.0)
            env = math.exp(-t * 34.0) * (1.0 - math.exp(-t * 650.0))
            knock = (math.sin(2.0 * math.pi * f1 * t) + 0.40 * math.sin(2.0 * math.pi * f2 * t)) * env
            _, res = bp_wood.process(white, 380.0 + idx * 30.0)
            samples.append(knock * 0.85 + res * env * 0.45)
        write_wav_mono(os.path.join(out_dir, f"footstep_wood_0{idx}.wav"), samples, peak_amp=0.40)


def generate_crypt_water_drips(out_dir: str) -> None:
    """
    crypt_water_drip_01..03.wav & ambient_crypt_drip.wav:
    Strictly soft, high-passed (> 700Hz) upward pitch-chirped sine pings (1,100Hz -> 2,400Hz over 18ms)
    with a fast exponential decay exp(-t * 32.0) and peak amplitude capped at 0.18 (-15 dB).
    Zero low-frequency impulses, sub-bass thuds, or unfiltered noise bursts!
    """
    variants = [
        ("crypt_water_drip_01.wav", 1100.0, 2400.0),
        ("crypt_water_drip_02.wav", 1150.0, 2360.0),
        ("crypt_water_drip_03.wav", 1200.0, 2440.0),
        ("ambient_crypt_drip.wav", 1100.0, 2400.0),
    ]
    for filename, f_start, f_end in variants:
        dur = int(0.32 * SAMPLE_RATE)
        raw_samples: list[float] = []
        phase: float = 0.0

        for i in range(dur):
            t = i / float(SAMPLE_RATE)
            sweep_t = min(1.0, t / 0.018)
            freq = f_start + (f_end - f_start) * (sweep_t * sweep_t)
            phase += 2.0 * math.pi * freq / SAMPLE_RATE

            drop_env = math.exp(-t * 32.0) * (1.0 - math.exp(-t * 950.0))
            plink = math.sin(phase) * drop_env + 0.18 * math.sin(phase * 1.5) * math.exp(-t * 58.0)
            raw_samples.append(plink)

        hp_arr = _dsp_highpass(np.asarray(raw_samples, dtype=np.float64), 780.0, order=3)
        write_wav_mono(os.path.join(out_dir, filename), hp_arr.tolist(), peak_amp=0.18)
        ambient_copy_dir = os.path.join("assets", "audio", "ambient")
        if filename == "ambient_crypt_drip.wav":
            write_wav_mono(os.path.join(ambient_copy_dir, filename), hp_arr.tolist(), peak_amp=0.18)


def generate_cathedral_bell_distant(out_dir: str) -> None:
    """cathedral_bell_distant.wav: deep tarnished bronze bell toll (145Hz + minor-third overtones, 4.5s decay)."""
    dur = int(4.5 * SAMPLE_RATE)
    samples: list[float] = []
    f0 = 145.0
    partials = [
        (0.5, 0.35, 0.9),
        (1.0, 1.00, 1.3),
        (1.2, 0.72, 1.8),
        (1.5, 0.45, 2.5),
        (2.0, 0.55, 3.2),
        (2.42, 0.28, 4.5),
        (3.0, 0.18, 6.0),
    ]
    for i in range(dur):
        t = i / float(SAMPLE_RATE)
        attack = 1.0 - math.exp(-t * 180.0)
        fade_out = 1.0 if t < 3.8 else max(0.0, (4.5 - t) / 0.7)
        val: float = 0.0
        for ratio, amp, decay_rate in partials:
            freq = f0 * ratio
            beat = 1.0 + 0.12 * math.sin(t * 2.0 * math.pi * (1.4 * ratio))
            val += amp * math.sin(t * 2.0 * math.pi * freq) * math.exp(-t * decay_rate) * beat
        samples.append(val * attack * fade_out)

    write_wav_mono(os.path.join(out_dir, "cathedral_bell_distant.wav"), samples, peak_amp=0.75)


def generate_crypt_stone_settle(out_dir: str) -> None:
    """crypt_stone_settle.wav: soft high-passed (> 700Hz) double water droplet ping (no sub-bass thud)."""
    dur = int(0.42 * SAMPLE_RATE)
    raw_samples: list[float] = []
    phase1: float = 0.0
    phase2: float = 0.0

    for i in range(dur):
        t = i / float(SAMPLE_RATE)
        sweep1 = min(1.0, t / 0.018)
        f1 = 1120.0 + (2380.0 - 1120.0) * (sweep1 * sweep1)
        phase1 += 2.0 * math.pi * f1 / SAMPLE_RATE
        env1 = math.exp(-t * 32.0) * (1.0 - math.exp(-t * 950.0))
        val = math.sin(phase1) * env1

        if t >= 0.095:
            dt2 = t - 0.095
            sweep2 = min(1.0, dt2 / 0.018)
            f2 = 1280.0 + (2480.0 - 1280.0) * (sweep2 * sweep2)
            phase2 += 2.0 * math.pi * f2 / SAMPLE_RATE
            env2 = math.exp(-dt2 * 36.0) * (1.0 - math.exp(-dt2 * 950.0))
            val += math.sin(phase2) * env2 * 0.55

        raw_samples.append(val)

    hp_arr = _dsp_highpass(np.asarray(raw_samples, dtype=np.float64), 780.0, order=3)
    write_wav_mono(os.path.join(out_dir, "crypt_stone_settle.wav"), hp_arr.tolist(), peak_amp=0.16)


def generate_hub_anvil_upgrade(out_dir: str) -> None:
    """
    hub_anvil_upgrade.wav: Heavy blacksmith hammer-on-steel ring (1.8kHz & 3.1kHz resonant
    metallic chime + warm occult harmonic swell).
    """
    rng = random.Random(701)
    dur = int(1.45 * SAMPLE_RATE)
    samples: list[float] = []
    bp_strike = StateVariableBandpass(q=3.5)

    for i in range(dur):
        t = i / float(SAMPLE_RATE)
        # 1. Crisp metallic hammer-on-steel transient + 1.8kHz & 3.1kHz resonant ring
        strike_noise = rng.uniform(-1.0, 1.0) * math.exp(-t * 65.0)
        _, strike_band = bp_strike.process(strike_noise, 2200.0)
        anvil_ring = (
            0.55 * math.sin(t * 2.0 * math.pi * 1800.0) * math.exp(-t * 4.2)
            + 0.38 * math.sin(t * 2.0 * math.pi * 3100.0) * math.exp(-t * 5.8)
            + 0.24 * math.sin(t * 2.0 * math.pi * 920.0) * math.exp(-t * 3.1)
        )
        # 2. Warm occult harmonic swell (220Hz + 330Hz fifth + 440Hz octave)
        swell_env = math.sin(min(1.0, t / 1.35) * math.pi) * math.exp(-t * 1.1)
        occult_chord = (
            0.32 * math.sin(t * 2.0 * math.pi * 220.0)
            + 0.24 * math.sin(t * 2.0 * math.pi * 330.0)
            + 0.18 * math.sin(t * 2.0 * math.pi * 440.0)
        ) * swell_env
        samples.append(strike_band * 0.45 + anvil_ring + occult_chord)

    write_wav_mono(os.path.join(out_dir, "hub_anvil_upgrade.wav"), samples, peak_amp=0.80)


def generate_hub_armor_equip(out_dir: str) -> None:
    """
    hub_armor_equip.wav: Layered heavy leather strap cinch + articulated steel gauntlet plate latch clank.
    """
    rng = random.Random(702)
    dur = int(0.95 * SAMPLE_RATE)
    samples: list[float] = []
    bp_leather = StateVariableBandpass(q=2.2)
    bp_clank = StateVariableBandpass(q=4.8)

    for i in range(dur):
        t = i / float(SAMPLE_RATE)
        white = rng.uniform(-1.0, 1.0)
        # 1. Leather strap cinch friction (0.0s..0.38s)
        leather_env = math.sin(min(1.0, t / 0.36) * math.pi) if t < 0.36 else 0.0
        _, leather_creak = bp_leather.process(white * leather_env, 320.0 + 180.0 * math.sin(t * 28.0))

        # 2. Articulated steel gauntlet plate clank at t = 0.34s and buckle latch at t = 0.56s
        clank_val: float = 0.0
        if t >= 0.34:
            dt1 = t - 0.34
            _, c_band = bp_clank.process(white * math.exp(-dt1 * 48.0), 1450.0)
            plate_res = (
                0.50 * math.sin(dt1 * 2.0 * math.pi * 680.0) * math.exp(-dt1 * 18.0)
                + 0.40 * math.sin(dt1 * 2.0 * math.pi * 1420.0) * math.exp(-dt1 * 24.0)
                + 0.25 * math.sin(dt1 * 2.0 * math.pi * 2380.0) * math.exp(-dt1 * 32.0)
            )
            clank_val += c_band * 0.45 + plate_res
        if t >= 0.56:
            dt2 = t - 0.56
            latch_click = (
                0.45 * math.sin(dt2 * 2.0 * math.pi * 1950.0) * math.exp(-dt2 * 38.0)
                + 0.35 * math.sin(dt2 * 2.0 * math.pi * 2850.0) * math.exp(-dt2 * 45.0)
            )
            clank_val += latch_click

        samples.append(leather_creak * 0.55 + clank_val)

    write_wav_mono(os.path.join(out_dir, "hub_armor_equip.wav"), samples, peak_amp=0.78)


def generate_hub_weapon_mod(out_dir: str) -> None:
    """
    hub_weapon_mod.wav: Crisp gunsmith vice ratchet + brass cartridge slide + revolver cylinder lock.
    """
    rng = random.Random(703)
    dur = int(0.88 * SAMPLE_RATE)
    samples: list[float] = []
    bp_slide = StateVariableBandpass(q=4.0)

    ratchet_times = (0.02, 0.08, 0.14, 0.20)
    for i in range(dur):
        t = i / float(SAMPLE_RATE)
        val: float = 0.0
        # 1. 4 crisp gunsmith vice ratchet clicks
        for rt in ratchet_times:
            if t >= rt:
                dt = t - rt
                val += 0.38 * math.sin(dt * 2.0 * math.pi * 2450.0) * math.exp(-dt * 95.0)
                val += 0.25 * math.sin(dt * 2.0 * math.pi * 1350.0) * math.exp(-dt * 75.0)

        # 2. Brass cartridge slide chime (0.28s..0.52s)
        if 0.28 <= t <= 0.56:
            dt_s = t - 0.28
            slide_env = math.sin(min(1.0, dt_s / 0.24) * math.pi)
            _, s_band = bp_slide.process(rng.uniform(-1.0, 1.0) * slide_env, 1600.0 + 900.0 * (dt_s / 0.24))
            brass_ping = 0.30 * math.sin(dt_s * 2.0 * math.pi * 2180.0) * math.exp(-dt_s * 16.0)
            val += s_band * 0.35 + brass_ping

        # 3. Heavy revolver cylinder lock click at t = 0.58s
        if t >= 0.58:
            dt_l = t - 0.58
            val += (
                0.60 * math.sin(dt_l * 2.0 * math.pi * 1120.0) * math.exp(-dt_l * 35.0)
                + 0.48 * math.sin(dt_l * 2.0 * math.pi * 2640.0) * math.exp(-dt_l * 48.0)
            )

        samples.append(val)

    write_wav_mono(os.path.join(out_dir, "hub_weapon_mod.wav"), samples, peak_amp=0.78)


def generate_hub_sanctuary_heal(out_dir: str) -> None:
    """
    hub_sanctuary_heal.wav: Deep warm cathedral chord shimmer + liquid oil resonance.
    """
    rng = random.Random(704)
    dur = int(1.65 * SAMPLE_RATE)
    samples: list[float] = []
    bp_oil = StateVariableBandpass(q=5.5)

    for i in range(dur):
        t = i / float(SAMPLE_RATE)
        attack = 1.0 - math.exp(-t * 14.0)
        decay = math.exp(-t * 1.45)
        env = attack * decay

        # Warm cathedral major/fifth chord shimmer (196Hz G3, 294Hz D4, 392Hz G4, 493.88Hz B4, 588Hz D5)
        vib = 1.0 + 0.004 * math.sin(t * 2.0 * math.pi * 5.2)
        chord = (
            0.36 * math.sin(t * 2.0 * math.pi * 196.0 * vib)
            + 0.28 * math.sin(t * 2.0 * math.pi * 294.0 * vib)
            + 0.22 * math.sin(t * 2.0 * math.pi * 392.0 * vib)
            + 0.16 * math.sin(t * 2.0 * math.pi * 493.88 * vib)
            + 0.12 * math.sin(t * 2.0 * math.pi * 588.0 * vib)
        ) * env

        # Gentle consecrated liquid oil resonance
        oil_freq = 520.0 + 180.0 * math.sin(t * 2.0 * math.pi * 3.4)
        _, oil_res = bp_oil.process(rng.uniform(-1.0, 1.0) * math.exp(-t * 2.6), oil_freq)
        samples.append(chord + oil_res * 0.18)

    write_wav_mono(os.path.join(out_dir, "hub_sanctuary_heal.wav"), samples, peak_amp=0.76)


def generate_portal_hum_loop(out_dir: str) -> None:
    """
    portal_hum_loop.wav: 8.0s seamless loop of a deep phase-shifted sub-bass dimensional hum
    (48Hz + 72Hz fifth + slow LFO formant sweep, zero high-frequency hiss).
    """
    rng = random.Random(801)
    dur_samples = int(8.0 * SAMPLE_RATE)
    fade_samples = int(1.6 * SAMPLE_RATE)
    total = dur_samples + fade_samples

    lp3 = CascadedThreePoleLowPass()
    brown: float = 0.0
    raw: list[float] = []

    for i in range(total):
        t = i / float(SAMPLE_RATE)
        white = rng.uniform(-1.0, 1.0)
        brown = (brown + 0.024 * white) * 0.993

        # Phase-shifted sub-bass dimensional drone (48Hz & 48.5Hz beating + 72Hz fifth + 144Hz harmonic)
        lfo_phase = 0.85 * math.sin(t * 2.0 * math.pi * 0.25)
        sub_a = math.sin(t * 2.0 * math.pi * 48.0 + lfo_phase)
        sub_b = math.sin(t * 2.0 * math.pi * 48.5 - lfo_phase * 0.7)
        fifth = math.sin(t * 2.0 * math.pi * 72.0 + 0.5 * math.cos(t * 2.0 * math.pi * 0.125))
        harmonic = math.sin(t * 2.0 * math.pi * 144.0 + 1.2 * math.sin(t * 2.0 * math.pi * 0.375))

        cutoff = 115.0 + 85.0 * (0.5 + 0.5 * math.sin(t * 2.0 * math.pi * 0.25))
        deep_air = lp3.process(brown, cutoff)
        pulse = 0.72 + 0.28 * math.sin(t * 2.0 * math.pi * 0.50)

        sample = ((sub_a + sub_b) * 0.36 + fifth * 0.28 + harmonic * 0.14 + deep_air * 0.32) * pulse
        raw.append(sample)

    looped = make_seamless_loop(raw, dur_samples, fade_samples)
    write_wav_mono(os.path.join(out_dir, "portal_hum_loop.wav"), looped, peak_amp=0.42)


def generate_portal_warp_enter(out_dir: str) -> None:
    """
    portal_warp_enter.wav: Heavy sub-drop + reverse-reverb dimensional whoosh + occult bell transient
    when crossing an Occult Rift threshold.
    """
    rng = random.Random(802)
    dur = int(1.55 * SAMPLE_RATE)
    samples: list[float] = []
    bp_whoosh = StateVariableBandpass(q=2.6)
    lp_sub = CascadedThreePoleLowPass()
    brown: float = 0.0
    sub_phase: float = 0.0

    for i in range(dur):
        t = i / float(SAMPLE_RATE)
        white = rng.uniform(-1.0, 1.0)
        brown = (brown + 0.035 * white) * 0.991

        # 1. Reverse-reverb swell up to t = 0.32s followed by deep cavern decay
        if t < 0.32:
            swell_env = (t / 0.32) ** 2.2
        else:
            swell_env = math.exp(-(t - 0.32) * 2.8)

        sweep_freq = 180.0 + 620.0 * math.sin(min(1.0, t / 0.65) * math.pi)
        _, whoosh_band = bp_whoosh.process(white * swell_env, sweep_freq)
        low_rumble = lp_sub.process(brown, 160.0) * swell_env

        # 2. Heavy dimensional sub-drop (115Hz -> 34Hz) starting at t = 0.18s
        sub_drop: float = 0.0
        if t >= 0.18:
            dt = t - 0.18
            f_inst = 34.0 + 81.0 * math.exp(-dt * 4.5)
            sub_phase += 2.0 * math.pi * f_inst / SAMPLE_RATE
            sub_env = (1.0 - math.exp(-dt * 65.0)) * math.exp(-dt * 2.1)
            sub_drop = math.sin(sub_phase) * sub_env * 0.85

        # 3. Occult harmonic shimmer chord (144Hz, 216Hz, 288Hz, 432Hz)
        chord_env = math.sin(min(1.0, t / 1.45) * math.pi) * math.exp(-t * 1.4)
        chord = (
            0.30 * math.sin(t * 2.0 * math.pi * 144.0)
            + 0.24 * math.sin(t * 2.0 * math.pi * 216.0)
            + 0.18 * math.sin(t * 2.0 * math.pi * 288.0)
            + 0.12 * math.sin(t * 2.0 * math.pi * 432.0)
        ) * chord_env

        samples.append(sub_drop + whoosh_band * 0.48 + low_rumble * 0.40 + chord * 0.55)

    write_wav_mono(os.path.join(out_dir, "portal_warp_enter.wav"), samples, peak_amp=0.82)


def generate_loot_drop_spawn(out_dir: str) -> None:
    """
    loot_drop_spawn.wav: Crisp metallic coin/crystal pop + upward harmonic shimmer
    when loot bursts from an enemy or chest.
    """
    dur = int(0.55 * SAMPLE_RATE)
    samples: list[float] = []
    phase: float = 0.0
    for i in range(dur):
        t = i / float(SAMPLE_RATE)
        # Upward pitch pop (280Hz -> 620Hz) + crystalline harmonics (1480Hz, 2220Hz, 2960Hz)
        f_pop = 280.0 + 340.0 * min(1.0, t / 0.06)
        phase += 2.0 * math.pi * f_pop / SAMPLE_RATE
        pop_env = (1.0 - math.exp(-t * 450.0)) * math.exp(-t * 28.0)
        shimmer_env = math.sin(min(1.0, t / 0.50) * math.pi) * math.exp(-t * 5.2)
        crystal = (
            0.48 * math.sin(t * 2.0 * math.pi * 1480.0)
            + 0.36 * math.sin(t * 2.0 * math.pi * 2220.0)
            + 0.24 * math.sin(t * 2.0 * math.pi * 2960.0)
        ) * shimmer_env
        samples.append(math.sin(phase) * pop_env * 0.70 + crystal)
    write_wav_mono(os.path.join(out_dir, "loot_drop_spawn.wav"), samples, peak_amp=0.76)


def generate_loot_pickup_chime(out_dir: str) -> None:
    """
    loot_pickup_chime.wav: Satisfying resonant gothic chord + gear latch click on pickup.
    """
    dur = int(0.68 * SAMPLE_RATE)
    samples: list[float] = []
    for i in range(dur):
        t = i / float(SAMPLE_RATE)
        # Crisp latch click at t = 0.0s..0.04s + resonant gothic fifth/octave chime (528Hz, 792Hz, 1056Hz, 1584Hz)
        click = (
            0.55 * math.sin(t * 2.0 * math.pi * 1850.0) * math.exp(-t * 85.0)
            + 0.35 * math.sin(t * 2.0 * math.pi * 920.0) * math.exp(-t * 65.0)
        )
        chime_env = (1.0 - math.exp(-t * 120.0)) * math.exp(-t * 4.6)
        chord = (
            0.45 * math.sin(t * 2.0 * math.pi * 528.0)
            + 0.36 * math.sin(t * 2.0 * math.pi * 792.0)
            + 0.28 * math.sin(t * 2.0 * math.pi * 1056.0)
            + 0.18 * math.sin(t * 2.0 * math.pi * 1584.0)
        ) * chime_env
        samples.append(click + chord)
    write_wav_mono(os.path.join(out_dir, "loot_pickup_chime.wav"), samples, peak_amp=0.78)


def generate_rpg_level_up_fanfare(out_dir: str) -> None:
    """
    rpg_level_up_fanfare.wav: Deep cathedral organ/bell fifth chord (110Hz + 165Hz + 220Hz + 330Hz)
    with warm golden shimmer over 2.2s.
    """
    dur = int(2.2 * SAMPLE_RATE)
    samples: list[float] = []
    for i in range(dur):
        t = i / float(SAMPLE_RATE)
        attack = 1.0 - math.exp(-t * 18.0)
        decay = math.exp(-t * 1.15)
        fade_out = 1.0 if t < 1.85 else max(0.0, (2.2 - t) / 0.35)
        env = attack * decay * fade_out
        vib = 1.0 + 0.0035 * math.sin(t * 2.0 * math.pi * 5.0)
        organ_bell = (
            0.42 * math.sin(t * 2.0 * math.pi * 110.0 * vib)
            + 0.36 * math.sin(t * 2.0 * math.pi * 165.0 * vib)
            + 0.32 * math.sin(t * 2.0 * math.pi * 220.0 * vib)
            + 0.26 * math.sin(t * 2.0 * math.pi * 330.0 * vib)
            + 0.18 * math.sin(t * 2.0 * math.pi * 440.0 * vib)
            + 0.14 * math.sin(t * 2.0 * math.pi * 660.0 * vib)
        ) * env
        samples.append(organ_bell)
    write_wav_mono(os.path.join(out_dir, "rpg_level_up_fanfare.wav"), samples, peak_amp=0.84)


def generate_ability_lantern_pyre_blast(out_dir: str) -> None:
    """
    ability_lantern_pyre_blast.wav: Roaring occult flame whoosh + searing crackle ([F] Ability 1).
    """
    rng = random.Random(901)
    dur = int(1.15 * SAMPLE_RATE)
    samples: list[float] = []
    bp_roar = StateVariableBandpass(q=1.8)
    bp_sear = StateVariableBandpass(q=3.6)
    lp_sub = CascadedThreePoleLowPass()
    brown: float = 0.0
    for i in range(dur):
        t = i / float(SAMPLE_RATE)
        white = rng.uniform(-1.0, 1.0)
        brown = (brown + 0.04 * white) * 0.99
        env = (1.0 - math.exp(-t * 45.0)) * math.exp(-t * 2.6)
        sweep = 220.0 + 540.0 * math.exp(-t * 3.2)
        _, roar = bp_roar.process(white * env, sweep)
        _, sear = bp_sear.process(white * env, 1450.0 + 400.0 * math.sin(t * 32.0))
        sub = lp_sub.process(brown, 145.0) * env
        flame_thump = 0.55 * math.sin(t * 2.0 * math.pi * (85.0 * math.exp(-t * 3.5) + 42.0)) * env
        samples.append(flame_thump + sub * 0.55 + roar * 0.65 + sear * 0.28)
    write_wav_mono(os.path.join(out_dir, "ability_lantern_pyre_blast.wav"), samples, peak_amp=0.84)


def generate_ability_lantern_soul_chains(out_dir: str) -> None:
    """
    ability_lantern_soul_chains.wav: Heavy rattling spectral iron chains + deep sub-bass bind lock ([F] Ability 2).
    """
    rng = random.Random(902)
    dur = int(1.20 * SAMPLE_RATE)
    samples: list[float] = []
    bp_clank = StateVariableBandpass(q=4.5)
    link_times = (0.01, 0.07, 0.13, 0.20, 0.28, 0.37)
    for i in range(dur):
        t = i / float(SAMPLE_RATE)
        white = rng.uniform(-1.0, 1.0)
        val: float = 0.0
        for idx, lt in enumerate(link_times):
            if t >= lt:
                dt = t - lt
                f1 = 1180.0 + idx * 140.0
                f2 = 2340.0 + idx * 190.0
                ring = (
                    0.38 * math.sin(dt * 2.0 * math.pi * f1) * math.exp(-dt * 28.0)
                    + 0.28 * math.sin(dt * 2.0 * math.pi * f2) * math.exp(-dt * 36.0)
                )
                val += ring
        _, clank_band = bp_clank.process(white * math.exp(-t * 5.5), 1680.0)
        sub_lock = 0.65 * math.sin(t * 2.0 * math.pi * (68.0 - 22.0 * min(1.0, t))) * math.exp(-t * 2.4)
        icy_chord = (
            0.25 * math.sin(t * 2.0 * math.pi * 392.0)
            + 0.20 * math.sin(t * 2.0 * math.pi * 588.0)
        ) * math.exp(-t * 2.2)
        samples.append(val + clank_band * 0.32 + sub_lock + icy_chord)
    write_wav_mono(os.path.join(out_dir, "ability_lantern_soul_chains.wav"), samples, peak_amp=0.82)


def generate_ability_lantern_blood_nova(out_dir: str) -> None:
    """
    ability_lantern_blood_nova.wav: Dark resonant shockwave pulse + high crystalline life-drain hum ([F] Ability 3).
    """
    dur = int(1.35 * SAMPLE_RATE)
    samples: list[float] = []
    phase_sub: float = 0.0
    for i in range(dur):
        t = i / float(SAMPLE_RATE)
        f_sub = 36.0 + 95.0 * math.exp(-t * 5.0)
        phase_sub += 2.0 * math.pi * f_sub / SAMPLE_RATE
        sub_env = (1.0 - math.exp(-t * 80.0)) * math.exp(-t * 2.0)
        shockwave = math.sin(phase_sub) * sub_env * 0.85

        drain_env = math.sin(min(1.0, t / 1.25) * math.pi) * math.exp(-t * 1.6)
        vib = 1.0 + 0.012 * math.sin(t * 2.0 * math.pi * 8.5)
        drain_hum = (
            0.34 * math.sin(t * 2.0 * math.pi * 264.0 * vib)
            + 0.26 * math.sin(t * 2.0 * math.pi * 396.0 * vib)
            + 0.20 * math.sin(t * 2.0 * math.pi * 792.0 * vib)
            + 0.14 * math.sin(t * 2.0 * math.pi * 1188.0 * vib)
        ) * drain_env
        samples.append(shockwave + drain_hum)
    write_wav_mono(os.path.join(out_dir, "ability_lantern_blood_nova.wav"), samples, peak_amp=0.84)


def generate_revolver_fire(out_dir: str) -> None:
    """
    revolver_fire.wav (1.35s, 2-channel stereo):
    waveguide_steel_impact firing-pin pre-click (0..7ms, 1850Hz) + unfiltered supersonic N-wave crack
    (highpass 950Hz) + wavefolded midrange black-powder bark (320Hz-2,600Hz modulated by a 185Hz -> 55Hz
    combustion pulse, drive=3.2) + 199Hz -> 34Hz chest sub-punch + 1320Hz barrel ring, passed through
    time_varying_air_damping(6.5ms) and stereo_catacomb_acoustics(width=0.48, wet=0.40).
    """
    rng = np.random.default_rng(1101)
    dur_s: float = 1.35
    n: int = int(dur_s * SAMPLE_RATE)
    t = np.arange(n, dtype=np.float64) / float(SAMPLE_RATE)
    mono = np.zeros(n, dtype=np.float64)

    # 1. Firing-pin pre-click (0..7ms, 1850Hz)
    pin_click = waveguide_steel_impact(0.045, 1850.0, 1.24, 58.0, 1.8, rng)
    _mix_at(mono, pin_click, 0.0, gain=0.52)

    # Main blast starts at t0 = 0.007s (7ms)
    idx0: int = int(0.007 * SAMPLE_RATE)
    rem: int = n - idx0
    tb = np.arange(rem, dtype=np.float64) / float(SAMPLE_RATE)

    # 2. Unfiltered supersonic N-wave crack (highpass 950Hz)
    nwave_raw = (1.0 - 2.0 * np.minimum(1.0, tb / 0.0018)) * np.exp(-tb * 420.0) + rng.standard_normal(rem) * np.exp(-tb * 310.0) * 0.75
    nwave_crack = _dsp_highpass(nwave_raw, 950.0, order=2) * 1.15

    # 3. Wavefolded midrange black-powder bark (320Hz-2,600Hz modulated by 185Hz -> 55Hz combustion pulse, drive=3.2)
    f_comb = 55.0 + (185.0 - 55.0) * np.exp(-tb * 18.0)
    comb_phase = 2.0 * np.pi * np.cumsum(f_comb) / float(SAMPLE_RATE)
    comb_pulse = np.sin(comb_phase) * 0.65 + rng.standard_normal(rem) * 0.85
    mid_bp = _dsp_bandpass(comb_pulse, 320.0, 2600.0, order=2)
    bark_env = (1.0 - np.exp(-tb * 950.0)) * np.exp(-tb * 11.5)
    mid_bark = asymmetric_wavefold_growl(mid_bp * bark_env, drive=3.2, asym=0.28) * 0.92

    # 4. 199Hz -> 34Hz chest sub-punch
    f_sub = 34.0 + (199.0 - 34.0) * np.exp(-tb * 24.0)
    sub_phase = 2.0 * np.pi * np.cumsum(f_sub) / float(SAMPLE_RATE)
    sub_env = (1.0 - np.exp(-tb * 680.0)) * np.exp(-tb * 7.2)
    sub_punch = np.sin(sub_phase) * sub_env * 1.05

    # 5. 1320Hz octagonal steel barrel ring
    barrel_ring = (
        np.sin(2.0 * np.pi * 1320.0 * tb) * np.exp(-tb * 22.0) * 0.24
        + np.sin(2.0 * np.pi * 2112.0 * tb) * np.exp(-tb * 34.0) * 0.14
    )

    blast = time_varying_air_damping(nwave_crack + mid_bark + sub_punch + barrel_ring, transient_ms=6.5)
    mono[idx0:] += blast

    left, right = stereo_catacomb_acoustics(mono, stereo_width=0.48, sub_tail_wet=0.40, decay_sec=1.15, pan_bias=0.06)
    save_stereo_wav(os.path.join(out_dir, "revolver_fire.wav"), left, right)


def generate_revolver_cock_click(out_dir: str) -> None:
    """
    revolver_cock_click.wav (0.28s, 2-channel stereo):
    4 precision machined-steel waveguide stages at 0.008s (1950Hz, scrape=4ms),
    0.042s (2380Hz, scrape=6.5ms), 0.088s (2890Hz, scrape=2ms), and 0.132s (1680Hz, scrape=3.5ms).
    """
    rng = np.random.default_rng(1102)
    dur_s: float = 0.28
    n: int = int(dur_s * SAMPLE_RATE)
    mono = np.zeros(n, dtype=np.float64)

    stages = [
        (0.008, 1950.0, 1.24, 52.0, 4.0, 0.72),
        (0.042, 2380.0, 1.26, 56.0, 6.5, 0.84),
        (0.088, 2890.0, 1.28, 62.0, 2.0, 0.96),
        (0.132, 1680.0, 1.22, 46.0, 3.5, 0.88),
    ]
    for start_t, freq, stiff, dec, scr_ms, gain in stages:
        evt = waveguide_steel_impact(0.11, freq, stiff, dec, scr_ms, rng)
        _mix_at(mono, evt, start_t, gain=gain)

    left, right = stereo_catacomb_acoustics(mono, stereo_width=0.30, sub_tail_wet=0.16, decay_sec=0.24, pan_bias=0.08)
    save_stereo_wav(os.path.join(out_dir, "revolver_cock_click.wav"), left, right)


def generate_revolver_reload(out_dir: str) -> None:
    """
    revolver_reload.wav (0.92s, 2-channel stereo):
    9 distinct steel & hollow-brass waveguide events:
    - thumb latch & crane swing (0.015s, 1520Hz, scrape=12ms)
    - extractor rod push (0.105s, 2150Hz, scrape=18ms)
    - 3 high-pitched brass casing eject clinks (0.175s, 0.205s, 0.238s at 3290Hz-3780Hz, stiffness=1.33)
    - 6 rounds sliding in (0.375s, 1890Hz, scrape=22ms)
    - rim seat (0.455s, 2640Hz)
    - solid steel cylinder crane slam (0.615s, 1380Hz, scrape=8ms)
    - detent locking pin snap (0.648s, 2950Hz)
    """
    rng = np.random.default_rng(1103)
    dur_s: float = 0.92
    n: int = int(dur_s * SAMPLE_RATE)
    mono = np.zeros(n, dtype=np.float64)

    events = [
        (0.015, 0.14, 1520.0, 1.22, 38.0, 12.0, 0.82),  # 1. thumb latch & crane swing
        (0.105, 0.14, 2150.0, 1.24, 42.0, 18.0, 0.78),  # 2. extractor rod push
        (0.175, 0.12, 3290.0, 1.33, 28.0, 1.5, 0.65),   # 3. brass casing eject clink 1
        (0.205, 0.12, 3540.0, 1.33, 29.0, 1.5, 0.68),   # 4. brass casing eject clink 2
        (0.238, 0.12, 3780.0, 1.33, 30.0, 1.5, 0.64),   # 5. brass casing eject clink 3
        (0.375, 0.16, 1890.0, 1.25, 36.0, 22.0, 0.85),  # 6. 6 rounds sliding in
        (0.455, 0.12, 2640.0, 1.27, 48.0, 4.0, 0.76),   # 7. rim seat
        (0.615, 0.18, 1380.0, 1.21, 32.0, 8.0, 0.98),   # 8. solid steel cylinder crane slam
        (0.648, 0.14, 2950.0, 1.29, 54.0, 2.0, 0.92),   # 9. detent locking pin snap
    ]
    for start_t, evt_dur, freq, stiff, dec, scr_ms, gain in events:
        evt = waveguide_steel_impact(evt_dur, freq, stiff, dec, scr_ms, rng)
        _mix_at(mono, evt, start_t, gain=gain)

    left, right = stereo_catacomb_acoustics(mono, stereo_width=0.34, sub_tail_wet=0.20, decay_sec=0.45, pan_bias=0.06)
    save_stereo_wav(os.path.join(out_dir, "revolver_reload.wav"), left, right)


def generate_revolver_dry_fire(out_dir: str) -> None:
    """
    revolver_dry_fire.wav (0.22s, 2-channel stereo):
    Hardened steel hammer impact (2120Hz, stiffness=1.25, scrape=2ms).
    """
    rng = np.random.default_rng(1104)
    dur_s: float = 0.22
    mono = waveguide_steel_impact(dur_s, 2120.0, 1.25, 48.0, 2.0, rng)
    left, right = stereo_catacomb_acoustics(mono, stereo_width=0.28, sub_tail_wet=0.15, decay_sec=0.20, pan_bias=0.08)
    save_stereo_wav(os.path.join(out_dir, "revolver_dry_fire.wav"), left, right)


def generate_shotgun_fire_boom(out_dir: str) -> None:
    """
    shotgun_fire_boom.wav (1.55s, 2-channel stereo):
    Dual hammer drop (0..7ms) + twin staggered 12-gauge barrels (7ms and 15ms) combining
    supersonic buckshot rip (highpass 850Hz), wavefolded midrange dragon-roar (250Hz-2,300Hz, drive=3.6),
    205Hz -> 25Hz cannon sub-punch, and Damascus barrel ring (1080Hz), with wide stereo crypt tail
    (width=0.58, wet=0.48).
    """
    rng = np.random.default_rng(1001)
    dur_s: float = 1.55
    n: int = int(dur_s * SAMPLE_RATE)
    mono = np.zeros(n, dtype=np.float64)

    # 1. Dual hammer drop (0..7ms)
    hammer_l = waveguide_steel_impact(0.045, 1680.0, 1.24, 52.0, 1.6, rng)
    hammer_r = waveguide_steel_impact(0.045, 1760.0, 1.25, 54.0, 1.8, rng)
    _mix_at(mono, hammer_l, 0.000, gain=0.48)
    _mix_at(mono, hammer_r, 0.003, gain=0.48)

    # 2. Twin staggered 12-gauge barrels at 7ms (0.007s) and 15ms (0.015s)
    for b_idx, start_s in enumerate((0.007, 0.015)):
        idx_b: int = int(start_s * SAMPLE_RATE)
        rem: int = n - idx_b
        tb = np.arange(rem, dtype=np.float64) / float(SAMPLE_RATE)
        b_gain: float = 1.0 if b_idx == 0 else 0.92

        # Supersonic buckshot rip (highpass 850Hz)
        rip_raw = (1.0 - 2.0 * np.minimum(1.0, tb / 0.0022)) * np.exp(-tb * 360.0) + rng.standard_normal(rem) * np.exp(-tb * 240.0) * 0.85
        buckshot_rip = _dsp_highpass(rip_raw, 850.0, order=2) * 1.15

        # Wavefolded midrange dragon-roar (250Hz-2,300Hz, drive=3.6)
        f_roar = 46.0 + (165.0 - 46.0) * np.exp(-tb * 14.0)
        roar_phase = 2.0 * np.pi * np.cumsum(f_roar) / float(SAMPLE_RATE)
        roar_src = np.sin(roar_phase) * 0.70 + rng.standard_normal(rem) * 0.95
        roar_bp = _dsp_bandpass(roar_src, 250.0, 2300.0, order=2)
        roar_env = (1.0 - np.exp(-tb * 850.0)) * np.exp(-tb * 8.2)
        dragon_roar = asymmetric_wavefold_growl(roar_bp * roar_env, drive=3.6, asym=0.30) * 1.05

        # 205Hz -> 25Hz cannon sub-punch
        f_sub = 25.0 + (205.0 - 25.0) * np.exp(-tb * 19.0)
        sub_phase = 2.0 * np.pi * np.cumsum(f_sub) / float(SAMPLE_RATE)
        sub_env = (1.0 - np.exp(-tb * 620.0)) * np.exp(-tb * 5.4)
        cannon_sub = np.sin(sub_phase) * sub_env * 1.25

        # Damascus barrel ring (1080Hz)
        damascus_ring = (
            np.sin(2.0 * np.pi * 1080.0 * tb) * np.exp(-tb * 18.0) * 0.25
            + np.sin(2.0 * np.pi * 1720.0 * tb) * np.exp(-tb * 28.0) * 0.14
        )

        barrel_blast = time_varying_air_damping(buckshot_rip + dragon_roar + cannon_sub + damascus_ring, transient_ms=6.5)
        mono[idx_b:] += barrel_blast * b_gain

    left, right = stereo_catacomb_acoustics(mono, stereo_width=0.58, sub_tail_wet=0.48, decay_sec=1.40, pan_bias=0.04)
    save_stereo_wav(os.path.join(out_dir, "shotgun_fire_boom.wav"), left, right)


def generate_shotgun_break_open(out_dir: str) -> None:
    """
    shotgun_break_open.wav (0.62s, 2-channel stereo):
    Machined steel top-lever snap (1820Hz), heavy hinged barrel cam drop (1180Hz, scrape=24ms),
    spring extractor kick (2240Hz), and brass hull ring (3180Hz).
    """
    rng = np.random.default_rng(1002)
    dur_s: float = 0.62
    n: int = int(dur_s * SAMPLE_RATE)
    mono = np.zeros(n, dtype=np.float64)

    events = [
        (0.012, 0.14, 1820.0, 1.24, 46.0, 4.5, 0.88),   # 1. Machined steel top-lever snap (1820Hz)
        (0.115, 0.22, 1180.0, 1.20, 28.0, 24.0, 0.96),  # 2. Heavy hinged barrel cam drop (1180Hz, scrape=24ms)
        (0.285, 0.15, 2240.0, 1.26, 42.0, 6.0, 0.84),   # 3. Spring extractor kick (2240Hz)
        (0.325, 0.20, 3180.0, 1.32, 24.0, 2.0, 0.76),   # 4. Brass hull ring 1 (3180Hz)
        (0.355, 0.20, 3340.0, 1.32, 26.0, 1.8, 0.70),   # 5. Brass hull ring 2
    ]
    for start_t, evt_dur, freq, stiff, dec, scr_ms, gain in events:
        evt = waveguide_steel_impact(evt_dur, freq, stiff, dec, scr_ms, rng)
        _mix_at(mono, evt, start_t, gain=gain)

    left, right = stereo_catacomb_acoustics(mono, stereo_width=0.35, sub_tail_wet=0.22, decay_sec=0.42, pan_bias=0.05)
    save_stereo_wav(os.path.join(out_dir, "shotgun_break_open.wav"), left, right)


def generate_shotgun_shell_load_close(out_dir: str) -> None:
    """
    shotgun_shell_load_close.wav (0.68s, 2-channel stereo):
    Dual shell chamber slides (1640Hz, 1720Hz, scrape=20ms), heavy steel breech slam (1240Hz),
    and top locking bolt snap (2580Hz).
    """
    rng = np.random.default_rng(1003)
    dur_s: float = 0.68
    n: int = int(dur_s * SAMPLE_RATE)
    mono = np.zeros(n, dtype=np.float64)

    events = [
        (0.025, 0.16, 1640.0, 1.23, 38.0, 20.0, 0.80),  # 1. Shell 1 chamber slide (1640Hz, scrape=20ms)
        (0.155, 0.16, 1720.0, 1.24, 38.0, 20.0, 0.84),  # 2. Shell 2 chamber slide (1720Hz, scrape=20ms)
        (0.355, 0.22, 1240.0, 1.21, 28.0, 9.0, 1.00),   # 3. Heavy steel breech slam (1240Hz)
        (0.392, 0.16, 2580.0, 1.28, 48.0, 2.5, 0.92),   # 4. Top locking bolt snap (2580Hz)
    ]
    for start_t, evt_dur, freq, stiff, dec, scr_ms, gain in events:
        evt = waveguide_steel_impact(evt_dur, freq, stiff, dec, scr_ms, rng)
        _mix_at(mono, evt, start_t, gain=gain)

    left, right = stereo_catacomb_acoustics(mono, stereo_width=0.36, sub_tail_wet=0.24, decay_sec=0.45, pan_bias=0.05)
    save_stereo_wav(os.path.join(out_dir, "shotgun_shell_load_close.wav"), left, right)


def generate_stakedriver_fire_pneumatic(out_dir: str) -> None:
    """
    stakedriver_fire_pneumatic.wav (1.00s, 2-channel stereo):
    Forged steel anvil slam (1460Hz, stiffness=1.26) + wavefolded pneumatic-combustion midrange bark
    (380Hz-3,200Hz) + 227Hz -> 32Hz piston sub-thump + 2.2kHz-9.5kHz high-pressure steam burst
    + 15 decelerating machined-steel winch ratchet teeth (2450Hz-3125Hz).
    """
    rng = np.random.default_rng(1004)
    dur_s: float = 1.00
    n: int = int(dur_s * SAMPLE_RATE)
    t = np.arange(n, dtype=np.float64) / float(SAMPLE_RATE)
    mono = np.zeros(n, dtype=np.float64)

    # 1. Forged steel anvil slam (1460Hz, stiffness=1.26)
    anvil_slam = waveguide_steel_impact(0.32, 1460.0, 1.26, 28.0, 3.0, rng)
    _mix_at(mono, anvil_slam, 0.0, gain=1.05)

    # 2. Wavefolded pneumatic-combustion midrange bark (380Hz-3,200Hz)
    f_pneu = 62.0 + (210.0 - 62.0) * np.exp(-t * 22.0)
    pneu_phase = 2.0 * np.pi * np.cumsum(f_pneu) / float(SAMPLE_RATE)
    pneu_src = np.sin(pneu_phase) * 0.70 + rng.standard_normal(n) * 0.85
    pneu_bp = _dsp_bandpass(pneu_src, 380.0, 3200.0, order=2)
    pneu_env = (1.0 - np.exp(-t * 920.0)) * np.exp(-t * 13.5)
    pneu_bark = asymmetric_wavefold_growl(pneu_bp * pneu_env, drive=3.1, asym=0.28) * 0.88

    # 3. 227Hz -> 32Hz piston sub-thump
    f_sub = 32.0 + (227.0 - 32.0) * np.exp(-t * 26.0)
    sub_phase = 2.0 * np.pi * np.cumsum(f_sub) / float(SAMPLE_RATE)
    sub_env = (1.0 - np.exp(-t * 750.0)) * np.exp(-t * 8.0)
    piston_sub = np.sin(sub_phase) * sub_env * 1.12

    # 4. 2.2kHz-9.5kHz high-pressure steam burst
    steam_env = (1.0 - np.exp(-t * 180.0)) * np.exp(-t * 6.8)
    steam_burst = _dsp_bandpass(rng.standard_normal(n), 2200.0, 9500.0, order=2) * steam_env * 0.46

    mono += time_varying_air_damping(pneu_bark + piston_sub + steam_burst, transient_ms=6.5)

    # 5. 15 decelerating machined-steel winch ratchet teeth (2450Hz-3125Hz)
    tooth_time: float = 0.085
    for tooth_idx in range(15):
        frac: float = tooth_idx / 14.0
        tooth_freq: float = 3125.0 - (3125.0 - 2450.0) * frac
        tooth_evt = waveguide_steel_impact(0.055, tooth_freq, 1.25, 68.0, 1.2, rng)
        _mix_at(mono, tooth_evt, tooth_time, gain=0.34 * (1.0 - 0.35 * frac))
        tooth_time += 0.024 + 0.036 * (frac ** 1.4)

    left, right = stereo_catacomb_acoustics(mono, stereo_width=0.46, sub_tail_wet=0.36, decay_sec=0.85, pan_bias=0.06)
    save_stereo_wav(os.path.join(out_dir, "stakedriver_fire_pneumatic.wav"), left, right)



def generate_stakedriver_melee_cleave(out_dir: str) -> None:
    """
    stakedriver_melee_cleave.wav: Heavy bladed air-whoosh + serrated steel slash ring.
    """
    rng = random.Random(1005)
    dur = int(0.58 * SAMPLE_RATE)
    samples: list[float] = []
    bp_whoosh = StateVariableBandpass(q=2.0)
    for i in range(dur):
        t = i / float(SAMPLE_RATE)
        white = rng.uniform(-1.0, 1.0)
        whoosh_env = math.sin(min(1.0, t / 0.34) * math.pi) if t < 0.34 else 0.0
        _, whoosh = bp_whoosh.process(white * whoosh_env, 280.0 + 520.0 * math.sin(min(1.0, t / 0.34) * math.pi))
        slash_ring = (
            0.48 * math.sin(t * 2.0 * math.pi * 1640.0) * math.exp(-t * 10.5)
            + 0.34 * math.sin(t * 2.0 * math.pi * 2920.0) * math.exp(-t * 14.0)
        )
        samples.append(whoosh * 0.72 + slash_ring)
    write_wav_mono(os.path.join(out_dir, "stakedriver_melee_cleave.wav"), samples, peak_amp=0.80)


def generate_weapon_swap_holster(out_dir: str) -> None:
    """
    weapon_swap_holster.wav: Quick leather holster draw + metallic safety catch click.
    """
    rng = random.Random(1006)
    dur = int(0.42 * SAMPLE_RATE)
    samples: list[float] = []
    bp_draw = StateVariableBandpass(q=2.5)
    for i in range(dur):
        t = i / float(SAMPLE_RATE)
        white = rng.uniform(-1.0, 1.0)
        draw_env = math.sin(min(1.0, t / 0.24) * math.pi) if t < 0.24 else 0.0
        _, leather_draw = bp_draw.process(white * draw_env, 420.0 + 380.0 * (t / 0.24))
        click: float = 0.0
        if t >= 0.20:
            dtc = t - 0.20
            click = (
                0.52 * math.sin(dtc * 2.0 * math.pi * 2150.0) * math.exp(-dtc * 65.0)
                + 0.38 * math.sin(dtc * 2.0 * math.pi * 1240.0) * math.exp(-dtc * 50.0)
            )
        samples.append(leather_draw * 0.55 + click)
    write_wav_mono(os.path.join(out_dir, "weapon_swap_holster.wav"), samples, peak_amp=0.76)


def generate_enemy_aggro_roar(out_dir: str) -> None:
    """
    enemy_aggro_roar.wav: Deep guttural metallic/hollow crypt roar when spotting the player.
    """
    rng = random.Random(2001)
    dur = int(0.88 * SAMPLE_RATE)
    samples: list[float] = []
    bp_formant = StateVariableBandpass(q=2.8)
    for i in range(dur):
        t = i / float(SAMPLE_RATE)
        white = rng.uniform(-1.0, 1.0)
        env = math.sin(min(1.0, t / 0.88) * math.pi) ** 0.7
        pitch = 92.0 - 26.0 * (t / 0.88) + 8.0 * math.sin(t * 2.0 * math.pi * 24.0)
        growl_osc = (
            0.55 * math.sin(t * 2.0 * math.pi * pitch)
            + 0.35 * math.sin(t * 2.0 * math.pi * pitch * 2.02)
            + 0.25 * math.sin(t * 2.0 * math.pi * pitch * 3.10)
        )
        _, rasp = bp_formant.process(white * env, 340.0 - 110.0 * (t / 0.88))
        samples.append((growl_osc * 0.72 + rasp * 0.55) * env)
    write_wav_mono(os.path.join(out_dir, "enemy_aggro_roar.wav"), samples, peak_amp=0.84)


def generate_enemy_windup_telegraph(out_dir: str) -> None:
    """
    enemy_windup_telegraph.wav: Rising metallic scrape + sinister occult chime (0.5s warning before enemy strike).
    """
    rng = random.Random(2002)
    dur = int(0.50 * SAMPLE_RATE)
    samples: list[float] = []
    bp_scrape = StateVariableBandpass(q=4.0)
    for i in range(dur):
        t = i / float(SAMPLE_RATE)
        white = rng.uniform(-1.0, 1.0)
        prog = t / 0.50
        env = math.sin(prog * math.pi)
        _, scrape = bp_scrape.process(white * env, 720.0 + 1480.0 * prog)
        chime_freq = 540.0 + 660.0 * (prog * prog)
        chime = (
            0.52 * math.sin(t * 2.0 * math.pi * chime_freq)
            + 0.32 * math.sin(t * 2.0 * math.pi * (chime_freq * 1.5))
        ) * env
        samples.append(scrape * 0.45 + chime * 0.70)
    write_wav_mono(os.path.join(out_dir, "enemy_windup_telegraph.wav"), samples, peak_amp=0.82)


def generate_enemy_melee_slash(out_dir: str) -> None:
    """
    enemy_melee_slash.wav: Heavy air-cleave + iron chain rattle.
    """
    rng = random.Random(2003)
    dur = int(0.55 * SAMPLE_RATE)
    samples: list[float] = []
    bp_cleave = StateVariableBandpass(q=2.0)
    for i in range(dur):
        t = i / float(SAMPLE_RATE)
        white = rng.uniform(-1.0, 1.0)
        whoosh_env = math.sin(min(1.0, t / 0.32) * math.pi) if t < 0.32 else 0.0
        _, cleave = bp_cleave.process(white * whoosh_env, 240.0 + 480.0 * whoosh_env)
        chain_rattle = (
            0.35 * math.sin(t * 2.0 * math.pi * 1840.0) * math.exp(-t * 14.0)
            + 0.28 * math.sin(t * 2.0 * math.pi * 2760.0) * math.exp(-t * 18.0)
        )
        samples.append(cleave * 0.75 + chain_rattle)
    write_wav_mono(os.path.join(out_dir, "enemy_melee_slash.wav"), samples, peak_amp=0.82)


def generate_enemy_spell_cast(out_dir: str) -> None:
    """
    enemy_spell_cast.wav: Arcane frequency sweep + crystalline pulse for ranged hex/bile casts.
    """
    dur = int(0.68 * SAMPLE_RATE)
    samples: list[float] = []
    for i in range(dur):
        t = i / float(SAMPLE_RATE)
        env = (1.0 - math.exp(-t * 45.0)) * math.exp(-t * 4.5)
        sweep_hz = 320.0 + 640.0 * math.exp(-t * 5.0)
        crystal = (
            0.48 * math.sin(t * 2.0 * math.pi * sweep_hz)
            + 0.36 * math.sin(t * 2.0 * math.pi * 1320.0 + 2.5 * math.sin(t * 2.0 * math.pi * 18.0))
            + 0.24 * math.sin(t * 2.0 * math.pi * 2180.0)
        )
        samples.append(crystal * env)
    write_wav_mono(os.path.join(out_dir, "enemy_spell_cast.wav"), samples, peak_amp=0.80)


def generate_enemy_sonic_bell_slam(out_dir: str) -> None:
    """
    enemy_sonic_bell_slam.wav: Massive low-end bronze bell shockwave toll (130Hz + 45Hz sub drop).
    """
    rng = random.Random(2005)
    dur = int(1.35 * SAMPLE_RATE)
    samples: list[float] = []
    bp_dust = StateVariableBandpass(q=1.8)
    for i in range(dur):
        t = i / float(SAMPLE_RATE)
        white = rng.uniform(-1.0, 1.0)
        sub_drop = 0.80 * math.sin(t * 2.0 * math.pi * (45.0 + 35.0 * math.exp(-t * 12.0))) * math.exp(-t * 3.8)
        bell_toll = (
            0.65 * math.sin(t * 2.0 * math.pi * 130.0) * math.exp(-t * 2.4)
            + 0.45 * math.sin(t * 2.0 * math.pi * 260.0) * math.exp(-t * 3.2)
            + 0.32 * math.sin(t * 2.0 * math.pi * 392.0) * math.exp(-t * 4.5)
            + 0.22 * math.sin(t * 2.0 * math.pi * 715.0) * math.exp(-t * 6.5)
        )
        _, impact_dust = bp_dust.process(white * math.exp(-t * 14.0), 190.0)
        samples.append(sub_drop + bell_toll * 0.85 + impact_dust * 0.45)
    write_wav_mono(os.path.join(out_dir, "enemy_sonic_bell_slam.wav"), samples, peak_amp=0.90)


def generate_player_hit_hurt(out_dir: str) -> None:
    """
    player_hit_hurt.wav: Visceral armor crunch + low heartbeat thud when the player takes damage.
    """
    rng = random.Random(2006)
    dur = int(0.48 * SAMPLE_RATE)
    samples: list[float] = []
    bp_crunch = StateVariableBandpass(q=2.6)
    for i in range(dur):
        t = i / float(SAMPLE_RATE)
        white = rng.uniform(-1.0, 1.0)
        heartbeat = 0.85 * math.sin(t * 2.0 * math.pi * (62.0 - 18.0 * min(1.0, t * 3.0))) * math.exp(-t * 8.5)
        _, crunch = bp_crunch.process(white * math.exp(-t * 22.0), 680.0)
        plate_ring = 0.38 * math.sin(t * 2.0 * math.pi * 1120.0) * math.exp(-t * 26.0)
        samples.append(heartbeat + crunch * 0.65 + plate_ring)
    write_wav_mono(os.path.join(out_dir, "player_hit_hurt.wav"), samples, peak_amp=0.88)


def generate_ui_grimoire_open(out_dir: str) -> None:
    """
    ui_grimoire_open.wav (0.48s, 2-channel stereo):
    Heavy leather-bound tome unfolding + deep brass clasp unlatching + subtle subterranean choir resonance (220Hz + 330Hz fifth pad).
    """
    rng = np.random.default_rng(3001)
    dur_s: float = 0.48
    n: int = int(dur_s * SAMPLE_RATE)
    t = np.arange(n, dtype=np.float64) / float(SAMPLE_RATE)
    mono = np.zeros(n, dtype=np.float64)

    # 1. Brass clasp unlatching at t = 0.015s
    clasp = waveguide_steel_impact(0.085, 1340.0, 1.24, 38.0, 1.4, rng)
    _mix_at(mono, clasp, 0.015, gain=0.58)

    # 2. Heavy leather-bound tome unfolding & vellum page rustle (bandpass 240Hz-1,400Hz)
    leather_env = np.sin(np.clip(t / 0.36, 0.0, 1.0) * math.pi) * np.exp(-t * 2.8)
    leather_noise = _dsp_bandpass(rng.standard_normal(n), 240.0, 1400.0, order=2) * leather_env * 0.42
    mono += leather_noise

    # 3. Subterranean choir fifth pad resonance (220Hz + 330Hz + 440Hz)
    choir_env = (1.0 - np.exp(-t * 24.0)) * np.exp(-t * 4.5) * np.clip((dur_s - t) / 0.08, 0.0, 1.0)
    vib = 1.0 + 0.004 * np.sin(2.0 * math.pi * 5.2 * t)
    choir = (
        0.38 * np.sin(2.0 * math.pi * 220.0 * vib * t)
        + 0.30 * np.sin(2.0 * math.pi * 330.0 * vib * t)
        + 0.18 * np.sin(2.0 * math.pi * 440.0 * vib * t)
    ) * choir_env
    mono += choir

    left, right = stereo_catacomb_acoustics(mono, stereo_width=0.36, sub_tail_wet=0.22, decay_sec=0.35, pan_bias=0.0)
    save_stereo_wav(os.path.join(out_dir, "ui_grimoire_open.wav"), left, right)


def generate_ui_armor_equip_clank(out_dir: str) -> None:
    """
    ui_armor_equip_clank.wav (0.52s, 2-channel stereo):
    Authoritative forged-steel gauntlet plate lock + leather strap cinch + metallic buckle ring
    (waveguide_steel_impact at 1,650Hz and 2,480Hz).
    """
    rng = np.random.default_rng(3002)
    dur_s: float = 0.52
    n: int = int(dur_s * SAMPLE_RATE)
    t = np.arange(n, dtype=np.float64) / float(SAMPLE_RATE)
    mono = np.zeros(n, dtype=np.float64)

    # 1. Forged-steel gauntlet plate lock at t = 0.01s (1,650Hz) and buckle ring at t = 0.09s (2,480Hz)
    plate_lock = waveguide_steel_impact(0.16, 1650.0, 1.24, 28.0, 1.7, rng)
    buckle_ring = waveguide_steel_impact(0.18, 2480.0, 1.25, 32.0, 1.5, rng)
    _mix_at(mono, plate_lock, 0.01, gain=0.78)
    _mix_at(mono, buckle_ring, 0.09, gain=0.64)

    # 2. Deep armor plate thud (145Hz -> 62Hz) + leather strap cinch (bandpass 380Hz-1,800Hz)
    thud_env = (1.0 - np.exp(-t * 140.0)) * np.exp(-t * 18.0)
    thud = np.sin(2.0 * math.pi * (62.0 + 83.0 * np.exp(-t * 25.0)) * t) * thud_env * 0.65
    strap_env = np.sin(np.clip((t - 0.03) / 0.22, 0.0, 1.0) * math.pi)
    strap = _dsp_bandpass(rng.standard_normal(n), 380.0, 1800.0, order=2) * strap_env * 0.35
    mono += thud + strap

    left, right = stereo_catacomb_acoustics(mono, stereo_width=0.38, sub_tail_wet=0.24, decay_sec=0.38, pan_bias=-0.04)
    save_stereo_wav(os.path.join(out_dir, "ui_armor_equip_clank.wav"), left, right)


def generate_ui_skill_consecrate_chime(out_dir: str) -> None:
    """
    ui_skill_consecrate_chime.wav (0.85s, 2-channel stereo):
    Heavy brass astrolabe gear lock (1,420Hz) + searing wax-seal stamp sizzle + harmonic occult cathedral bell chord
    (440Hz, 660Hz, 880Hz, 1,320Hz shimmering golden decay).
    """
    rng = np.random.default_rng(3003)
    dur_s: float = 0.85
    n: int = int(dur_s * SAMPLE_RATE)
    t = np.arange(n, dtype=np.float64) / float(SAMPLE_RATE)
    mono = np.zeros(n, dtype=np.float64)

    # 1. Brass astrolabe gear lock (1,420Hz)
    gear_lock = waveguide_steel_impact(0.14, 1420.0, 1.24, 34.0, 1.6, rng)
    _mix_at(mono, gear_lock, 0.0, gain=0.72)

    # 2. Searing wax-seal stamp sizzle (high-band 1,600Hz-5,200Hz filtered noise)
    sizzle_env = (1.0 - np.exp(-t * 95.0)) * np.exp(-t * 9.5)
    sizzle = _dsp_bandpass(rng.standard_normal(n), 1600.0, 5200.0, order=2) * sizzle_env * 0.28

    # 3. Harmonic occult cathedral bell chord (440Hz, 660Hz, 880Hz, 1,320Hz shimmering golden decay)
    bell_env = (1.0 - np.exp(-t * 85.0)) * np.exp(-t * 3.4) * np.clip((dur_s - t) / 0.09, 0.0, 1.0)
    shimmer = 1.0 + 0.0045 * np.sin(2.0 * math.pi * 6.5 * t)
    bell_chord = (
        0.44 * np.sin(2.0 * math.pi * 440.0 * shimmer * t)
        + 0.36 * np.sin(2.0 * math.pi * 660.0 * shimmer * t)
        + 0.28 * np.sin(2.0 * math.pi * 880.0 * shimmer * t)
        + 0.20 * np.sin(2.0 * math.pi * 1320.0 * shimmer * t)
    ) * bell_env
    mono += sizzle + bell_chord

    left, right = stereo_catacomb_acoustics(mono, stereo_width=0.44, sub_tail_wet=0.28, decay_sec=0.55, pan_bias=0.0)
    save_stereo_wav(os.path.join(out_dir, "ui_skill_consecrate_chime.wav"), left, right)


def generate_ui_tab_page_turn(out_dir: str) -> None:
    """
    ui_tab_page_turn.wav (0.28s, 2-channel stereo):
    Crisp parchment vellum rustle + metallic index tab click.
    """
    rng = np.random.default_rng(3004)
    dur_s: float = 0.28
    n: int = int(dur_s * SAMPLE_RATE)
    t = np.arange(n, dtype=np.float64) / float(SAMPLE_RATE)
    mono = np.zeros(n, dtype=np.float64)

    # 1. Metallic index tab click at t = 0.008s
    tab_click = waveguide_steel_impact(0.055, 2240.0, 1.25, 58.0, 1.3, rng)
    _mix_at(mono, tab_click, 0.008, gain=0.52)

    # 2. Crisp parchment vellum rustle (bandpass 650Hz-4,200Hz)
    rustle_env = np.sin(np.clip(t / 0.22, 0.0, 1.0) * math.pi) * np.exp(-t * 5.5)
    rustle = _dsp_bandpass(rng.standard_normal(n), 650.0, 4200.0, order=2) * rustle_env * 0.48
    mono += rustle

    left, right = stereo_catacomb_acoustics(mono, stereo_width=0.32, sub_tail_wet=0.16, decay_sec=0.22, pan_bias=0.02)
    save_stereo_wav(os.path.join(out_dir, "ui_tab_page_turn.wav"), left, right)


def generate_hunter_quickstep_dash(out_dir: str) -> None:
    """
    hunter_quickstep_dash.wav (0.38s, 2-channel stereo):
    Sharp leather-coat whip + boot-scuff push-off + low ethereal shadow-wind whoosh
    (180Hz-1,400Hz band-passed noise sweep with stereo Haas widening).
    """
    rng = np.random.default_rng(3005)
    dur_s: float = 0.38
    n: int = int(dur_s * SAMPLE_RATE)
    t = np.arange(n, dtype=np.float64) / float(SAMPLE_RATE)
    mono = np.zeros(n, dtype=np.float64)

    # 1. Boot-scuff stone push-off & low sub-impulse (125Hz -> 44Hz)
    scuff_env = (1.0 - np.exp(-t * 480.0)) * np.exp(-t * 28.0)
    scuff_sub = np.sin(2.0 * np.pi * (44.0 + 81.0 * np.exp(-t * 32.0)) * t) * scuff_env * 0.72
    scuff_grit = _dsp_bandpass(rng.standard_normal(n), 420.0, 2400.0, order=2) * scuff_env * 0.45

    # 2. Sharp leather-coat whip snap at t = 0.018s..0.14s
    whip_env = np.sin(np.clip((t - 0.012) / 0.12, 0.0, 1.0) * math.pi) ** 1.3 * np.exp(-np.maximum(0.0, t - 0.012) * 14.0)
    whip_noise = _dsp_bandpass(rng.standard_normal(n), 680.0, 3800.0, order=2) * whip_env * 0.56
    buckle_tick = waveguide_steel_impact(0.06, 2180.0, 1.24, 52.0, 1.3, rng)
    _mix_at(mono, buckle_tick, 0.022, gain=0.36)

    # 3. Low ethereal shadow-wind whoosh (180Hz-1,400Hz band-passed noise sweep + ghostly 196Hz/294Hz chord)
    whoosh_env = np.sin(np.clip(t / 0.34, 0.0, 1.0) * math.pi) * np.exp(-t * 3.8)
    shadow_wind_low = _dsp_bandpass(rng.standard_normal(n), 180.0, 620.0, order=2) * whoosh_env * 0.68
    shadow_wind_high = _dsp_bandpass(rng.standard_normal(n), 420.0, 1400.0, order=2) * (whoosh_env ** 1.4) * 0.52
    ethereal_hum = (
        0.22 * np.sin(2.0 * np.pi * (196.0 - 24.0 * (t / dur_s)) * t)
        + 0.16 * np.sin(2.0 * np.pi * (294.0 - 36.0 * (t / dur_s)) * t)
    ) * whoosh_env

    mono += scuff_sub + scuff_grit + whip_noise + shadow_wind_low + shadow_wind_high + ethereal_hum

    # Stereo Haas widening (0.65ms inter-aural delay + wide catacomb acoustics)
    left, right = stereo_catacomb_acoustics(mono, stereo_width=0.58, sub_tail_wet=0.26, decay_sec=0.28, pan_bias=0.0)
    haas_shift: int = int(0.00065 * SAMPLE_RATE)
    if haas_shift > 0 and haas_shift < n:
        right_delayed = np.zeros_like(right)
        right_delayed[haas_shift:] = right[:-haas_shift]
        right = 0.72 * right_delayed + 0.28 * left
    save_stereo_wav(os.path.join(out_dir, "hunter_quickstep_dash.wav"), left, right)


if __name__ == "__main__":
    ambient_dir = os.path.join("assets", "audio", "ambient")
    sfx_dir = os.path.join("assets", "audio", "sfx")
    generate_ambient_moor_wind_loop(ambient_dir)
    generate_ambient_church_draft_loop(ambient_dir)
    generate_ambient_crypt_drone_loop(ambient_dir)
    generate_torch_fire_loop(sfx_dir)
    generate_footsteps(sfx_dir)
    generate_crypt_water_drips(sfx_dir)
    generate_cathedral_bell_distant(sfx_dir)
    generate_crypt_stone_settle(sfx_dir)
    generate_hub_anvil_upgrade(sfx_dir)
    generate_hub_armor_equip(sfx_dir)
    generate_hub_weapon_mod(sfx_dir)
    generate_hub_sanctuary_heal(sfx_dir)
    generate_portal_hum_loop(sfx_dir)
    generate_portal_warp_enter(sfx_dir)
    generate_loot_drop_spawn(sfx_dir)
    generate_loot_pickup_chime(sfx_dir)
    generate_rpg_level_up_fanfare(sfx_dir)
    generate_ability_lantern_pyre_blast(sfx_dir)
    generate_ability_lantern_soul_chains(sfx_dir)
    generate_ability_lantern_blood_nova(sfx_dir)
    generate_revolver_fire(sfx_dir)
    generate_revolver_cock_click(sfx_dir)
    generate_revolver_reload(sfx_dir)
    generate_revolver_dry_fire(sfx_dir)
    generate_shotgun_fire_boom(sfx_dir)
    generate_shotgun_break_open(sfx_dir)
    generate_shotgun_shell_load_close(sfx_dir)
    generate_stakedriver_fire_pneumatic(sfx_dir)
    generate_stakedriver_melee_cleave(sfx_dir)
    generate_weapon_swap_holster(sfx_dir)
    generate_enemy_aggro_roar(sfx_dir)
    generate_enemy_windup_telegraph(sfx_dir)
    generate_enemy_melee_slash(sfx_dir)
    generate_enemy_spell_cast(sfx_dir)
    generate_enemy_sonic_bell_slam(sfx_dir)
    generate_player_hit_hurt(sfx_dir)
    generate_ui_grimoire_open(sfx_dir)
    generate_ui_armor_equip_clank(sfx_dir)
    generate_ui_skill_consecrate_chime(sfx_dir)
    generate_ui_tab_page_turn(sfx_dir)
    generate_hunter_quickstep_dash(sfx_dir)
    print("[Audio] All ambient loops, footsteps, horror SFX, Hub SFX, Portal SFX, RPG/Ability SFX, Multi-Weapon SFX, Enemy Combat SFX, Gothic UI SFX, and Hunter Quickstep Dash SFX generated successfully.")
