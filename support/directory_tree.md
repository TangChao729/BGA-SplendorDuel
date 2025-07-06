splendor_duel/                ← top‐level package
├── __init__.py
├── cards.py                  # Card + Deck
├── tokens.py                 # Token + Bag
├── board.py                  # Board (incl. privileges & royal cards)
├── player.py                 # PlayerState
├── actions.py                # ActionType + Action
├── env.py                    # SplendorDuelEnv (Gymnasium wrapper)
├── cli.py                    # CommandLineUI
├── agents.py                 # RandomAgent (and later other agents)
├── utils.py                  # any shared helpers (e.g. parsing, serialization)
└── tests/                    # pytest or unittest suite
    ├── __init__.py
    ├── test_cards.py
    ├── test_tokens.py
    ├── test_board.py
    ├── test_player.py
    ├── test_actions.py
    ├── test_env.py
    └── test_cli.py

project root
├── README.md                 # overview, installation, usage
├── pyproject.toml            # dependencies, build config
├── requirements.txt          # pin exact versions (if not using pyproject)
└── .gitignore