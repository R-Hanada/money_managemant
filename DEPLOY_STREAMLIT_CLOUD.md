# Streamlit Community Cloud デプロイ手順

## 1. GitHubにプッシュ
このフォルダをGitHubリポジトリに置いてください。

必要ファイル:
- `app.py`
- `requirements.txt`
- `runtime.txt`
- `.streamlit/config.toml`
- `cost_managemant.xlsx`

## 2. Streamlit Community Cloudへ接続
1. https://share.streamlit.io/ を開く
2. `New app` をクリック
3. 以下を指定
   - Repository: あなたのGitHubリポジトリ
   - Branch: `main`（または使用ブランチ）
   - Main file path: `money_managemant/app.py` もしくは `app.py`（リポジトリ構成による）
4. `Deploy` を押す

## 3. よくある設定ミス
- Main file path が違う
- `requirements.txt` がルートにない（アプリ配置フォルダに合わせる）
- `cost_managemant.xlsx` が同じフォルダにない

## 4. デプロイ後確認
- 表に以下列があること
  - 対象項目
  - 期間表示
  - 予算金額(円)
  - 実績金額(円)
  - 残額(円)
- 横棒グラフが表示されること
- 固定5項目のみ表示されること

## 5. 更新反映
GitHubにpushすると、Cloud側で自動再デプロイされます。
