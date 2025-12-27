# 2d_shooting_pyxel

Pyxel 製の横スクロールシューティング（Gradius-like）です。  
4種類の機体選択、4種類の攻撃、撃破数（スコア）、ライフゲージ、アイテムドロップ、背景テーマ遷移を実装しています。

## Requirements

- Python 3.x
- Pyxel

外部ライブラリ（pygame / numpy など）は使用していません。

## Run

リポジトリ直下で実行します。

```sh
pyxel run main.py
```

## GitHub Pages（Web公開）

GitHub Actions で Pyxel を HTML に変換して GitHub Pages にデプロイします。

1. GitHub のリポジトリ設定 `Settings -> Pages` を開く
2. `Build and deployment` の `Source` を `GitHub Actions` にする
3. `main` ブランチへ push すると自動でデプロイされる

ローカルでPages用HTMLを作る場合:

```sh
./scripts/build_pages.sh
```

生成物は `site/index.html` です。

## Controls

- `W/A/S/D`: 移動
- `J`: 決定 / 砲弾（Cannon）
- `K`: ミサイル（Missile）
- `L`: 爆弾（Bomb）
- `U`: レーザー（押しっぱなしで溜めて、離すと発射。最大まで溜めると最大出力＋雷エフェクト）
- `I`: 火炎放射（Flame）
- `O`: 戻る（タイトルへ）
- `TAB`: デバッグ表示切替（当たり判定の可視化など）

## Game Rules

- 敵を撃破すると撃破数（KILLS）が増えます
- 被弾するとライフゲージが減り、0 でゲームオーバーになります（被弾直後に短い無敵時間あり）
- 敵撃破時に確率でアイテムがドロップします
  - `heal`: ライフ回復
  - `power`: 武器レベル上昇
  - `speed`: 移動速度上昇（上限あり）
- `power` 取得後の追加効果
  - 火炎放射（`B`）が強化され、押しっぱなしでどんどん大きく/長く/太くなります
  - 最大まで溜めると火炎が青くなります
  - 火炎放射は威力低めですが、火炎を当てた敵は燃焼し、近くの敵に燃え広がります（燃焼中は敵が遅くなります）
- 背景はステージ区間に応じて「moon → space → planet1 → planet2 …」のように遷移します

## Config

調整可能な値は `config/game.toml` に集約しています。

- ウィンドウ設定: `window.*`
- プレイヤー: `player.*`
- 武器: `weapons.*`
- アイテム: `items.*`
- ステージ区間/スポーン: `stage.*`

## Project Layout

- `main.py`: エントリポイント
- `src/core/`: 共通基盤（App / 入力 / 設定 / アセット / シーン管理）
- `src/scenes/`: Title / Game / GameOver
- `src/entities/`: Player / Enemy / Projectile / Item / Effects
- `src/systems/`: Stage / Spawner / Collision / DropTable
- `src/ui/`: HUD

## Notes

- `draw()` 内ではゲーム状態の変更を行わず、描画は `pyxel.blt()` を基本にしています（背景のみ `pyxel.cls()` / `pyxel.bltm()` を使用）。
- `.env` は任意です（存在しなくても起動します）。必要なキーがある場合は `.env.example` を参考にしてください。
