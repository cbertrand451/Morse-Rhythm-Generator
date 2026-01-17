import re
import logging
import streamlit as st

from morse import text_to_morse
from rhythm import (
    events_to_steps,
    morse_to_events_with_spans,
    split_into_bars,
    timing_scale,
    units_per_beat,
)
from render_svg import labels_for_bar, render_bar_svg
from utils import sanitize_text, load_css
from components import build_morse_metronome_wave, wav_bytes_from_audio


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)


logger = logging.getLogger("morse_rhythm")


def format_morse_tokens(tokens):
    parts = []
    for token in tokens:
        if token["type"] == "letter":
            parts.append(token["value"])
        elif token["type"] == "letter_gap":
            parts.append("/")
        elif token["type"] == "word_gap":
            parts.append("|")
    return " ".join(parts)

# Load shared CSS before any UI elements render
load_css("styles/app.css")
load_css("styles/textarea.css")

st.set_page_config(page_title="Morse Rhythm Generator", layout="wide")
st.title("Morse Rhythm Generator")
st.markdown("Convert text into rhythms")

SVG_WIDTH = 720
SVG_HEIGHT = 120

st.markdown("""
<div style="
    width: 100%;
    height: 1px;
    background-color: #5E6973;
    margin: 1.5rem 0;
"></div>
""", unsafe_allow_html=True)

# Left column handles inputs and right column is morse ouput
text_c, morse_c = st.columns([1.6, 3])
with text_c:
    text = st.text_input("Enter text", value="", key="test")
    time_sig = st.radio(
        "Time signature",
        ["4/4", "12/8"],
        # ["3/4", "4/4", "5/4", "6/4", "7/4", "6/8", "9/8", "12/8"],
        horizontal=True
    )
    numerator, denominator = (int(part) for part in time_sig.split("/"))
    show_inactive_labels = st.checkbox("Show all counts (1 e + a)", value=True)
    st.caption("Without this, only the notes being played have counts beneath them.")
    show_char_brackets = st.checkbox("Show individual characters", value=True)
    st.caption("This allows you to see the exact notes that are being played for each letter/character.")

    # Normalize input so other functions never sees None
    clean_text = sanitize_text(text)
    tokens = text_to_morse(clean_text)
    scale = timing_scale(numerator, denominator)
    events, spans = morse_to_events_with_spans(tokens, unit_scale=scale)
    steps = events_to_steps(events)

    units = units_per_beat(denominator)
    bar_units = numerator * units
    bars = split_into_bars(steps, bar_units)
    labels = labels_for_bar(numerator, denominator)


    if not clean_text.strip():
        st.info("Enter text to generate a Morse rhythm.")
    else:
        qs = '"'
        st.html(
            f"""
            <div style="
                display: flex;
                justify-content: center;
                align-items: baseline;
                gap: 0.5rem;
            ">
                <h2 style="margin: 0;">Morse Code for {qs}</h2>
                <h2 style="margin: 0; color: #C5A572;">{text.upper()}</h2>
                <h2 style='margin: 0;'>{qs}</h2>
            </div>
            """,
        )

        st.html(f"<h1 style='text-align: center;'>{format_morse_tokens(tokens)}</h1>")
        #st.caption("**/** denotes space between letters and **|** denotes space between words")
    
    st.markdown("""
        <div style="
        width: 100%;
        height: 1px;
        background-color: #5E6973;
        margin: 1.5rem 0;
        "></div>
    """, unsafe_allow_html=True)

    vals = []
    for i in range(60, 181, 5):
        vals.append(i)
    bpm = st.select_slider("Select a tempo (bpm):", options=vals)
    metronome_on = st.checkbox("Metronome click", value=True)

    if clean_text.strip():
        log_payload = {
            "text": clean_text,
            "time_signature": time_sig,
            "show_inactive_labels": show_inactive_labels,
            "show_char_brackets": show_char_brackets,
            "metronome_on": metronome_on,
            "tempo_bpm": bpm,
        }
        if st.session_state.get("last_log_payload") != log_payload:
            logger.info(
                "user_input text=%s time_signature=%s show_inactive_labels=%s "
                "show_char_brackets=%s metronome_on=%s tempo_bpm=%s",
                clean_text,
                time_sig,
                show_inactive_labels,
                show_char_brackets,
                metronome_on,
                bpm,
            )
            st.session_state["last_log_payload"] = log_payload

    if clean_text.strip():
        audio, sample_rate = build_morse_metronome_wave(
            clean_text,
            bpm,
            time_sig=time_sig,
            metronome_enabled=metronome_on,
        )
        wav_bytes = wav_bytes_from_audio(audio, sample_rate)
        if wav_bytes:
            st.audio(wav_bytes, format="audio/wav")
    st.caption("Audio will start with a one measure countoff")

with morse_c:
    if not bars:
        st.stop()
    else:
        qs = '"'
        st.html(f"<h2 style='text-align:center;'>{qs}{text.upper()}{qs} in {time_sig}</h2>")
        last_index = len(bars) - 1
        svg_rows = []
        svg_list = []
        # Render each bar as a separate SVG row
        for idx, bar_steps in enumerate(bars):
            bar_start = idx * bar_units
            bar_end = bar_start + bar_units - 1
            bar_spans = []
            if show_char_brackets:
                for span in spans:
                    if span["end"] < bar_start or span["start"] > bar_end:
                        continue
                    bar_spans.append(
                            {
                                "start": span["start"] - bar_start,
                                "end": span["end"] - bar_start,
                                "label": span["label"],
                            }
                    )
            svg = render_bar_svg(
                bar_steps,
                labels,
                units,
                denominator,
                is_last_bar=idx == last_index,
                show_inactive_labels=show_inactive_labels,
                annotations=bar_spans if show_char_brackets else None,
                width=SVG_WIDTH,
                height=SVG_HEIGHT,
            )
            svg_rows.append(f'<div class="svg-row">{svg}</div>')
            svg_list.append(svg)
        st.markdown(
            f'<div class="svg-frame">{"".join(svg_rows)}</div>',
            unsafe_allow_html=True,
        )
        

# 6F9CEB
# FB8B24
# 6F9CEB

# Footer
st.markdown("""
<style>
/* Make page a flex container */
.main {
    display: flex;
    flex-direction: column;
    min-height: 100vh;
}

/* Push footer to bottom */
footer {
    margin-top: auto;
}

/* Footer styling */
.app-footer {
    text-align: center;
    padding: 0.75rem;
    font-size: 0.85rem;
    color: #6b7280;
    border-top: 1px solid #5E6973;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<footer>
  <div class="app-footer">
    © 2026 · Built with Streamlit · Colin Bertrand
  </div>
</footer>
""", unsafe_allow_html=True)
