"""Generate a clean original SVG crossing schedule without third-party packages."""

from pathlib import Path


def build() -> str:
    rows = [("A + B", True, 2, 2), ("A", False, 1, 3),
            ("C + D", True, 5, 8), ("B", False, 2, 10), ("A + B", True, 2, 12)]
    pieces = ['<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="740" viewBox="0 0 1100 740" role="img" aria-labelledby="title desc">',
              '<title id="title">Bridge and torch: five trips in twelve hours</title>',
              '<desc id="desc">A needs 1 hour, B 2, C 4, D 5. A and B cross, A returns, C and D cross, B returns, A and B cross. Trip costs 2,1,5,2,2 sum to 12 hours.</desc>',
              '<defs><marker id="arrow" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto"><path d="M0,0 L9,4.5 L0,9 Z" fill="#62478a"/></marker></defs>',
              '<rect width="1100" height="740" rx="28" fill="#faf8f1"/>',
              '<g font-family="Arial, sans-serif" fill="#342348">',
              '<text x="60" y="58" font-size="30" font-weight="700">1 h · 2 h · 4 h · 5 h → 12 h</text>',
              '<text x="60" y="96" font-size="21">A = 1 h     B = 2 h     C = 4 h     D = 5 h</text>',
              '<text x="188" y="152" font-size="23" font-weight="700">L</text>',
              '<text x="708" y="152" font-size="23" font-weight="700">R</text>',
              '<text x="920" y="152" font-size="23" font-weight="700">Σt</text>',
              '<path d="M195,173 L195,635 M715,173 L715,635" stroke="#d7cbe2" stroke-width="3" stroke-dasharray="6 7"/>']
    for index, (names, forward, duration, total) in enumerate(rows):
        y = 212 + index * 91
        pieces.append(f'<circle cx="69" cy="{y}" r="19" fill="#e6dff0"/><text x="69" y="{y + 7}" text-anchor="middle" font-size="20" font-weight="700">{index + 1}</text>')
        start, end = (222, 687) if forward else (687, 222)
        pieces.append(f'<path d="M{start},{y} L{end},{y}" stroke="#62478a" stroke-width="3" marker-end="url(#arrow)"/>')
        pieces.append(f'<rect x="350" y="{y - 28}" width="210" height="56" rx="13" fill="#fffdfa" stroke="#cdbbdf" stroke-width="2"/>')
        pieces.append(f'<text x="455" y="{y + 7}" text-anchor="middle" font-size="22" font-weight="700">{names} · {duration} h</text>')
        pieces.append(f'<text x="944" y="{y + 8}" text-anchor="middle" font-size="25" font-weight="700">{total} h</text>')
    pieces += ['<rect x="60" y="652" width="980" height="56" rx="13" fill="#e7efe8"/>',
               '<text x="550" y="688" text-anchor="middle" font-size="24" font-weight="700">2 + 1 + 5 + 2 + 2 = 12 h</text>',
               '</g></svg>']
    return "\n".join(pieces) + "\n"


if __name__ == "__main__":
    path = Path(__file__).with_name("prep_039_bridge_timeline.svg")
    path.write_bytes(build().replace("\n", "\r\n").encode("utf-8"))
    print(path.name)
