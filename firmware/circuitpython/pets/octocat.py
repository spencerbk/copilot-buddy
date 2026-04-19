"""Octocat pet — GitHub's cat-octopus mascot. Canonical pet data format."""

PET = {
    "name": "octocat",
    "frames": {
        # Sleeping — eyes closed, slow breathing
        "sleep": [
            "  ╱|、\n"
            " (˘ ˘ zzZ\n"
            "  ꜝ |、\n"
            "  ~じし_)ノ",

            "  ╱|、\n"
            " (˘ ˘  zZ\n"
            "  ꜝ |、\n"
            " ~ じし_)ノ",
        ],
        # Idle — blinking, looking around
        "idle": [
            "  ╱|、\n"
            " (• ω •)\n"
            "  ꜝ |、\n"
            "  ~じし_)ノ",

            "  ╱|、\n"
            " (- ω -)\n"
            "  ꜝ |、\n"
            "  ~じし_)ノ",

            "  ╱|、\n"
            " (• ω •)?\n"
            "  ꜝ |、\n"
            "  ~じし_)ノ",
        ],
        # Busy — working hard, typing
        "busy": [
            "  ╱|、\n"
            " (◎_◎;)\n"
            "  ꜝ |、⌨\n"
            "  ~じし_)ノ",

            "  ╱|、\n"
            " (◎_◎ )\n"
            "  ꜝ |、 ⌨\n"
            "  ~じし_)ノ",
        ],
        # Attention — alert, bouncing
        "attention": [
            "  ╱|、  !\n"
            " (°ω° )\n"
            "  ꜝ |、\n"
            "  ~じし_)ノ",

            "  ╱|、 !!\n"
            " (°ω°)/\n"
            "  ꜝ |、\n"
            " ~ じし_)ノ",
        ],
        # Celebrate — confetti, dancing
        "celebrate": [
            "  ╱|、 ★\n"
            "\\(^ω^ )/\n"
            "  ꜝ |、\n"
            "  ~じし_)ノ",

            " ☆╱|、\n"
            " (^ω^)ノ\n"
            "  ꜝ |、 ♪\n"
            "  ~じし_)ノ",

            "  ╱|、 ✧\n"
            "\\(^ω^ )\n"
            "  ꜝ |、♪\n"
            " ~ じし_)ノ",
        ],
        # Dizzy — spiral eyes, wobbling
        "dizzy": [
            "  ╱|、\n"
            " (@_@ )\n"
            "  ꜝ |、\n"
            " ~ じし_)ノ",

            "   ╱|、\n"
            "  (×_× )\n"
            "   ꜝ |、\n"
            "  ~じし_)ノ",
        ],
        # Heart — floating hearts
        "heart": [
            "  ╱|、 ♥\n"
            " (♡ω♡ )\n"
            "  ꜝ |、\n"
            "  ~じし_)ノ",

            "  ╱|、♥\n"
            " (♡ω♡)ノ♥\n"
            "  ꜝ |、\n"
            " ~ じし_)ノ",
        ],
    },
}
