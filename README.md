# Kubernetes Visualization Simulator

Kubernetes の構成・イベントを、自然言語入力から可視化するハッカソン向けプロジェクトです。  
ユーザーがシナリオを文章で入力すると、バックエンドが YAML / シナリオ説明 / Mermaid 図を生成し、フロントエンドで確認できます。

- Hackathon: [Google Cloud Japan AI Hackathon Vol.4](https://zenn.dev/hackathons/google-cloud-japan-ai-hackathon-vol4)

## Features

- チャット入力からシナリオを生成
- 生成した構成を Mermaid 図として可視化
- シナリオ説明（日本語）と YAML マニフェストを同時表示
- Mermaid 描画失敗時に、AI 指示で図を再生成

## Tech Stack

- Frontend: React + TypeScript + Vite
- Backend: FastAPI + SQLAlchemy (async)
- Database: MySQL（`DATABASE_URL` で接続）
- AI: Gemini API（`GEMINI_API_KEY`）
- Diagram: Mermaid

## Repository Structure

```text
.
├── src/frontend/   # React アプリ
└── src/backend/    # FastAPI アプリ
```

## Prerequisites

- Node.js 20+
- Python 3.11+
- MySQL 8+（または互換 DB）
- Gemini API Key

## Local Setup

### 1. Backend

```bash
cd src/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

`src/backend/.env` を作成して、以下を設定してください。

```env
DATABASE_URL=mysql+aiomysql://USER:PASSWORD@HOST:3306/DB_NAME
GEMINI_API_KEY=your_gemini_api_key
KUBERNETES_HOST=http://localhost:8080
```

起動:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

ヘルスチェック:

```bash
curl http://127.0.0.1:8000/health
```

### 2. Frontend

別ターミナルで:

```bash
cd src/frontend
npm install
npm run dev
```

- Frontend: `http://127.0.0.1:5173`
- Backend API: `http://127.0.0.1:8000`

`vite.config.ts` で `/api` はバックエンドへプロキシされます。

## API Overview

主要エンドポイント（prefix: `/api/v1`）:

- `POST /sessions/` セッション作成
- `POST /sessions/{session_id}/messages` チャット送信 + シナリオ生成
- `GET /scenarios/{id}` シナリオ取得
- `POST /scenarios/{id}/events` イベント追加
- `POST /scenarios/{id}/diagram/retry` Mermaid 図の再生成
- `DELETE /k8s/pods/{namespace}/{name}` Pod 削除
- `WS /stream/events` Kubernetes イベントストリーム

## Notes

- `GEMINI_API_KEY` 未設定時は図の再生成 API が失敗します。