# mnemo 要件・仕様書

このドキュメントは `docs/todo.md`（未対応事項の一覧）・`docs/tasks.md`（Issue化用の小タスク一覧）の前提となる仕様をまとめたもの。
会話でユーザーと詰めた要件をベースにしている。

## 1. サービス概要（再確認）

音声ファイルをアップロード → Whisperで文字起こし → （オプションで）Ollamaで要約、を行うAPIサービス。
FastAPI + Celery(RabbitMQ) + MySQL構成。

## 2. 今回のスコープ

### やること
- タスク永続化基盤の整備（文字起こし・要約タスクの状態管理・結果保存・ポーリングAPI）
- 要約機能の実装（Ollamaを使った単純な自由文要約）
- 音声フォーマット対応（WAV以外をffmpegで変換）
- 未使用依存の整理（`pywhispercpp`の削除）

### やらないこと（今回は明確に対象外・TODOとして記録するのみ）
- API認証・認可（`ApiKey`を使ったヘッダー認証など）— 実装せず、関連コードは現状のまま置いてTODOにする
- レート制限・不正利用対策（`FingerPrint`, `used_counts`）
- 要約の精度向上・プロンプトチューニング（動くことを優先。品質は追求しない）
- 多言語対応（日本語のみを前提とする）
- リアルタイム進捗通知（WebSocket等）。ポーリングAPIのみ

### この方針を選んだ理由
- 本プロジェクトは「プログラミング初心者に小タスクを割り振って学習してもらう」ことを目的としている。
- そのため、スコープを広げすぎず、1つ1つのタスクを小さく・自己完結させることを優先する。

## 3. 認証に関する暫定対応（重要な設計判断）

現状のコードには以下の不整合がある。

- `models/files.py` の `File.owner_id` は `nullable=False` で `api_keys.id` への外部キーになっている。
- しかし `services/files/__init__.py` の `save_file()` は `owner_id` を一切設定していない。
- そのため、**現状のコードのままではファイルアップロードAPIがそもそもDBエラーで失敗する**。

認証実装は今回のスコープ外のため、暫定対応として以下を行う。

- `files.owner_id` と `tasks.owner_id` を **一時的にNULL許容（nullable）** に変更する（マイグレーションで対応）。
- モデルの型も `Mapped[int]` → `Mapped[Optional[int]]` に変更する。
- 認証実装を行うタイミングで、これらを再度 `NOT NULL` に戻し、リクエストから取得した `ApiKey` を設定するようにする（`docs/todo.md` に記録）。

## 4. タスク永続化 仕様

### 4.1 方針（決定事項）
- タスクの **状態（ステータス）の正はCeleryのresult backend**とする。DB側で状態を二重管理しない。
- タスクの **種別（文字起こし／要約など）は1つの`Task`テーブルを`kind`列で区別**して管理する（テーブルを種別ごとに分けない）。
- タスクの **実行結果（テキスト・SRT・要約文）は専用の結果テーブル（`TaskResult`）に保存**する。`Task`テーブルには結果を持たせない。
- `Task`レコードは **Celeryタスク起動時**（例: `POST /v1/transcribes/{uuid}` や `POST /v1/summaries/{file_uuid}` を呼んだ瞬間）に作成する。アップロード時点では作成しない。

### 4.2 テーブル設計

#### `tasks`（既存テーブルの変更）
| カラム | 型 | 説明 |
|---|---|---|
| id | Integer PK | |
| uuid | UUID(36) | 外部公開用ID |
| task_id | String(64) | Celeryのタスクid |
| kind | String(32) | `"transcribe"` \| `"summarize"`（新規追加） |
| owner_id | Integer, nullable | `api_keys.id`（今回は一時的にnullable化。3章参照） |
| file_id | Integer, nullable | `files.id` |
| created_at / updated_at / deleted_at | DateTime | 既存の`DeletableModel`由来 |

#### `task_results`（新規テーブル）
| カラム | 型 | 説明 |
|---|---|---|
| id | Integer PK | |
| uuid | UUID(36) | 外部公開用ID |
| task_id | Integer, FK(tasks.id), unique | 対象タスク（1タスクにつき1結果、1:1） |
| text | Text, nullable | 文字起こし結果テキスト、または要約結果本文（`kind`によって意味が変わる） |
| srt | Text, nullable | 文字起こし時のみ使用するSRT字幕テキスト |
| error_message | Text, nullable | 失敗時のエラーメッセージ |
| created_at / updated_at | DateTime | |

`text`列を文字起こし・要約の両方で共用するのは、テーブル数を増やさずシンプルに保つための意図的な設計。

### 4.3 ステータス取得の流れ（`GET .../tasks/{uuid}` の実装方針）

1. `uuid` から `Task` レコードを検索し、`task_id`（Celery ID）と `kind` を取得する。
2. `celery.result.AsyncResult(task.task_id, app=celery_app)` でCeleryの状態を取得する（`PENDING` / `STARTED` / `SUCCESS` / `FAILURE` など）。
3. Celeryの状態を、アプリ側のステータス（`PENDING` / `RUNNING` / `COMPLETED` / `FAILED`。既存の `entities/transcribes/__init__.py` の `TaskStatus` を汎用化して `entities/tasks` に移す）にマッピングする。
4. `SUCCESS` の場合は `TaskResult` を `task_id` で検索し、結果（`text`/`srt`）をレスポンスに含める。
5. `FAILURE` の場合は `TaskResult.error_message`（Celeryタスク側が例外時に書き込む）を返す。

## 5. 要約機能 仕様

### 5.1 方針（決定事項）
- 要約エンジンは **Ollama**（ローカルLLM）を使う。モデル名は環境変数で切り替え可能にする（デフォルトモデルは実装者が選定してよい。例: `llama3.2` 等の軽量モデル）。
- 実行トリガーは **別APIで明示的に実行**する（文字起こし完了後の自動実行チェーンは組まない）。呼び出し前提として、対象ファイルの文字起こしが完了している必要がある。
- 出力形式は **単一の自由文要約**（見出し分解や構造化データは不要）。
- **要約の精度・プロンプト品質は追求しない**。動くこと・学習素材として理解しやすいことを優先する。

### 5.2 設定
`settings.py` に以下を追加する。

```python
ollama_host: str = "http://ollama:11434"
ollama_model: str = "llama3.2"
```

### 5.3 API

| メソッド | パス | 説明 |
|---|---|---|
| POST | `/v1/summaries/{file_uuid}` | 指定ファイルの文字起こし結果を元に要約タスクを起動する。文字起こし未完了の場合は`ValidationError`(400)を返す |
| GET | `/v1/summaries/tasks/{uuid}` | 要約タスクの状態・結果を取得する（4.3の流れを流用） |

### 5.4 処理フロー
1. `POST /v1/summaries/{file_uuid}` が呼ばれる。
2. 対象ファイルに紐づく、直近で完了した`kind="transcribe"`の`Task`＋`TaskResult`を検索する。無ければ`NotFoundError`。
3. `kind="summarize"`の`Task`を作成し、Celeryタスク`summarize_task.delay(file_id)`を起動する。
4. `summarize_task`は文字起こし結果テキストを取得し、`services/summaries`の`summarize()`関数でOllamaに要約を依頼する。
5. 結果を`TaskResult`に保存する。

## 6. 音声フォーマット対応 仕様

- `services/files/__init__.py` の `ensure_wav_file()` を実装し、WAV以外の形式（mp3/m4a等）は **ffmpeg** を使ってWAVに変換する。
- Dockerイメージ（`docker/Dockerfile`）に `ffmpeg` パッケージを追加する（現状 `gcc` / `pkg-config` / `default-libmysqlclient-dev` のみで、ffmpegは入っていない）。
- 変換は `save_file()` の中、もしくはアップロードエンドポイントで、保存直後に行う。

## 7. 依存関係の整理

- `pywhispercpp` は現在コード内で未使用のため `pyproject.toml` の `dependencies` から削除する。
- `ollama` は要約機能で使用することが確定したため、そのまま維持する。

## 8. API一覧（今回の変更を反映した全体像）

| メソッド | パス | 状態 |
|---|---|---|
| POST | `/v1/transcribes/uploads` | 既存（変更なし） |
| POST | `/v1/transcribes/{uuid}` | 既存 + Task作成処理を追加 |
| GET | `/v1/transcribes/tasks/{uuid}` | 未実装 → 今回実装 |
| POST | `/v1/summaries/{file_uuid}` | 新規実装 |
| GET | `/v1/summaries/tasks/{uuid}` | 新規実装 |

## 9. 将来対応（今回は着手しないが記録しておく事項）

- API認証・認可（`ApiKey`の検証、`owner_id`の正規復元）
- レート制限（`FingerPrint`, `used_counts`の活用）
- 要約の精度向上（プロンプト改善、モデル選定、要約の構造化）
- `GET /v1/transcribes/tasks/{uuid}` 等のポーリングAPIをWebSocket/SSEに置き換える
