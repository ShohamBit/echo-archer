from loop_archer.models import new_game_state
from loop_archer.persistence import load_game, save_game


def test_save_load_preserves_shards_upgrades_best_time_and_loop(tmp_path):
    path = tmp_path / "save.json"
    state = new_game_state(total_shards=18, owned_upgrades={"sharper_arrows_1"})
    state.best_time = 42.5
    state.current_loop = 4

    save_game(state, path)
    loaded = load_game(path)

    assert loaded.total_shards == 18
    assert loaded.owned_upgrades == {"sharper_arrows_1"}
    assert loaded.player_stats.damage == 12
    assert loaded.best_time == 42.5
    assert loaded.current_loop == 4
