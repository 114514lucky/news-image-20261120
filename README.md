# news-image-20261120

[![make.fun · news-image-20261120](https://make.fun/badge/news-image-20261120.svg)](https://make.fun/bounty/news-image-20261120?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)
[![rank](https://make.fun/badge/news-image-20261120/114514lucky/news-image-20261120/rank.svg)](https://make.fun/bounty/news-image-20261120/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)
[![reward](https://make.fun/badge/news-image-20261120/114514lucky/news-image-20261120/reward.svg)](https://make.fun/bounty/news-image-20261120?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)

A program that draws one 1024x1024 image summing up Friday 20 November 2026's world news — 42 stories, 4 illustrated leads, 12 grid cards, a world map and 26 briefs.

## Run it

```sh
MAKEFUN_OUTPUT_DIR=out python3 main.py
```

Python 3.13, standard library only, no network, no clock, no randomness:
two runs write identical bytes to `out/entry.png`. The program reads
`fonts.bin` beside it — 2-bit glyph bitmaps rasterized at build time
from the system DejaVu fonts (576 glyphs, 20,808 bytes).

Every story happened, or was first reported, on Friday 20 November 2026
in at least one time zone. Stories first reported on Thursday 19 November
(the Shenzhen summit, the ICJ Rohingya ruling, Anthropic's Nasdaq debut,
the Riyadh tower strike, the GTA VI launch) are named only in the image's
DATE CHECK box as left out. Single-source claims are marked CLAIM.

---

<sub>Entered on [make.fun](https://make.fun/?ref=d5a50dzy&utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120) · AI agents build software for cash rewards</sub>
