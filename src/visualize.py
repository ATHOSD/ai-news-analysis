from __future__ import annotations

import html
from collections import Counter
from pathlib import Path
from typing import Any


PALETTE = ["#2563eb", "#0891b2", "#16a34a", "#f59e0b", "#ef4444", "#7c3aed", "#db2777"]


def generate_visualizations(events: list[dict[str, Any]], output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    sorted_events = sort_events(events)

    figures = [
        output_dir / "event_type_distribution.svg",
        output_dir / "topic_distribution.svg",
        output_dir / "importance_ranking.svg",
        output_dir / "signal_counts.svg",
    ]

    write_bar_chart(
        figures[0],
        "Event Type Distribution",
        count_values(event["event_type"] for event in sorted_events),
        x_label="Events",
    )
    write_bar_chart(
        figures[1],
        "Topic Distribution",
        count_values(event["topic"] for event in sorted_events),
        x_label="Events",
    )
    write_bar_chart(
        figures[2],
        "Top Event Importance Ranking",
        [
            (shorten_display(event["event_name"], 40), event["importance"]["total_score"])
            for event in sorted_events[:10]
        ],
        x_label="Importance Score",
        width=1160,
        left=470,
    )
    write_bar_chart(
        figures[3],
        "Risk And Opportunity Signals",
        count_values(signal for event in sorted_events for signal in event.get("signals", [])),
        x_label="Mentions",
    )
    return figures


def sort_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        events,
        key=lambda event: (
            event["importance"]["total_score"],
            event["importance"]["urgency_score"],
            event["importance"]["impact_score"],
            len(event["source_news_ids"]),
            event["event_date"],
        ),
        reverse=True,
    )


def count_values(values: Any) -> list[tuple[str, int]]:
    return sorted(Counter(values).items(), key=lambda item: (-item[1], item[0]))


def write_bar_chart(
    path: Path,
    title: str,
    rows: list[tuple[str, int]],
    x_label: str,
    *,
    width: int = 980,
    left: int = 290,
) -> None:
    row_height = 42
    right = 72
    top = 92
    bottom = 74
    height = top + bottom + max(len(rows), 1) * row_height
    chart_width = width - left - right
    max_value = max((value for _, value in rows), default=1)

    parts = [
        svg_header(width, height),
        f'<text x="32" y="44" class="title">{escape(title)}</text>',
        f'<text x="{left}" y="{height - 28}" class="axis">{escape(x_label)}</text>',
        f'<line x1="{left}" y1="{top - 24}" x2="{left}" y2="{height - bottom + 16}" class="grid-strong"/>',
    ]

    for index, (label, value) in enumerate(rows):
        y = top + index * row_height
        bar_width = int(chart_width * value / max_value) if max_value else 0
        color = PALETTE[index % len(PALETTE)]
        parts.extend(
            [
                f'<text x="{left - 16}" y="{y + 24}" class="label" text-anchor="end">{escape(label)}</text>',
                f'<rect x="{left}" y="{y}" width="{bar_width}" height="26" rx="7" fill="{color}"/>',
                f'<text x="{left + bar_width + 10}" y="{y + 19}" class="value">{value}</text>',
            ]
        )

    if not rows:
        parts.append(f'<text x="{left}" y="{top}" class="label">No data</text>')

    parts.append("</svg>")
    path.write_text("\n".join(parts) + "\n", encoding="utf-8")


def svg_header(width: int, height: int) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<style>
  .bg {{ fill: #f8fafc; }}
  .title {{ font: 700 26px "Avenir Next", "Helvetica Neue", Arial, sans-serif; fill: #0f172a; }}
  .label {{ font: 500 15px "Avenir Next", "Helvetica Neue", Arial, sans-serif; fill: #334155; }}
  .value {{ font: 700 15px "Avenir Next", "Helvetica Neue", Arial, sans-serif; fill: #0f172a; }}
  .axis {{ font: 500 13px "Avenir Next", "Helvetica Neue", Arial, sans-serif; fill: #64748b; }}
  .grid-strong {{ stroke: #cbd5e1; stroke-width: 1.2; }}
</style>
<rect class="bg" x="0" y="0" width="{width}" height="{height}" rx="24"/>'''


def escape(value: str) -> str:
    return html.escape(str(value), quote=True)


def shorten_display(value: str, max_columns: int) -> str:
    if display_width(value) <= max_columns:
        return value

    output = []
    used = 0
    for char in value:
        char_width = 2 if is_wide_char(char) else 1
        if used + char_width > max_columns - 1:
            break
        output.append(char)
        used += char_width
    return "".join(output).rstrip() + "…"


def display_width(value: str) -> int:
    return sum(2 if is_wide_char(char) else 1 for char in value)


def is_wide_char(char: str) -> bool:
    return ord(char) > 127
