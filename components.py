import wave
from io import BytesIO

import numpy as np

from morse import text_to_morse


def _sine_wave(freq_hz, duration_s, sample_rate):
    samples = int(sample_rate * duration_s)
    if samples <= 0:
        return np.zeros(0, dtype=np.float32)
    t = np.linspace(0, duration_s, samples, endpoint=False)
    return np.sin(2 * np.pi * freq_hz * t)


def _morse_grid(tokens):
    grid = []
    for i, token in enumerate(tokens):
        if token["type"] != "letter":
            continue
        pattern = token.get("value", "")
        for si, symbol in enumerate(pattern):
            if symbol == ".":
                grid.extend([1])
            elif symbol == "-":
                grid.extend([1, 0, 0])
            if si < len(pattern) - 1:
                grid.extend([0])

        next_type = None
        if i + 1 < len(tokens):
            next_type = tokens[i + 1]["type"]
        if next_type == "letter_gap":
            grid.extend([0, 0, 0])
        elif next_type == "word_gap":
            grid.extend([0, 0, 0, 0, 0, 0, 0])
    return grid


def build_morse_metronome_wave(
    text,
    bpm,
    time_sig="4/4",
    metronome_enabled=True,
    sample_rate=44100,
    morse_freq=620,
    click_freq=1400,
):
    tokens = text_to_morse(text)
    grid = _morse_grid(tokens)
    if not grid:
        return np.zeros(0, dtype=np.int16), sample_rate

    unit_duration = 7.5 / bpm
    unit_samples = int(sample_rate * unit_duration)
    if unit_samples <= 0:
        return np.zeros(0, dtype=np.int16), sample_rate

    numerator, denominator = (int(part) for part in time_sig.split("/"))
    group_units = 8
    groups_per_bar = numerator
    if denominator == 8:
        group_units = 6
        groups_per_bar = max(numerator // 3, 1)
    count_in_units = group_units * groups_per_bar

    total_samples = unit_samples * (count_in_units + len(grid))
    morse_layer = np.zeros(total_samples, dtype=np.float32)
    tone = _sine_wave(morse_freq, unit_duration, sample_rate)
    if len(tone) != unit_samples:
        tone = tone[:unit_samples]
        if len(tone) < unit_samples:
            tone = np.pad(tone, (0, unit_samples - len(tone)))

    morse_offset = count_in_units * unit_samples
    for i, active in enumerate(grid):
        if not active:
            continue
        start = morse_offset + (i * unit_samples)
        morse_layer[start : start + unit_samples] += tone

    mix = morse_layer

    if metronome_enabled:
        click_samples = max(1, min(int(unit_samples * 0.25), int(sample_rate * 0.03)))
        click = np.zeros(unit_samples, dtype=np.float32)
        click_wave = _sine_wave(click_freq, click_samples / sample_rate, sample_rate)
        if len(click_wave) != click_samples:
            click_wave = click_wave[:click_samples]
            if len(click_wave) < click_samples:
                click_wave = np.pad(
                    click_wave, (0, click_samples - len(click_wave))
                )
        click[:click_samples] = click_wave

        metronome_layer = np.zeros(total_samples, dtype=np.float32)
        total_units = count_in_units + len(grid)
        for i in range(total_units):
            if i % group_units != 0:
                continue
            start = i * unit_samples
            metronome_layer[start : start + unit_samples] += click

        mix = morse_layer + metronome_layer

    peak = np.max(np.abs(mix)) if mix.size else 0
    if peak > 0:
        mix = mix / peak * 0.9

    audio = (mix * 32767).astype(np.int16)
    return audio, sample_rate


def wav_bytes_from_audio(audio, sample_rate):
    if audio.size == 0:
        return b""
    buffer = BytesIO()
    with wave.open(buffer, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio.tobytes())
    return buffer.getvalue()
