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

### push不要でデータだけ更新したい場合
アプリ画面の `データファイルをアップロード (xlsx)` を使うと、GitHubへpushしなくても表示データを差し替えできます。

手順:
1. Excelを編集して保存
2. アプリ画面で `データファイルをアップロード (xlsx)` に編集済みxlsxを指定
3. 必要なら `最新データ読込` を押してキャッシュをクリア

補足:
- アップロードファイルは現在のセッションで優先利用されます。
- 既定のローカルファイルを使う場合も、`最新データ読込` で即時反映できます。
- キャッシュは5分TTLでも自動更新されます。
