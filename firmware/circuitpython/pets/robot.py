"""Robot pet — a friendly robot with antenna and screen face."""

PET = {
    "name": "robot",
    "frames": {
        # Sleeping — powered down, dim display
        "sleep": [
            "    T  zzZ\n"
            "  [_._]\n"
            "  |   |\n"
            " _|___|_",

            "    T   zZ\n"
            "  [_._]\n"
            "  |   |\n"
            " _|___|_",
        ],
        # Idle — scanning, antenna blinking
        "idle": [
            "    *\n"
            "  [o.o]\n"
            "  |   |\n"
            " _|___|_",

            "    T\n"
            "  [o.o]\n"
            "  |   |\n"
            " _|___|_",

            "    *\n"
            "  [o. o]\n"
            "  |   |\n"
            " _|___|_",
        ],
        # Busy — processing, loading display
        "busy": [
            "    *\n"
            "  [◎_◎]\n"
            "  |[==]|\n"
            " _|___|_",

            "    *\n"
            "  [◎_◎]\n"
            "  |[= ]|\n"
            " _|___|_",
        ],
        # Attention — exclamation, antenna up
        "attention": [
            "    ! \n"
            "  [O_O]\n"
            "  |   |\n"
            " _|___|_",

            "    !!\n"
            "  [O_O]/\n"
            "  |   |\n"
            " _|___|_",
        ],
        # Celebrate — arms waving, stars
        "celebrate": [
            "   ★*\n"
            " \\[^v^]/\n"
            "  |   |\n"
            " _|___|_",

            "  ☆ *\n"
            "  [^v^]> ♪\n"
            "  |   |\n"
            " _|___|_",

            "   ✧*\n"
            " \\[^v^]/ ♪\n"
            "  |   |\n"
            " _|___|_",
        ],
        # Dizzy — error display, sparks
        "dizzy": [
            "   ~*~\n"
            "  [@_@]\n"
            "  |ERR|\n"
            " _|___|_",

            "    *~\n"
            "  [×_×]\n"
            "  | ER|\n"
            "  _|__|_",
        ],
        # Heart — heart on screen
        "heart": [
            "    * ♥\n"
            "  [♡.♡]\n"
            "  | <3|\n"
            " _|___|_",

            "  ♥ * ♥\n"
            "  [♡.♡]\n"
            "  |<3 |\n"
            " _|___|_",
        ],
    },
}
