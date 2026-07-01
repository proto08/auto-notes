# mnemo タスク一覧（Issue化用）

`docs/specs.md`（仕様）と`docs/todo.md`（TODO一覧）を元に、初心者エンジニアがひとつずつ着手できる粒度に分割したタスク一覧。
各タスクはそのままGitHub Issueにする想定なので、背景・完了条件・対象ファイルを明記している。

**進める順番**: 番号の順に上から着手するのが基本（後続タスクが前提にしているため）。「依存」に前提タスクを明記した。

難易度: `S`=数時間程度 / `M`=半日〜1日程度

---

## TASK-00: ウォームアップ — フィラー除去処理のユニットテストを書く

- **難易度**: S
- **依存**: なし（最初に取り組むのに最適）
- **背景**: `services/transcribes/__init__.py` の `remove_fillers()` にテストが一つも存在しない。開発環境のセットアップ（`uv sync`, `uv run pytest`）と、リポジトリの構成に慣れるためのウォームアップタスク。
- **やること**:
  1. `tests/services/test_transcribes.py` を新規作成する
  2. `remove_fillers()` に対し、フィラー語を含む文章／含まない文章の両方でテストケースを書く
  3. `uv run pytest` でテストが通ることを確認する
- **完了条件**: `uv run pytest` が新規テストを含めて全て成功する
- **対象ファイル**: `tests/services/test_transcribes.py`（新規）

---

## Phase 0: 前提修正（他タスクに入る前に必須）

## TASK-01: `owner_id` を一時的にNULL許容にするマイグレーションを作成する

- **難易度**: S
- **依存**: なし
- **背景**: `File.owner_id` / `Task.owner_id` は `nullable=False` で `api_keys.id` を参照しているが、`save_file()` などどこからも値を設定していない。認証機能は今回のスコープ外（`docs/specs.md` 3章）なので、暫定的にnullable化して現状のバグ（アップロードAPIがDB制約違反で失敗する）を解消する。
- **やること**:
  1. `models/files.py` の `File.owner_id` を `Mapped[Optional[int]]` に変更し、`nullable=True` にする
  2. `models/tasks.py` の `Task.owner_id` も同様に変更する
  3. `uv run alembic revision --autogenerate -m "make owner_id nullable"` でマイグレーションを作成する
  4. `uv run alembic upgrade head` で反映する
- **完了条件**: マイグレーションが通り、`owner_id`を指定せずに`File`を作成してもエラーにならない
- **対象ファイル**: `models/files.py`, `models/tasks.py`, `alembic/versions/`(新規)

## TASK-02: `Task.owner` リレーションの不具合を修正する

- **難易度**: S
- **依存**: なし
- **背景**: `models/tasks.py` の `Task.owner` が `relationship("ApiKey", back_populates="files")` になっており、`File.owner`（同じく `back_populates="files"`）と衝突している。おそらくコピペミス。`ApiKey`側に`Task`用の逆参照が定義されていない。
- **やること**:
  1. `models/secrets.py` の `ApiKey` に `tasks: Mapped[list["Task"]] = relationship("Task", back_populates="owner")` を追加する
  2. `models/tasks.py` の `Task.owner` の `back_populates` を `"tasks"` に修正する
- **完了条件**: `File`と`Task`それぞれの`owner`リレーションが正しく別々に対応する。既存のテスト・アプリ起動に影響がないことを確認する
- **対象ファイル**: `models/secrets.py`, `models/tasks.py`

---

## Phase 1: タスク永続化（`docs/specs.md` 4章）

## TASK-03: `Task`モデルに`kind`列を追加する

- **難易度**: S
- **依存**: TASK-01, TASK-02
- **背景**: 文字起こし・要約など複数種別のタスクを1つの`tasks`テーブルで管理する方針（`docs/specs.md` 4.1）。現状`kind`にあたる列が無い。
- **やること**:
  1. `models/tasks.py` に `kind: Mapped[str] = mapped_column(String(32), nullable=False)` を追加する
  2. マイグレーションを作成・適用する
- **完了条件**: `Task`作成時に`kind="transcribe"`または`"summarize"`を指定できる
- **対象ファイル**: `models/tasks.py`, `alembic/versions/`(新規)

## TASK-04: 結果保存用テーブル `TaskResult` を新規作成する

- **難易度**: M
- **依存**: TASK-03
- **背景**: 文字起こし結果（テキスト/SRT）や要約結果を構造化して保存する場所が無い。`docs/specs.md` 4.2のテーブル定義に従って新規作成する。
- **やること**:
  1. `models/task_results.py` を新規作成し、`TaskResult`モデルを定義する（`id`, `uuid`, `task_id`(FK, unique), `text`, `srt`, `error_message`, `created_at`, `updated_at`）
  2. `alembic/env.py` に `import models.task_results` を追加する（autogenerateで検出されるように）
  3. マイグレーションを作成・適用する
- **完了条件**: `task_results`テーブルが作成され、`task_id`に`unique制約`が付いている
- **対象ファイル**: `models/task_results.py`(新規), `alembic/env.py`, `alembic/versions/`(新規)

## TASK-05: タスクステータスの共通DTO・Celery状態マッピングを実装する

- **難易度**: M
- **依存**: TASK-04
- **背景**: `entities/transcribes/__init__.py` に定義されている `TaskStatus` enumは文字起こし専用の場所にあり、要約タスクでも使い回せる形になっていない。Celeryの状態（`PENDING`/`STARTED`/`SUCCESS`/`FAILURE`等）とアプリ側`TaskStatus`のマッピングも存在しない。
- **やること**:
  1. `entities/tasks/__init__.py` を新規作成し、`TaskStatus` enum（`PENDING`/`RUNNING`/`COMPLETED`/`FAILED`）と、タスク状態＋結果を表すDTO（例: `TaskStatusDto`）を定義する
  2. `entities/transcribes/__init__.py` の`TaskStatus`は`entities/tasks`のものを使うように差し替える（重複削除）
  3. `services/tasks/__init__.py` に、Celeryの`AsyncResult.state`を`TaskStatus`に変換する関数（例: `map_celery_state(state: str) -> TaskStatus`）を実装する
- **完了条件**: Celeryの4状態それぞれが正しく`TaskStatus`にマッピングされることをテストで確認する
- **対象ファイル**: `entities/tasks/__init__.py`(新規), `entities/transcribes/__init__.py`, `services/tasks/__init__.py`

## TASK-06: 文字起こし起動時に`Task`レコードを作成する

- **難易度**: M
- **依存**: TASK-03, TASK-04
- **背景**: `POST /v1/transcribes/{uuid}` はCeleryタスクを起動するだけで、`Task`テーブルにレコードを作っていない（コード中に`# TODO: create task`コメントあり）。
- **やること**:
  1. `services/tasks/__init__.py` に `create_task(session, kind: str, file_id: int, celery_task_id: str) -> Task` のような関数を追加する
  2. `v1/transcribes/__init__.py` の `transcribe` エンドポイントで、Celeryタスク起動後に`create_task(..., kind="transcribe", ...)`を呼び、`session.commit()`する
- **完了条件**: `POST /v1/transcribes/{uuid}` を呼ぶと`tasks`テーブルに`kind="transcribe"`のレコードが作成される
- **対象ファイル**: `services/tasks/__init__.py`, `v1/transcribes/__init__.py`

## TASK-07: 文字起こしタスク完了時に結果を`TaskResult`へ保存する

- **難易度**: M
- **依存**: TASK-04, TASK-06
- **背景**: 現在`transcribe_task`はCeleryの戻り値として結果を返すだけで、DBに保存していない。失敗時のエラー保存も無い。
- **やること**:
  1. `tasks/transcribes.py` の `transcribe_task` を修正し、`transcribe()`の結果（text/srt）を`TaskResult`として保存する
  2. 例外発生時は`TaskResult.error_message`に保存してから再raiseする（`task_reject_on_worker_lost`等の既存リトライ設定はそのまま活かす）
- **完了条件**: 文字起こしが成功すると`task_results`にtext/srtが保存され、失敗するとerror_messageが保存される
- **対象ファイル**: `tasks/transcribes.py`

## TASK-08: `GET /v1/transcribes/tasks/{uuid}` を実装する

- **難易度**: M
- **依存**: TASK-05, TASK-07
- **背景**: エンドポイント自体は存在するが本体が`pass`で未実装。
- **やること**:
  1. `uuid`から`Task`を検索する（`services/tasks/find_task_by_uuid`を使う、無ければ追加）
  2. `AsyncResult(task.task_id, app=celery_app)`でCeleryの状態を取得し、TASK-05の`map_celery_state`で変換する
  3. 完了していれば`TaskResult`を`task_id`で検索し、text/srtを含めて返す。失敗していれば`error_message`を返す
  4. レスポンスをTASK-05で定義したDTOで返す
- **完了条件**: 文字起こし中・完了・失敗それぞれの状態を正しく返せることを確認する（手動でも良い）
- **対象ファイル**: `v1/transcribes/__init__.py`, `services/tasks/__init__.py`

---

## Phase 2: 要約機能（`docs/specs.md` 5章）

## TASK-09: Ollama接続設定を`settings.py`に追加する

- **難易度**: S
- **依存**: なし（Phase1と並行可能）
- **やること**:
  1. `settings.py` に `ollama_host: str = "http://ollama:11434"` と `ollama_model: str = "llama3.2"` を追加する
  2. `.env.sample` にも該当項目を追記する
  3. 必要であれば`docker-compose.yml`にOllamaサービス（または既存の外部Ollamaサーバーへの接続方針）を追記する（開発者間で要相談。無ければTODOコメントで残す）
- **完了条件**: `settings.ollama_host` / `settings.ollama_model` が読み込める
- **対象ファイル**: `settings.py`, `.env.sample`

## TASK-10: `services/summaries` に要約関数を実装する

- **難易度**: M
- **依存**: TASK-09
- **背景**: 要約の精度は今回追求しない。まずOllamaを呼び出して要約文を1つ返す最小実装を作る。
- **やること**:
  1. `services/summaries/__init__.py` に `summarize(text: str) -> str` を実装する
  2. `ollama`パッケージのクライアントを使い、`settings.ollama_host`/`settings.ollama_model`宛にシンプルな要約プロンプトを送る
  3. 空文字列や極端に短い入力に対する最低限のバリデーションのみ行う（複雑なエラー処理は不要）
- **完了条件**: 適当な日本語テキストを渡すと要約文字列が返る（精度は問わない）
- **対象ファイル**: `services/summaries/__init__.py`

## TASK-11: 要約用Celeryタスクを実装する

- **難易度**: M
- **依存**: TASK-04, TASK-10
- **背景**: `tasks/transcribes.py`と同じパターンで要約タスクを実装する。
- **やること**:
  1. `tasks/summaries.py` を新規作成し、`summarize_task(self, file_id: int)` を実装する（`tasks/transcribes.py`を参考にする）
  2. 対象ファイルの文字起こし結果（`TaskResult.text` where `kind="transcribe"`）を取得し、`summarize()`に渡す
  3. 結果を新規`Task`(`kind="summarize"`)に紐づく`TaskResult`として保存する（TASK-07と同じ保存パターン）
- **完了条件**: Celeryワーカーで`summarize_task`が実行でき、`task_results`に要約結果が保存される
- **対象ファイル**: `tasks/summaries.py`(新規)

## TASK-12: `POST /v1/summaries/{file_uuid}` を実装する

- **難易度**: M
- **依存**: TASK-06, TASK-11
- **背景**: 要約は「文字起こし完了済みのファイル」に対してのみ実行できる（`docs/specs.md` 5.4）。
- **やること**:
  1. `v1/summaries/__init__.py` に`POST /{file_uuid}`エンドポイントを追加する
  2. 対象ファイルの`kind="transcribe"`かつ完了済みの`Task`/`TaskResult`が存在するか確認する。無ければ`ValidationError`（400）を返す
  3. `kind="summarize"`の`Task`を作成し（TASK-06の`create_task`を再利用）、`summarize_task.delay(file_id)`を起動する
  4. `TranscribesTaskDto`と同様の形式でタスクIDを返す
- **完了条件**: 文字起こし未完了のファイルに対して呼ぶとエラーになり、完了済みファイルに対して呼ぶと要約タスクが起動する
- **対象ファイル**: `v1/summaries/__init__.py`

## TASK-13: `GET /v1/summaries/tasks/{uuid}` を実装する

- **難易度**: S〜M
- **依存**: TASK-08
- **背景**: TASK-08で実装したロジックと同じパターン（`kind`が異なるだけ）。共通化されていればほぼそのまま使えるはずである。
- **やること**:
  1. `v1/summaries/__init__.py` に`GET /tasks/{uuid}`を追加する
  2. TASK-08で作った共通関数（`services/tasks`側の状態取得ロジック）を再利用する
- **完了条件**: 要約タスクの状態・結果が取得できる
- **対象ファイル**: `v1/summaries/__init__.py`

## TASK-14: 要約用DTOを整備する

- **難易度**: S
- **依存**: TASK-11
- **やること**:
  1. `entities/summaries/__init__.py` に `SummarizeTaskDto`（タスクID返却用）、`SummaryDto`（要約結果返却用: `summary: str`）を追加する
- **完了条件**: TASK-12, TASK-13のレスポンスモデルとして使われている
- **対象ファイル**: `entities/summaries/__init__.py`

---

## Phase 3: 音声フォーマット対応（`docs/specs.md` 6章）

## TASK-15: Dockerfileに`ffmpeg`を追加する

- **難易度**: S
- **依存**: なし
- **やること**:
  1. `docker/Dockerfile` の `apt-get install` リストに `ffmpeg` を追加する
  2. `docker compose build app` (または`batch`) でビルドが通ることを確認する
- **完了条件**: コンテナ内で `ffmpeg -version` が実行できる
- **対象ファイル**: `docker/Dockerfile`

## TASK-16: `ensure_wav_file()` をffmpegで実装する

- **難易度**: M
- **依存**: TASK-15
- **背景**: 現状`ensure_wav_file()`はWAVでなければ何もせず元のパスを返すだけ（`# TODO: convert to wav file`）。
- **やること**:
  1. `services/files/__init__.py` の `ensure_wav_file()` を実装し、`is_wav_file()`が`False`の場合は`subprocess`で`ffmpeg`を呼び出しWAVへ変換する
  2. 変換後の一時ファイルを`FILES_DIR`に保存し、変換後のパスを返す
  3. ffmpegの実行に失敗した場合は`ValidationError`等の適切な例外を投げる
- **完了条件**: mp3ファイルを渡すとWAVファイルに変換されたパスが返る
- **対象ファイル**: `services/files/__init__.py`

## TASK-17: アップロードフローに変換処理を組み込む

- **難易度**: S〜M
- **依存**: TASK-16
- **やること**:
  1. `services/files/__init__.py` の `save_file()` から `ensure_wav_file()` を呼び出すようにする
  2. 変換後のファイルに応じて `mime_type` を `audio/wav` に更新する
- **完了条件**: mp3をアップロードすると、DB上の`File.mime_type`が`audio/wav`になり、実ファイルもWAV形式で保存されている
- **対象ファイル**: `services/files/__init__.py`

---

## Phase 4: 依存整理

## TASK-18: 未使用の`pywhispercpp`を削除する

- **難易度**: S
- **依存**: なし（いつでも着手可能）
- **やること**:
  1. `pyproject.toml` の `dependencies` から `pywhispercpp` を削除する
  2. `uv sync` を実行し `uv.lock` を更新する
  3. アプリが問題なく起動することを確認する
- **完了条件**: `pywhispercpp`への参照がリポジトリ内に残っていない
- **対象ファイル**: `pyproject.toml`, `uv.lock`

---

## 依存関係まとめ（着手順の参考）

```
TASK-00 (ウォームアップ、他と独立)

TASK-01 → TASK-02 → TASK-03 → TASK-04 → TASK-05 → TASK-06 → TASK-07 → TASK-08
                                              │
TASK-09 → TASK-10 → TASK-11(depends TASK-04) → TASK-12(depends TASK-06) → TASK-13(depends TASK-08) → TASK-14

TASK-15 → TASK-16 → TASK-17   （Phase1/2と並行可能）

TASK-18   （いつでも着手可能）
```
