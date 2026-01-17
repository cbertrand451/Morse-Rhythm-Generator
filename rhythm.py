# DEFINE TIMINGS HERE (For future use)
DOT = 1
DASH = 2
INTRA_SYMBOL_GAP = 0
LETTER_GAP = 1
WORD_GAP = 3


def timing_scale(numerator, denominator):
    # /8 uses a larger unit scale for timing math
    if denominator == 8:
        return 2
    return 1


def morse_to_events(morse, unit_scale=1):
    # Convert tokens to note/rest events with durations in "units"
    events = []
    dot_len = DOT * unit_scale
    dash_total = DASH * unit_scale
    dash_play = DOT * unit_scale
    dash_rest = max(dash_total - dash_play, 0)
    intra_gap = INTRA_SYMBOL_GAP * unit_scale
    letter_gap = LETTER_GAP * unit_scale
    word_gap = WORD_GAP * unit_scale
    # creates indexed list of letters and spaces in the morse
    for i, token in enumerate(morse):
        token_type = token["type"]
        if token_type != "letter":
            continue
        
        # Gets the rhythm of each token
        pattern = token.get("value", "")
        # creates indexed list of each "hit" taking place
        for si, symbol in enumerate(pattern):
            if symbol == ".":
                events.append({"type": "note", "duration": dot_len, "source": "."})
            elif symbol == "-":
                events.append({"type": "note", "duration": dash_play, "source": "-"})
                if dash_rest:
                    events.append(
                        {"type": "rest", "duration": dash_rest, "source": "dash_rest"}
                    )
            if si < len(pattern) - 1:
                events.append(
                    {"type": "rest", "duration": intra_gap, "source": "gap"}
                )

        next_type = None
        if i + 1 < len(morse):
            next_type = morse[i + 1]["type"]

        if next_type == "letter_gap":
            events.append({"type": "rest", "duration": letter_gap, "source": "gap"})
        elif next_type == "word_gap":
            events.append({"type": "rest", "duration": word_gap, "source": "gap"})

    return events


def morse_to_events_with_spans(morse, unit_scale=1):
    # Same as morse_to_events, but also track spans per character
    events = []
    spans = []
    current = 0
    dot_len = DOT * unit_scale
    dash_total = DASH * unit_scale
    dash_play = DOT * unit_scale
    dash_rest = max(dash_total - dash_play, 0)
    intra_gap = INTRA_SYMBOL_GAP * unit_scale
    letter_gap = LETTER_GAP * unit_scale
    word_gap = WORD_GAP * unit_scale

    for i, token in enumerate(morse):
        token_type = token["type"]
        if token_type != "letter":
            continue

        start = current
        pattern = token.get("value", "")
        for si, symbol in enumerate(pattern):
            if symbol == ".":
                events.append({"type": "note", "duration": dot_len, "source": "."})
                current += dot_len
            elif symbol == "-":
                events.append({"type": "note", "duration": dash_play, "source": "-"})
                current += dash_play
                if dash_rest:
                    events.append(
                        {"type": "rest", "duration": dash_rest, "source": "dash_rest"}
                    )
                    current += dash_rest
            if si < len(pattern) - 1 and intra_gap:
                events.append({"type": "rest", "duration": intra_gap, "source": "gap"})
                current += intra_gap

        end = current - 1 if current > start else start
        spans.append(
            {
                "start": start,
                "end": end,
                "label": token.get("char", "?"),
            }
        )

        next_type = None
        if i + 1 < len(morse):
            next_type = morse[i + 1]["type"]

        if next_type == "letter_gap":
            events.append({"type": "rest", "duration": letter_gap, "source": "gap"})
            current += letter_gap
        elif next_type == "word_gap":
            events.append({"type": "rest", "duration": word_gap, "source": "gap"})
            current += word_gap

    return events, spans


def events_to_steps(events):
    # Expand events into step-by-step grid entries
    steps = []
    for event in events:
        duration = int(event["duration"])
        if event["type"] == "note":
            for i in range(duration):
                steps.append(
                    {
                        "active": True,
                        "kind": "note",
                        "meta": {"is_onset": i == 0},
                    }
                )
        else:
            for _ in range(duration):
                steps.append({"active": False, "kind": "rest", "meta": None})
    return steps


def split_into_bars(steps, bar_units):
    # Pad the grid to full bars, then slice into bar-sized chunks
    if not steps:
        return []
    if bar_units <= 0:
        return []

    padded = list(steps)
    remainder = len(padded) % bar_units
    if remainder:
        pad_count = bar_units - remainder
        for _ in range(pad_count):
            padded.append({"active": False, "kind": "rest", "meta": None})

    bars = []
    for i in range(0, len(padded), bar_units):
        bars.append(padded[i : i + bar_units])
    return bars


def units_per_beat(denominator):
    # Grid resolution for labels per beat
    if denominator == 4:
        return 4
    if denominator == 8:
        return 2
    return 4
