import streamlit as st
import json
import io
import urllib.request
import urllib.error
from PIL import Image
from pathlib import Path

# ── 設定 ────────────────────────────────────────────────
CONFIG_PATH = Path.home() / ".config/vtuber-wear/config.json"

EVENTS = {
    "🎍 お正月・新年":       {"month": 1,  "keywords": "振袖 晴れ着 門松 和風"},
    "💝 バレンタイン":       {"month": 2,  "keywords": "ピンク ハート チョコ 天使"},
    "🌸 卒業・ひな祭り":     {"month": 3,  "keywords": "袴 桜 春色"},
    "🌼 入学・お花見":       {"month": 4,  "keywords": "制服 桜 春"},
    "🎏 GW・こどもの日":     {"month": 5,  "keywords": "鯉のぼり 忍者 武将"},
    "☔ 梅雨・花嫁":         {"month": 6,  "keywords": "レインコート 花嫁 白"},
    "🌟 七夕・夏前":         {"month": 7,  "keywords": "浴衣 星 天の川"},
    "🎆 夏祭り・花火":       {"month": 8,  "keywords": "浴衣 花火 かき氷"},
    "🌕 お月見・秋":         {"month": 9,  "keywords": "和服 うさぎ 月 紅葉"},
    "🎃 ハロウィン":         {"month": 10, "keywords": "魔女 吸血鬼 かぼちゃ 黒オレンジ"},
    "🍂 七五三・文化祭":     {"month": 11, "keywords": "着物 制服 学園祭"},
    "🎄 クリスマス":         {"month": 12, "keywords": "サンタ 赤白 雪 トナカイ"},
}

VIBES = ["かわいい 💕", "かっこいい ⚔️", "ふわふわ 🌸", "セクシー 🌙", "クール 🧊", "ポップ 🎨"]

HAIR_COLORS   = ["黒", "ブラック", "ネイビー（紺）", "ブラウン", "金（ブロンド）", "銀（シルバー）",
                 "白", "ピンク", "赤", "青", "緑", "紫", "グラデーション", "その他"]
HAIR_LENGTHS  = ["ショート", "ミディアム", "ロング", "ツインテール", "ポニーテール", "その他"]
EYE_COLORS    = ["茶色", "黒", "青", "緑", "赤", "金", "紫", "ピンク", "オッドアイ（左右違う）"]
SKIN_TONES    = ["標準", "白め（色白）", "日焼け（褐色）"]
BODY_TYPES    = ["標準", "小柄（ロリ系）", "スラリ（スレンダー）", "ふくよか"]

# ── ページ設定 ────────────────────────────────────────────
st.set_page_config(
    page_title="VtuberWear — AIで3日、月9,800円",
    page_icon="👘",
    layout="centered",
)

st.title("👘 VtuberWear")
st.caption("AIがあなたのキャラに合わせたイベント衣装を3日でお届けします")

st.divider()

# ── STEP 1: キャラクター情報 ──────────────────────────────
st.subheader("① キャラクター情報")

col1, col2 = st.columns(2)
with col1:
    char_name   = st.text_input("キャラ名（任意）", placeholder="例: さくら、SAGE、湊あくあ風")
    hair_color  = st.selectbox("髪の色", HAIR_COLORS)
    hair_length = st.selectbox("髪の長さ・スタイル", HAIR_LENGTHS)
with col2:
    eye_color   = st.selectbox("瞳の色", EYE_COLORS)
    skin_tone   = st.selectbox("肌の色", SKIN_TONES)
    body_type   = st.selectbox("体型", BODY_TYPES)

char_notes = st.text_area(
    "キャラの特徴・こだわり（任意）",
    placeholder="例: 猫耳あり、ツノがある、サイバーパンク系の雰囲気が好き",
    height=80,
)

model_file = st.file_uploader(
    "既存のLive2Dモデルファイル（.zip）をお持ちの場合はアップロード",
    type=["zip"],
    help="あると髪・目の色を自動解析してより正確な衣装が作れます"
)

st.divider()

# ── STEP 2: 衣装オーダー ─────────────────────────────────
st.subheader("② 衣装オーダー")

event_label = st.selectbox("イベントを選んでください", list(EVENTS.keys()))
event_info  = EVENTS[event_label]

vibe = st.select_slider("雰囲気", options=VIBES)

order_notes = st.text_area(
    "その他のご要望（任意）",
    placeholder="例: メインカラーをオレンジにしてほしい、和風より洋風で、アクセサリーを派手めに",
    height=80,
)

st.divider()

# ── STEP 3: 生成プレビュー ────────────────────────────────
st.subheader("③ コンセプト画像を生成")

st.info(f"**{event_label}** の衣装を、{hair_color}髪・{eye_color}瞳のキャラに合わせて生成します。")

if st.button("🎨  コンセプト画像を生成する", type="primary", use_container_width=True):

    # Streamlit Cloud上はsecretsから、ローカルはconfig.jsonから読む
    try:
        api_key = st.secrets["stability_api_key"]
    except Exception:
        if not CONFIG_PATH.exists():
            st.error("APIキーが設定されていません。管理者にお問い合わせください。")
            st.stop()
        with open(CONFIG_PATH) as f:
            api_key = json.load(f)["stability_api_key"]

    # プロンプト構築
    vibe_en_map = {
        "かわいい 💕": "cute kawaii",
        "かっこいい ⚔️": "cool and stylish",
        "ふわふわ 🌸": "fluffy and soft",
        "セクシー 🌙": "elegant and alluring",
        "クール 🧊": "cool and sophisticated",
        "ポップ 🎨": "colorful and pop art",
    }
    hair_en_map = {
        "黒": "black", "ブラック": "black", "ネイビー（紺）": "dark navy blue",
        "ブラウン": "brown", "金（ブロンド）": "blonde", "銀（シルバー）": "silver",
        "白": "white", "ピンク": "pink", "赤": "red", "青": "blue",
        "緑": "green", "紫": "purple", "グラデーション": "gradient colorful", "その他": "",
    }
    eye_en_map = {
        "茶色": "brown", "黒": "black", "青": "blue", "緑": "green",
        "赤": "red", "金": "golden", "紫": "purple", "ピンク": "pink",
        "オッドアイ（左右違う）": "heterochromia eyes",
    }

    prompt = (
        f"anime vtuber character, {hair_en_map.get(hair_color, '')} hair, "
        f"{eye_en_map.get(eye_color, '')} eyes, "
        f"{event_info['keywords']} themed costume, "
        f"{vibe_en_map.get(vibe, 'cute')} style, "
        f"full body standing pose, flat 2D cel shading anime illustration, "
        f"clean line art, white background, high quality"
    )
    if order_notes:
        prompt += f", {order_notes}"

    negative = "realistic, photo, 3d render, blurry, nsfw, multiple characters, bad anatomy"

    boundary = "vtwboundary"
    def mp(name, value, filename=None, ctype=None):
        if filename:
            return (f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"; '
                    f'filename="{filename}"\r\nContent-Type: {ctype}\r\n\r\n').encode() + value + b"\r\n"
        return f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode()

    body = (
        mp("prompt", prompt) +
        mp("negative_prompt", negative) +
        mp("aspect_ratio", "9:16") +
        mp("output_format", "png") +
        f"--{boundary}--\r\n".encode()
    )

    req = urllib.request.Request(
        "https://api.stability.ai/v2beta/stable-image/generate/core",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "image/*",
            "User-Agent": "Mozilla/5.0",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        }
    )

    with st.spinner("AIが衣装を考えています... 約30秒お待ちください"):
        try:
            with urllib.request.urlopen(req, timeout=90) as res:
                img = Image.open(io.BytesIO(res.read()))
                st.image(img, caption=f"{event_label} コンセプト画像", use_container_width=True)
                st.success("生成完了！このデザインをベースに3日以内に衣装データをお届けします。")

                buf = io.BytesIO()
                img.save(buf, format="PNG")
                st.download_button(
                    "📥 コンセプト画像をダウンロード",
                    data=buf.getvalue(),
                    file_name=f"vtuberwear_{event_label.split()[1]}_concept.png",
                    mime="image/png",
                    use_container_width=True,
                )
        except urllib.error.HTTPError as e:
            st.error(f"生成エラー: {e.code} — {e.read().decode()[:200]}")

st.divider()
st.caption("VtuberWear | 月9,800円〜 | 最短3日納品 | 30日動作保証")
