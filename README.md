# X 投稿自動化ツール

ゴールを設定するとClaude AIがツイートを自動生成し、スケジュール投稿できるウェブアプリです。

## アーキテクチャ

| 部分 | 技術 | デプロイ先 |
|------|------|-----------|
| フロントエンド | HTML/CSS/JS (静的) | GitHub Pages |
| バックエンド | Python FastAPI | Render (無料) |
| AI | Anthropic Claude API | - |
| X投稿 | Twitter API v2 (tweepy) | - |

## セットアップ手順

### 1. Twitter API の取得

1. [Twitter Developer Portal](https://developer.twitter.com/) でアプリを作成
2. **Elevated Access** を申請（投稿に必要）
3. API Key, API Secret, Access Token, Access Token Secret を取得

### 2. バックエンド (Render) のデプロイ

1. [Render.com](https://render.com) でアカウント作成
2. 「New Web Service」→ このリポジトリを接続
3. Root Directory: `backend`
4. 以下の環境変数を Render ダッシュボードで設定:

| 変数名 | 説明 |
|--------|------|
| `TWITTER_API_KEY` | Twitter API Key |
| `TWITTER_API_SECRET` | Twitter API Secret |
| `TWITTER_ACCESS_TOKEN` | Access Token |
| `TWITTER_ACCESS_TOKEN_SECRET` | Access Token Secret |
| `ANTHROPIC_API_KEY` | [Anthropic Console](https://console.anthropic.com) で取得 |
| `CORS_ORIGIN` | GitHub Pages の URL (例: `https://username.github.io`) |

5. デプロイ後に表示される URL をメモする

### 3. フロントエンドの設定

`frontend/js/api.js` の先頭にある `API_BASE` を Render の URL に更新:

```js
const API_BASE = "https://your-app-name.onrender.com/api/v1";
```

### 4. GitHub Pages のデプロイ

1. GitHub リポジトリの Settings → Pages → Source: **GitHub Actions** を選択
2. `main` ブランチにプッシュすると自動デプロイされます

## ローカル開発

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env  # 環境変数を設定
uvicorn main:app --reload
```

フロントエンドの確認:
```bash
cd frontend
python -m http.server 8080
```

## 注意事項

- **Render 無料枠**: 15分間アクセスがないとスリープします。初回リクエストは約30秒かかります
- **スケジュールの永続化**: SQLite を使用しているため、Render の再デプロイ時にスケジュール情報が消える場合があります
- **Twitter API**: 投稿には Elevated Access が必要です。申請が承認されるまで数日かかる場合があります
