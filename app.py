import streamlit as st
import os
import time
import datetime # ログ記録のために datetime をインポート

# --- 定数 ---
UPLOAD_DIR = "uploads"
LOGIN_LOG_FILE = "login_log.txt" # ログファイル名

# --- パスワード確認関数 (変更なし) ---
def check_password():
    """パスワードが環境変数 'PASS_KEY' と一致するか確認し、認証状態を返す"""
    PASSWD = os.environ.get('PASS_KEY')
    if not PASSWD:
        st.error("エラー: 環境変数 'PASS_KEY' が設定されていません。")
        st.stop()

    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    password = st.text_input("パスワードを入力してください", type="password", key="password_input")

    if password:
        if password == PASSWD:
            # ★ 認証成功時に Session State を True にする（ログ記録のトリガーになる）
            st.session_state.authenticated = True
        else:
            st.session_state.authenticated = False
            st.error("パスワードが違います。")

    return st.session_state.authenticated

# --- Session State 初期化 ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'file_to_delete_on_next_run' not in st.session_state:
    st.session_state.file_to_delete_on_next_run = None
if 'logged_this_session' not in st.session_state:
    st.session_state.logged_this_session = False # このセッションでログインログを記録したか

# --- ファイル削除処理関数 (変更なし) ---
def delete_file_if_scheduled():
    """Session State に削除がスケジュールされたファイルがあれば削除する"""
    file_path_to_delete = st.session_state.get('file_to_delete_on_next_run', None)
    if file_path_to_delete:
        st.session_state.file_to_delete_on_next_run = None
        if os.path.exists(file_path_to_delete):
            try:
                os.remove(file_path_to_delete)
                st.success(f"ファイル '{os.path.basename(file_path_to_delete)}' はサーバーから削除されました。", icon="✅")
                st.rerun()
            except Exception as e:
                st.error(f"ファイル '{os.path.basename(file_path_to_delete)}' の削除中にエラーが発生しました: {e}")
        else:
            st.warning(f"削除予定だったファイル '{os.path.basename(file_path_to_delete)}' は見つかりませんでした。")
            st.rerun()

# --- ダウンロードボタンのコールバック関数 (変更なし) ---
def schedule_file_deletion(file_path):
    """ダウンロードボタンクリック時に、次の実行で削除するファイルをスケジュール"""
    # st.session_state.file_to_delete_on_next_run = file_path

# --- 手動で選択したファイルを即座に削除する関数 ---
def delete_selected_file(file_path):
    """選択されたファイルを即時に削除します"""
    try:
        os.remove(file_path)
        st.success(f"ファイル '{os.path.basename(file_path)}' を削除しました。", icon="✅")
        st.rerun()
    except Exception as e:
        st.error(f"ファイル '{os.path.basename(file_path)}' の削除中にエラーが発生しました: {e}")

# --- ★★★ 新しい関数：ログインログ記録 ★★★ ---
def log_login_event():
    """ログイン成功イベントをログファイルに記録する"""
    try:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{now} - Login successful\n"
        # ファイルに追記モード ('a') で書き込む
        with open(LOGIN_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        # ログ記録のエラーは警告にとどめ、アプリの動作は続行する
        st.warning(f"ログインログの記録に失敗しました: {e}", icon="⚠️")

# --- ★★★ 新しい関数：ログインログ表示 ★★★ ---
def display_login_log():
    """ログインログファイルの内容をアプリ下部に表示する"""
    st.markdown("---") # 区切り線
    st.subheader("ログイン履歴")
    try:
        if os.path.exists(LOGIN_LOG_FILE):
            with open(LOGIN_LOG_FILE, "r", encoding="utf-8") as f:
                # ファイルの内容を行ごとに読み込み、逆順にする（最新のログを上に）
                log_lines = f.readlines()
                log_content = "".join(reversed(log_lines)) # リストを逆順にして結合

            if log_content:
                # ログが多い場合に備えて Expander を使う
                with st.expander("履歴を表示/非表示", expanded=False): # 初期状態は閉じる
                    # text_area を disabled=True にして読み取り専用にする
                    st.text_area(
                        "Log",
                        log_content,
                        height=300, # 高さを適宜調整
                        key="log_display_area",
                        disabled=True
                    )
            else:
                st.info("ログイン履歴はありません。")
        else:
            st.info("ログイン履歴はありません。（ログファイル未作成）")
    except Exception as e:
        st.error(f"ログインログの読み込み中にエラーが発生しました: {e}")


# --- メイン アプリケーション ロジック ---
def main():
    st.title("ファイル・シェア＆リレー・削除アプリ")

    # --- 1. パスワード認証 ---
    is_authenticated = check_password() # 認証状態を取得・更新

    if not is_authenticated:
        # 認証されていない場合はパスワード入力欄が表示される (check_password内)
        # メッセージは初回表示時やエラー時のみ表示するのが親切かも
        # if 'password_input' in st.session_state and st.session_state.password_input: # 何か入力があった場合
        #     # パスワードが間違っている場合のメッセージは check_password 内で表示される
        #     pass
        # else:
        #     st.info("アプリケーションにアクセスするにはパスワードを入力してください。")
        st.stop() # 認証されるまでここで停止

    # --- 認証成功後の処理 ---
    # 認証成功メッセージ (セッションで1回だけ表示するなら logged_this_session を流用しても良い)
    st.success("認証成功！", icon="🎉")

    # --- 1.1 ★★★ ログインログ記録 (認証成功直後、セッションで1回のみ) ★★★ ---
    if not st.session_state.get('logged_this_session', False):
        log_login_event() # ログファイルに記録
        st.session_state.logged_this_session = True # このセッションでは記録済みとする

    # --- 1.5 スケジュールされたファイル削除を実行 (変更なし) ---
    delete_file_if_scheduled()

    # --- 2. アップロードディレクトリ作成 (変更なし) ---
    if not os.path.exists(UPLOAD_DIR):
        try:
            os.makedirs(UPLOAD_DIR)
        except OSError as e:
            st.error(f"アップロードディレクトリ '{UPLOAD_DIR}' の作成に失敗しました: {e}")
            st.stop()

    # --- 3. ファイルアップロード機能 (変更なし、time.sleep含む) ---
    st.header("ファイルのアップロード")
    uploaded_files = st.file_uploader(
        "ここにファイルをドラッグ＆ドロップするか、クリックして選択してください",
        accept_multiple_files=True,
        key="file_uploader"
    )
    if uploaded_files:
        upload_success_count = 0
        upload_error = False
        for uploaded_file in uploaded_files:
            filename = os.path.basename(uploaded_file.name)
            save_path = os.path.join(UPLOAD_DIR, filename)
            try:
                with open(save_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                upload_success_count += 1
            except Exception as e:
                st.error(f"ファイル '{filename}' の保存中にエラー: {e}")
                upload_error = True
        if upload_success_count > 0:
            st.success(f"{upload_success_count}個のファイルをアップロードしました。", icon="🚀")
            time.sleep(0.5) # ファイルシステム反映待ち
            st.rerun()
        elif upload_error:
             st.warning("一部ファイルのアップロードに失敗しました。")


    # --- 4. ファイルリスト表示とダウンロード機能 (変更なし) ---
    st.header("ファイルのダウンロードと削除")
    try:
        if os.path.isdir(UPLOAD_DIR):
            files = sorted([f for f in os.listdir(UPLOAD_DIR) if os.path.isfile(os.path.join(UPLOAD_DIR, f))])
        else:
            files = []
            st.info(f"アップロードディレクトリ '{UPLOAD_DIR}' が見つかりません。")
    except Exception as e:
        st.error(f"ファイルリストの取得中にエラーが発生しました: {e}")
        files = []

    if not files:
        st.info("ダウンロード可能なファイルはありません。")
    else:
        selected_file = st.selectbox(
            "ダウンロードするファイルを選択してください:",
            options=["---"] + files,
            key="selected_file_to_download"
        )
        if selected_file != "---":
            file_path = os.path.join(UPLOAD_DIR, selected_file)
            if os.path.exists(file_path):
                try:
                    file_size = os.path.getsize(file_path)
                    st.write(f"選択中のファイル: {selected_file} ({file_size / 1024:.2f} KB)")
                    with open(file_path, "rb") as fp:
                        file_data = fp.read()
                    st.download_button(
                        label=f"'{selected_file}' をダウンロード",
                        data=file_data,
                        file_name=selected_file,
                        mime='application/octet-stream',
                        key=f"download_button_{selected_file}",
                        on_click=schedule_file_deletion,
                        args=(file_path,)
                    )
                    st.caption("ボタンをクリックするとダウンロードが開始されます。")
                except Exception as e:                                                      
                      st.error(f"ファイル '{selected_file}' の処理中にエラーが発生しました:   {e}")  

    # --- 手動ファイル削除 UI ---
    if files:
        file_to_delete = st.selectbox(
            "削除したいファイルを選択してください",
            options=["---"] + files,
            key="file_to_delete_select"
        )
        if file_to_delete != "---":
            delete_path = os.path.join(UPLOAD_DIR, file_to_delete)
            if st.button("削除"):
                delete_selected_file(delete_path)

# --- アプリケーション実行のエントリポイント (変更なし) ---
if __name__ == "__main__":
    if not os.environ.get('PASS_KEY'):
        st.error("重大なエラー: 環境変数 'PASS_KEY' が設定されていません。アプリケーションを起動できません。")
        st.stop()
    main()