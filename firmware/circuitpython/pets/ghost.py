"""Ghost pet — a playful floating ghost."""

PET = {
    "name": "ghost",
    "frames": {
        # Sleeping — ghost snoozing
        "sleep": [
            "  .--.  zzZ\n"
            " | -.- |\n"
            " |     |\n"
            "  \\/\\/\\/",

            "  .--.   zZ\n"
            " | -.- |\n"
            " |     |\n"
            "  \\/\\/\\/",
        ],
        # Idle — floating, eyes looking around
        "idle": [
            "  .--.\n"
            " | o.o |\n"
            " |     |\n"
            "  \\/\\/\\/",

            "   .--.\n"
            "  | o.o |\n"
            "  |     |\n"
            "   \\/\\/\\/",

            "  .--.\n"
            " | o. o|\n"
            " |     |\n"
            "  \\/\\/\\/",
        ],
        # Busy — rushing around, trailing
        "busy": [
            " ~ .--.\n"
            " ~| ◎.◎ |\n"
            "  |     |\n"
            "   \\/\\/\\/",

            "  .--. ~\n"
            " | ◎.◎ |~\n"
            " |     |\n"
            "  \\/\\/\\/",
        ],
        # Attention — surprised ghost
        "attention": [
            "  .--. !\n"
            " | O_O |\n"
            " |     |\n"
            "  \\/\\/\\/",

            "  .--. !!\n"
            " | O_O |/\n"
            " |     |\n"
            "  \\/\\/\\/",
        ],
        # Celebrate — party ghost
        "celebrate": [
            "  .~~. ★\n"
            " | ^o^ |\n"
            " |     |\n"
            "  \\/\\/\\/",

            " ☆.--.\n"
            " | ^o^ | ♪\n"
            " |     |\n"
            "  \\/\\/\\/",

            "  .~~. ✧\n"
            " | ^o^ |♪\n"
            " |     |\n"
            "  \\/\\/\\/",
        ],
        # Dizzy — swirly confused ghost
        "dizzy": [
            " ~.--.\n"
            " | @.@ |\n"
            " |  ~  |\n"
            "  \\/\\/\\/",

            "  .--. ~\n"
            " | ×.× |\n"
            " | ~   |\n"
            "   \\/\\/\\/ ",
        ],
        # Heart — blushing ghost with hearts
        "heart": [
            "  .--. ♥\n"
            " | ♡.♡ |\n"
            " |     |\n"
            "  \\/\\/\\/",

            " ♥.--. ♥\n"
            " | ♡.♡ |♥\n"
            " |     |\n"
            "  \\/\\/\\/",
        ],
    },
}
