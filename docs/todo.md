# mnemo TODOリスト

現状のコードベースを調査し、ユーザーとの要件詰めで決定した内容を反映したTODO一覧。
詳細な仕様は `docs/specs.md`、Issue化用の小タスクは `docs/tasks.md` を参照。

凡例: `[今回対応]` = このスコープで実装する / `[将来対応]` = 今回は対応せず記録のみ

---

## 1. 認証・認可 `[将来対応]`

- [ ] APIキーによるリクエスト認証（ヘッダーで受け取り、`ApiKey.key_hash`と照合する仕組み）が未実装。現状すべてのエンドポイントが無認証で叩ける。
- [ ] `is_master`フラグを持つマスターキーの扱い（レート制限無視など）が未定義。
- [ ] `ApiKey.used_counts`はカラムがあるが、インクリメントする処理がどこにもない。
- [ ] 認証実装後、`files.owner_id` / `tasks.owner_id` を `NOT NULL` に戻し、リクエストのAPIキーから設定する処理に置き換える（今回はnullable化で暫定対応。3章「認証に関する暫定対応」参照）。

## 2. タスク永続化 `[今回対応]`

- [ ] `Task`モデルに`kind`列（`"transcribe"` / `"summarize"`）が無く、種別を区別できない。
- [ ] `Task`レコードを作成する処理がどこにも実装されていない（`v1/transcribes/__init__.py` に `# TODO: create task` コメントが残っている）。
- [ ] 文字起こし・要約結果の永続化テーブル（`TaskResult`）が存在しない。現状Celeryのresult backendに結果JSONが入るだけで、アプリ側から構造化して参照できない。
- [ ] `GET /v1/transcribes/tasks/{uuid}` エンドポイントが未実装（本文が `pass` のまま）。
- [ ] Celery状態（`AsyncResult.status`）とアプリ側ステータス（`entities/transcribes/__init__.py` の `TaskStatus` enum）のマッピング処理が存在しない。この`TaskStatus`は文字起こし専用の場所に定義されており、要約タスクでも使えるよう共通化されていない。
- [ ] タスク失敗時のエラーメッセージを保存・参照する仕組みが無い。

## 3. 要約機能 `[今回対応]`

- [ ] `models/summaries.py` がコメントアウトのままで、要約結果を保存するモデルが存在しない（→ `docs/specs.md` の方針では専用モデルではなく `TaskResult` に統合する）。
- [ ] `services/summaries/__init__.py` が空ファイルで、要約ロジックが未実装。
- [ ] `v1/summaries/__init__.py` にルーターが定義されているが、エンドポイントが一つも登録されていない。
- [ ] Ollamaへの接続設定（ホスト・モデル名）が`settings.py`に存在しない。
- [ ] 要約用のCeleryタスク（`tasks/summaries.py`）が存在しない。
- [ ] 文字起こし未完了のファイルに対して要約を要求した場合のエラーハンドリングが未定義。

## 4. 音声フォーマット対応 `[今回対応]`

- [ ] `services/files/__init__.py` の `ensure_wav_file()` はWAV変換ロジックが未実装（`# TODO: convert to wav file`）で、事実上何もしていない。
- [ ] `docker/Dockerfile` に `ffmpeg` がインストールされていない。

## 5. データ不整合・既知の不具合 `[今回対応]`

- [ ] **重大**: `services/files/__init__.py` の `save_file()` が `File` を作成する際に `owner_id` を設定していない。`File.owner_id` は現状 `nullable=False` のため、このままではアップロードAPIがDB制約違反で失敗する。
- [ ] `models/tasks.py` の `Task.owner` リレーションが `back_populates="files"` になっており、`File.owner`（`back_populates="files"`）と名前が衝突している（コピペミスと思われる。`ApiKey`側に`tasks`用のリレーションが定義されていない）。

## 6. 依存関係・環境整理 `[今回対応]`

- [ ] `pywhispercpp` が `pyproject.toml` にあるが、コード内で一度も使われていない。
- [ ] `ollama` パッケージは依存にあるが、使用箇所が無かった（→ 要約機能で使用することが確定）。

## 7. レート制限・不正利用対策 `[将来対応]`

- [ ] `FingerPrint` モデルが `models/secrets.py` 内でコメントアウトされたまま。IPベースのレート制限などが未検討。

## 8. その他、将来的な検討事項 `[将来対応]`

- [ ] 要約の精度・プロンプト改善（今回は精度を追求しない方針）。
- [ ] 多言語対応（今回は日本語のみ）。
- [ ] ポーリングAPI（`GET .../tasks/{uuid}`）をWebSocket/SSEなどのリアルタイム通知に置き換える。
- [ ] テストコード（`tests/`ディレクトリ）が現状存在しない。今回のタスクではテスト追加は必須要件にしていないが、学習目的も兼ねて各タスクで簡単なテストを書くことを推奨する。
