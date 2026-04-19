"""Crab pet — a cute sideways crab with snappy claws."""

PET = {
    "name": "crab",
    "frames": {
        # Sleeping — claws down, eyes closed
        "sleep": [
            "     zzZ\n"
            " (v)(-,,- )(v)\n"
            "  /|      |\\\n"
            " _/ |____| \\_",

            "      zZ\n"
            " (v)(-,,- )(v)\n"
            "  /|      |\\\n"
            " _/ |____| \\_",
        ],
        # Idle — looking around, claws waving
        "idle": [
            " (V)(;,,;)(V)\n"
            "  /|      |\\\n"
            " _/ |____| \\_",

            " (V)(;,,; )(V)\n"
            "  /|      |\\\n"
            " _/ |____| \\_",

            "(V) (;,,;)(V)\n"
            "  /|      |\\\n"
            " _/ |____| \\_",
        ],
        # Busy — rapid claw clicking
        "busy": [
            " >V<(◎,,◎)>V<\n"
            "  /|      |\\\n"
            " _/ |____| \\_",

            " (V)(◎,,◎)(V)\n"
            "  /|      |\\\n"
            " _/ |____| \\_",
        ],
        # Attention — claws raised high
        "attention": [
            "\\V/       \\V/\n"
            "   (°,,°)!\n"
            "  /|      |\\\n"
            " _/ |____| \\_",

            "\\V/       \\V/\n"
            "   (°,,°)!!\n"
            "  /|      |\\\n"
            " _/ |____| \\_",
        ],
        # Celebrate — dancing side to side
        "celebrate": [
            "\\V/  ★  \\V/\n"
            "   (^,,^)\n"
            "  /|      |\\\n"
            " _/ |____| \\_",

            " \\V/ ♪ \\V/\n"
            "   (^,,^)\n"
            "   |      |\n"
            "  _/|____|\\_ ",

            "\\V/  ✧  \\V/\n"
            "   (^,,^)\n"
            "  /|      |\\\n"
            " _/ |____| \\_",
        ],
        # Dizzy — spiral eyes, wobbly
        "dizzy": [
            " (v)(@,,@)(v)\n"
            "  /|      |\\\n"
            "  _/|____|\\_ ",

            "  (v)(×,,×)(v)\n"
            "   /|      |\\\n"
            "  _/ |____| \\_",
        ],
        # Heart — happy crab with hearts
        "heart": [
            "  ♥       ♥\n"
            " (V)(♡,,♡)(V)\n"
            "  /|      |\\\n"
            " _/ |____| \\_",

            " ♥  ♥   ♥  ♥\n"
            " (V)(♡,,♡)(V)\n"
            "  /|      |\\\n"
            " _/ |____| \\_",
        ],
    },
}
