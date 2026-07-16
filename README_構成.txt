歌詞改行ツール 分割版

起動:
  python main.py

構成:
  main.py                         起動処理
  app/config.py                   定数・正規表現
  app/main_window.py              メイン画面と編集機能
  app/settings_store.py           settings.jsonの読み書き
  app/dialogs/settings_dialog.py  設定画面
  app/dialogs/time_tag_inspector.py タイムタグ検査画面
  app/services/update_service.py  GitHub Release確認
  app/services/part_extractor.py  パート分け抽出

追加した設定:
  part_start_char / part_end_char
  初期値は ( と )
  設定画面の「パート分け抽出設定」から変更可能
