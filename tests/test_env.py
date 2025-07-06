import pytest

from env import SplendorDuelEnv
from model.actions import Action
import yaml


def test_reset_and_observation_structure():
    box = yaml.safe_load("../data/box.yaml")
    env = SplendorDuelEnv()
    obs, info = env.reset()
    assert isinstance(obs, dict)
    assert "board" in obs and "players" in obs and "current_player" in obs
    assert info == {}


def test_legal_actions_and_step(monkeypatch):
    # Simplify Board
    class Dummy:
        def __init__(self, *args, **kwargs):
            self.tokens = lambda: {"black": 1, "pearl": 1}
            self.privileges = 1
            self.pyramid = {1: [None], 2: [None], 3: [None]}
            self.royal_cards = []

        def take_tokens(self, colors):
            return []

        def reserve_card(self, lvl, idx):
            return None

        def purchase_card(self, lvl, idx):
            return None

        def use_privilege(self):
            return True

    monkeypatch.setattr("env.Board", Dummy)

    from env import SplendorDuelEnv

    env = SplendorDuelEnv()
    obs, _ = env.reset()
    # legal_actions should return list of Action
    actions = env.legal_actions()
    assert isinstance(actions, list)
    assert all(isinstance(a, Action) for a in actions)
    # Test executing one action doesn't crash
    if actions:
        obs2, reward, done, truncated, info = env.step(actions[0])
        assert isinstance(obs2, dict)
        assert isinstance(reward, float)
        assert isinstance(done, bool)
        assert isinstance(truncated, bool)
        assert isinstance(info, dict)
