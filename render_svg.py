def labels_for_bar(numerator, denominator):
    if denominator == 8:
        labels = []
        groups = numerator // 3
        for group in range(1, groups + 1):
            labels.extend([str(group), "pl", "let"])
        return labels

    if denominator == 4:
        units = 4
    elif denominator == 8:
        units = 2
    else:
        units = 4

    labels = []
    for beat in range(1, numerator + 1):
        if units == 4:
            labels.extend([str(beat), "e", "+", "a"])
        else:
            labels.extend([str(beat), "+"])
    return labels

def render_bar_svg(
    bar_steps,
    labels,
    units_per_beat,
    denominator,
    is_last_bar=False,
    show_inactive_labels=True,
    annotations=None,
    width=720,
    height=120,
):
    steps_per_bar = len(bar_steps)
    if steps_per_bar == 0:
        return ""

    # Trim trailing empty quarter-note groups only on the final bar
    if denominator == 4 and is_last_bar:
        group_size = 4
        trimmed_steps = list(bar_steps)
        while len(trimmed_steps) >= group_size:
            tail = trimmed_steps[-group_size:]
            if any(step.get("active") for step in tail):
                break
            trimmed_steps = trimmed_steps[:-group_size]

        if not trimmed_steps:
            return ""

        bar_steps = trimmed_steps
        steps_per_bar = len(bar_steps)

    left_margin = 0
    right_margin = 0
    bar_draw_width = width - left_margin - right_margin

    staff_y1 = 20
    staff_y2 = 35
    stem_top = staff_y2
    stem_bottom = 70
    note_y = 75
    label_y = 100

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">'
    ]
    svg.append(
        f'<line x1="{left_margin}" y1="{staff_y1 - 2}" '
        f'x2="{left_margin}" y2="{stem_bottom + 5}" '
        f'stroke="#111" stroke-width="2" />'
    )
    # Decide whether labels map 1:1 to steps or need grouping
    label_count = len(labels)
    use_label_grid = label_count == steps_per_bar
    label_group_size = 1
    if not use_label_grid and label_count and steps_per_bar % label_count == 0:
        group_size = steps_per_bar // label_count
        label_group_size = group_size
        visual_steps = []
        for i in range(0, steps_per_bar, group_size):
            group = bar_steps[i : i + group_size]
            visual_steps.append(any(step.get("active") for step in group))
    else:
        visual_steps = [step.get("active") for step in bar_steps]
        use_label_grid = True

    visual_count = len(visual_steps)
    step_width = bar_draw_width / visual_count
    render_limit = visual_count
    # For compound meters, shrink rendering to the last active group
    if denominator == 8:
        last_active_group = -1
        for gi in range(0, visual_count, 3):
            group = visual_steps[gi : gi + 3]
            if any(group):
                last_active_group = gi // 3
        if last_active_group == -1:
            return ""
        render_limit = (last_active_group + 1) * 3

    # In /4, render beamed noteheads and per-group separators
    if denominator == 4:
        beam_top_y = staff_y2
        beam_second_y = staff_y2 + 6
        beam_thickness = 3
        dot_radius = 2
        dot_offset = 12
        separator_width = 1

        def x_for_pos(pos):
            return left_margin + (pos + 0.5) * step_width

        def add_beam(y, start_pos, end_pos):
            x1 = x_for_pos(start_pos)
            x2 = x_for_pos(end_pos)
            if x2 < x1:
                x1, x2 = x2, x1
            svg.append(
                f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" '
                f'stroke="#111" stroke-width="{beam_thickness}" />'
            )

        def add_short_beam(y, start_pos):
            x1 = x_for_pos(start_pos)
            x2 = x1 + step_width * 0.25
            y2 = y + 2
            svg.append(
                f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y2}" '
                f'stroke="#111" stroke-width="{beam_thickness}" />'
            )

        def add_dot(step_index):
            x = x_for_pos(step_index)
            svg.append(
                f'<circle cx="{x + dot_offset}" cy="{note_y}" r="{dot_radius}" fill="#111" />'
            )

        pattern_map = {
            "1100": {"top": [(0, 1)], "second": [(0, 0.25)], "dots": [1]},
            "1010": {"top": [(0, 2)], "second": [], "dots": []},
            "1001": {"top": [(0, 3)], "second": [(3, 2.5)], "dots": [0]},
            "0110": {"top": [(1, 2)], "second": [(1, 1.25)], "dots": []},
            "0101": {"top": [], "second": [], "dots": []},
            "0011": {"top": [(2, 3)], "second": [(2, 3)], "dots": []},
            "1110": {"top": [(0, 2)], "second": [(0, 1)], "dots": []},
            "1101": {"top": [(0, 3)], "second": [(0, 0.25), (3, 2.75)], "dots": []},
            "1011": {"top": [(0, 3)], "second": [(2, 3)], "dots": []},
            "0111": {"top": [(1, 3)], "second": [(1, 3)], "dots": []},
            "1111": {"top": [(0, 3)], "second": [(0, 3)], "dots": []},
            "0100": {"top": [(1, 1.15)], "second":[], "dots":[1]},
            "0010": {"top": [(2, 2.15)], "second":[], "dots": []}
        }

        for g in range(0, steps_per_bar, 4):
            group = bar_steps[g : g + 4]
            if len(group) < 4:
                break
            if g + 4 < steps_per_bar:
                boundary_x = left_margin + (g + 4) * step_width
                svg.append(
                    f'<line x1="{boundary_x}" y1="{stem_top}" '
                    f'x2="{boundary_x}" y2="{stem_bottom}" '
                    f'stroke="#111" stroke-width="{separator_width}" />'
                )
            pattern = "".join("1" if step.get("active") else "0" for step in group)
            if pattern in ("0101", "0001"):
                for idx, step in enumerate(group):
                    if step.get("active"):
                        add_short_beam(beam_top_y, g + idx)
                        add_short_beam(beam_second_y, g + idx)
                continue
            if pattern.count("1") <= 1 and pattern not in pattern_map:
                continue
            beams = pattern_map.get(pattern, {"top": [], "second": [], "dots": []})
            for start, end in beams["top"]:
                add_beam(beam_top_y, g + start, g + end)
            for start, end in beams["second"]:
                add_beam(beam_second_y, g + start, g + end)
            for idx in beams["dots"]:
                add_dot(g + idx)
    else:
        staff_group = 3
        separator_width = 1
        for g in range(0, render_limit, staff_group):
            start_x = left_margin + g * step_width + step_width / 2
            end_index = min(g + staff_group - 1, render_limit - 1)
            end_x = left_margin + end_index * step_width + step_width / 2
            svg.append(
                f'<line x1="{start_x}" y1="{staff_y2}" '
                f'x2="{end_x}" y2="{staff_y2}" stroke="#111" />'
            )
            if g + staff_group < render_limit:
                boundary_x = left_margin + (g + staff_group) * step_width
                svg.append(
                    f'<line x1="{boundary_x}" y1="{stem_top}" '
                    f'x2="{boundary_x}" y2="{stem_bottom}" '
                    f'stroke="#111" stroke-width="{separator_width}" />'
                )
    if annotations:
        bracket_y = staff_y2 - 18
        bracket_cap = 6
        for span in annotations:
            start = span["start"]
            end = span["end"]
            label = span["label"]
            if not use_label_grid and label_group_size > 1:
                start = start // label_group_size
                end = end // label_group_size
            if start >= render_limit:
                continue
            if end < 0:
                continue
            start = max(0, start)
            end = min(render_limit - 1, end)
            if end < start:
                continue
            x1 = left_margin + (start + 0.5) * step_width
            x2 = left_margin + (end + 0.5) * step_width
            svg.append(
                f'<line x1="{x1}" y1="{bracket_y}" x2="{x2}" y2="{bracket_y}" '
                f'stroke="#111" stroke-width="1" />'
            )
            svg.append(
                f'<line x1="{x1}" y1="{bracket_y}" x2="{x1}" y2="{bracket_y + bracket_cap}" '
                f'stroke="#111" stroke-width="1" />'
            )
            svg.append(
                f'<line x1="{x2}" y1="{bracket_y}" x2="{x2}" y2="{bracket_y + bracket_cap}" '
                f'stroke="#111" stroke-width="1" />'
            )
            svg.append(
                f'<text x="{(x1 + x2) / 2}" y="{bracket_y - 2}" font-size="16" '
                f'text-anchor="middle" fill="#111">{label}</text>'
            )
    # Draw stems/flags or inactive markers, then optional labels
    for i, is_active in enumerate(visual_steps[:render_limit]):
        x = left_margin + i * step_width + step_width / 2
        stroke_width = 2 if use_label_grid and i % units_per_beat == 0 else 2

        if is_active:
            svg.append(
                f'<line x1="{x}" y1="{stem_top}" x2="{x}" y2="{stem_bottom}" '
                f'stroke="#111" stroke-width="{stroke_width}" />'
            )
            svg.append(
                f'<ellipse cx="{x - 4}" cy="{note_y}" rx="6" ry="4" fill="#111" />'
            )
        else:
            skip_inactive = False
            label = labels[i] if label_count and i < label_count else ""
            if denominator == 4 and use_label_grid:
                group_start = (i // 4) * 4
                group_end = group_start + 3
                if group_end < steps_per_bar:
                    group = bar_steps[group_start : group_start + 4]
                    pattern = "".join("1" if step.get("active") else "0" for step in group)
                    idx_in_group = i - group_start
                    skip_map = {
                        "1001": {1, 2},
                        "1010": {1, 3},
                        "1101": {2},
                        "0100": {2, 3},
                        "0010": {1, 3},
                        "0011": {1},
                        "1100": {3},
                        "1110": {3},
                        "1000": {1, 2, 3}
                    }
                    if idx_in_group in skip_map.get(pattern, set()):
                        skip_inactive = True

                    single_flag_map = {
                        "0010": {0},
                        "0011": {0},
                        "1100": {2}
                    }
                    single_flag = idx_in_group in single_flag_map.get(pattern, set())

                if not skip_inactive and label == "e":
                    if i - 1 >= group_start and i + 1 <= group_end:
                        if bar_steps[i - 1].get("active") and bar_steps[i + 1].get("active"):
                            skip_inactive = True

            if not skip_inactive:
                stem_height = stem_bottom - stem_top
                shrink = stem_height * 0.25
                short_top = stem_top + shrink
                short_bottom = stem_bottom - shrink
                tilt = step_width * 0.06
                svg.append(
                    f'<line x1="{x + tilt}" y1="{short_top}" x2="{x - tilt}" y2="{short_bottom}" '
                    f'stroke="#111" stroke-width="{stroke_width}" />'
                )
                flag_len = step_width * 0.25
                flag_end = x + tilt - 1
                flag_start = flag_end - flag_len
                svg.append(
                    f'<line x1="{flag_start}" y1="{short_top}" x2="{flag_end}" y2="{short_top}" '
                    f'stroke="#111" stroke-width="{stroke_width}" />'
                )
                if not (denominator == 4 and use_label_grid and single_flag):
                    svg.append(
                        f'<line x1="{flag_start}" y1="{short_top + 4}" x2="{flag_end}" y2="{short_top + 4}" '
                        f'stroke="#111" stroke-width="{stroke_width}" />'
                    )

        if label_count and i < label_count:
            label = labels[i]
            if label and (show_inactive_labels or is_active):
                svg.append(
                    f'<text x="{x}" y="{label_y}" font-size="18" '
                    f'text-anchor="middle" fill="#333">{label}</text>'
                )

    barline_x = width - right_margin
    if denominator == 8:
        barline_x = left_margin + render_limit * step_width
    svg.append(
        f'<line x1="{barline_x}" y1="{staff_y1 - 2}" '
        f'x2="{barline_x}" y2="{stem_bottom + 5}" '
        f'stroke="#111" stroke-width="2" />'
    )

    svg.append("</svg>")
    return "".join(svg)
