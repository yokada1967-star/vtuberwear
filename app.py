import streamlit as st
import json
import io
import base64
import urllib.request
import urllib.error
from PIL import Image
from pathlib import Path

CONFIG_PATH = Path.home() / ".config/vtuber-wear/config.json"

EVENTS = {
    "🎍 お正月・新年":   {"month": 1,  "costume": "wearing a furisode kimono with obi sash, new year decorations, red and gold Japanese traditional dress"},
    "💝 バレンタイン":   {"month": 2,  "costume": "wearing a pink frilly dress with heart accessories, angel wings, holding chocolates, Valentine's Day theme"},
    "🌸 卒業・ひな祭り": {"month": 3,  "costume": "wearing a hakama over kimono, cherry blossom petals falling, graduation ceremony outfit"},
    "🌼 入学・お花見":   {"month": 4,  "costume": "wearing a cute school uniform, cherry blossom viewing party, spring floral accessories"},
    "🎏 GW・こどもの日": {"month": 5,  "costume": "wearing a kunoichi ninja outfit or samurai armor, Japanese warrior style"},
    "☔ 梅雨・花嫁":     {"month": 6,  "costume": "wearing a white wedding dress with veil, holding flower bouquet, rainy season theme"},
    "🌟 七夕・夏前":     {"month": 7,  "costume": "wearing a yukata with star pattern, Tanabata festival, Milky Way decorations, summer night"},
    "🎆 夏祭り・花火":   {"month": 8,  "costume": "wearing a yukata with floral pattern and obi sash, summer festival, fireworks in background, holding a fan"},
    "🌕 お月見・秋":     {"month": 9,  "costume": "wearing a traditional Japanese kimono, autumn leaves, full moon, rabbit motif accessories"},
    "🎃 ハロウィン":     {"month": 10, "costume": "wearing a witch costume with pointy hat, black and orange dress with ruffles, holding a pumpkin, Halloween night"},
    "🍂 七五三・文化祭": {"month": 11, "costume": "wearing a colorful kimono with elaborate accessories, autumn festival"},
    "🎄 クリスマス":     {"month": 12, "costume": "wearing a Santa Claus outfit with fur trim, red and white, Christmas tree and snow in background"},
}

VIBES = ["かわいい 💕", "かっこいい ⚔️", "ふわふわ 🌸", "セクシー 🌙", "クール 🧊", "ポップ 🎨"]
HAIR_COLORS   = ["黒", "ブラック", "ネイビー（紺）", "ブラウン", "金（ブロンド）", "銀（シルバー）",
                 "白", "ピンク", "赤", "青", "緑", "紫", "グラデーション", "その他"]
HAIR_LENGTHS  = ["ショート", "ミディアム", "ロング", "ツインテール", "ポニーテール", "その他"]
EYE_COLORS    = ["茶色", "黒", "青", "緑", "赤", "金", "紫", "ピンク", "オッドアイ（左右違う）"]
SKIN_TONES    = ["標準", "白め（色白）", "日焼け（褐色）"]
BODY_TYPES    = ["標準", "小柄（ロリ系）", "スラリ（スレンダー）", "ふくよか"]

st.set_page_config(
    page_title="VtuberWear — AIで3日、月9,800円",
    page_icon="👘",
    layout="centered",
)

# ── カスタムCSS ──────────────────────────────────────────
st.markdown("""
<style>
/* フォント・全体 */
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700;900&display=swap');
html, body, [class*="css"] { font-family: 'Noto Sans JP', sans-serif; }

/* ヒーロー */
.hero {
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    border-radius: 16px;
    padding: 2.5rem 2rem;
    text-align: center;
    margin-bottom: 1.5rem;
}
.hero-title {
    font-size: 2.4rem;
    font-weight: 900;
    color: white;
    letter-spacing: 0.04em;
    margin-bottom: 0.4rem;
}
.hero-sub {
    font-size: 1rem;
    color: #C4B5FD;
    margin-bottom: 1.5rem;
}
.hero-badges {
    display: flex;
    justify-content: center;
    gap: 0.75rem;
    flex-wrap: wrap;
}
.badge {
    background: rgba(255,255,255,0.12);
    border: 1px solid rgba(255,255,255,0.25);
    border-radius: 999px;
    padding: 0.3rem 0.9rem;
    font-size: 0.82rem;
    color: white;
    font-weight: 700;
}

/* ステップ */
.steps {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
    margin-bottom: 1.5rem;
}
.step-card {
    background: #F5F3FF;
    border: 1px solid #DDD6FE;
    border-radius: 12px;
    padding: 1.1rem 0.875rem;
    text-align: center;
}
.step-num {
    font-size: 0.65rem;
    font-weight: 800;
    letter-spacing: 0.12em;
    color: #7C3AED;
    text-transform: uppercase;
    margin-bottom: 0.3rem;
}
.step-icon { font-size: 1.5rem; margin-bottom: 0.3rem; }
.step-title { font-size: 0.82rem; font-weight: 700; color: #1E1B4B; margin-bottom: 0.2rem; }
.step-desc  { font-size: 0.72rem; color: #6B7280; line-height: 1.4; }

/* B2Bバナー */
.b2b-banner {
    background: #FFFBEB;
    border: 1.5px solid #F59E0B;
    border-radius: 12px;
    padding: 1.1rem 1.25rem;
    margin-top: 2rem;
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
}
.b2b-icon { font-size: 1.4rem; flex-shrink: 0; }
.b2b-text h4 { font-size: 0.88rem; font-weight: 800; color: #92400E; margin-bottom: 0.2rem; }
.b2b-text p  { font-size: 0.78rem; color: #78350F; line-height: 1.5; margin: 0; }

/* セクション見出し */
.section-label {
    font-size: 0.65rem;
    font-weight: 800;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #7C3AED;
    margin-bottom: 0.25rem;
}
</style>
""", unsafe_allow_html=True)

# ── ヒーロー ─────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <div class="hero-title">👘 VtuberWear</div>
  <div class="hero-sub">AIがあなたのキャラに合わせたイベント衣装を最短3日でお届け</div>
  <div class="hero-badges">
    <span class="badge">月額 9,800円〜</span>
    <span class="badge">最短3日納品</span>
    <span class="badge">年12イベント対応</span>
    <span class="badge">30日動作保証</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── サービスの流れ ─────────────────────────────────────
st.markdown("""
<div class="steps">
  <div class="step-card">
    <div class="step-num">Step 01</div>
    <div class="step-icon">📋</div>
    <div class="step-title">キャラ情報を入力</div>
    <div class="step-desc">髪・瞳の色、体型、<br>イベントを選ぶだけ</div>
  </div>
  <div class="step-card">
    <div class="step-num">Step 02</div>
    <div class="step-icon">🤖</div>
    <div class="step-title">AIが即座に生成</div>
    <div class="step-desc">30秒でコンセプト画像を<br>自動生成</div>
  </div>
  <div class="step-card">
    <div class="step-num">Step 03</div>
    <div class="step-icon">📦</div>
    <div class="step-title">Live2Dデータを納品</div>
    <div class="step-desc">最短3日で<br>すぐ使えるデータをお届け</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── サンプルギャラリー ────────────────────────────────────
st.markdown('<div class="section-label">✨ 生成サンプル</div>', unsafe_allow_html=True)
st.caption("同じキャラクター（紺髪・金瞳）で2つのイベント衣装を生成した例")

col_a, col_b = st.columns(2)
samples_dir = Path(__file__).parent / "samples"
with col_a:
    yukata_path = samples_dir / "yukata.png"
    if yukata_path.exists():
        st.image(str(yukata_path), caption="🎆 夏祭り・花火大会（浴衣）")
with col_b:
    halloween_path = samples_dir / "halloween.png"
    if halloween_path.exists():
        st.image(str(halloween_path), caption="🎃 ハロウィン（魔女衣装）")

st.divider()

# ── STEP 1: キャラクター情報 ──────────────────────────────
st.markdown('<div class="section-label">① キャラクター情報</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    char_name   = st.text_input("キャラ名（任意）", placeholder="例: さくら、SAGE、湊あくあ風")
    hair_color  = st.selectbox("髪の色", HAIR_COLORS)
    hair_length = st.selectbox("髪の長さ・スタイル", HAIR_LENGTHS)
with col2:
    eye_color   = st.selectbox("瞳の色", EYE_COLORS)
    skin_tone   = st.selectbox("肌の色", SKIN_TONES)
    body_type   = st.selectbox("体型", BODY_TYPES)

EYE_COLORS_SIMPLE = [c for c in EYE_COLORS if c != "オッドアイ（左右違う）"]
eye_left = eye_right = None
if eye_color == "オッドアイ（左右違う）":
    st.caption("左右それぞれの色を選んでください")
    col_l, col_r = st.columns(2)
    with col_l:
        eye_left  = st.selectbox("左目の色", EYE_COLORS_SIMPLE, key="eye_l")
    with col_r:
        eye_right = st.selectbox("右目の色", EYE_COLORS_SIMPLE, key="eye_r")

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
st.markdown('<div class="section-label">② 衣装オーダー</div>', unsafe_allow_html=True)

event_label = st.selectbox("イベントを選んでください", list(EVENTS.keys()))
event_info  = EVENTS[event_label]
vibe        = st.select_slider("雰囲気", options=VIBES)

order_notes = st.text_area(
    "その他のご要望（任意）",
    placeholder="例: メインカラーをオレンジにしてほしい、和風より洋風で、アクセサリーを派手めに",
    height=80,
)
st.caption("※ AIへの追加指示は **英語** で書くとより正確に反映されます。例: `front facing face`, `orange color scheme`")

st.divider()

# ── STEP 3: 生成 ──────────────────────────────────────────
st.markdown('<div class="section-label">③ コンセプト画像を生成</div>', unsafe_allow_html=True)
st.info(f"**{event_label}** の衣装を、{hair_color}髪・{eye_color}瞳のキャラに合わせて生成します。")

if st.button("🎨  コンセプト画像を生成する", type="primary", use_container_width=True):

    try:
        api_key = st.secrets["openai_api_key"]
    except Exception:
        if not CONFIG_PATH.exists():
            st.error("APIキーが設定されていません。管理者にお問い合わせください。")
            st.stop()
        with open(CONFIG_PATH) as f:
            api_key = json.load(f)["openai_api_key"]

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
    }
    hair_length_en_map = {
        "ショート": "short hair", "ミディアム": "medium length hair", "ロング": "long hair",
        "ツインテール": "twin tails hairstyle", "ポニーテール": "ponytail hairstyle", "その他": "",
    }
    skin_en_map = {
        "標準": "", "白め（色白）": "very pale white skin, fair complexion",
        "日焼け（褐色）": "dark tanned brown skin, sun-kissed dark complexion",
    }
    body_en_map = {
        "標準": "", "小柄（ロリ系）": "petite small body",
        "スラリ（スレンダー）": "slender slim body", "ふくよか": "curvy body",
    }

    if eye_color == "オッドアイ（左右違う）" and eye_left and eye_right:
        l = eye_en_map.get(eye_left, '')
        r = eye_en_map.get(eye_right, '')
        eye_desc = f"{l} left eye and {r} right eye, heterochromia"
        eye_priority = f"heterochromia eyes: left eye {l}, right eye {r}. "
    else:
        eye_desc = f"{eye_en_map.get(eye_color, '')} eyes"
        eye_priority = ""

    skin_desc = skin_en_map.get(skin_tone, "")
    hair_desc = f"{hair_en_map.get(hair_color, '')} hair, {hair_length_en_map.get(hair_length, '')}".strip(", ")
    char_parts = [hair_desc, eye_desc, skin_desc, body_en_map.get(body_type, "")]
    char_desc  = ", ".join(p for p in char_parts if p)

    prompt = (
        f"{eye_priority}"
        f"beautiful anime girl vtuber, {char_desc}, "
        f"{event_info['costume']}, "
        f"{vibe_en_map.get(vibe, 'cute kawaii')} expression, "
        f"realistic anime proportions, tall slender figure, NOT chibi, "
        f"high quality anime illustration, detailed cel shading with highlights and shadows, "
        f"beautiful detailed eyes, intricate fabric texture, "
        f"professional anime key visual style, masterpiece quality, "
        f"full body standing pose, white background"
    )
    if char_notes:
        prompt += f", {char_notes}"
    if order_notes:
        prompt += f", {order_notes}"

    body = json.dumps({
        "model": "gpt-image-1",
        "prompt": prompt,
        "n": 1,
        "size": "1024x1536",
        "quality": "high",
    }).encode()

    req = urllib.request.Request(
        "https://api.openai.com/v1/images/generations",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
    )

    with st.spinner("AIが衣装を考えています... 約30秒お待ちください"):
        try:
            with urllib.request.urlopen(req, timeout=120) as res:
                result = json.loads(res.read())
                img_data = base64.b64decode(result["data"][0]["b64_json"])
                img = Image.open(io.BytesIO(img_data))
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
            st.error(f"生成エラー: {e.code} — {e.read().decode()[:300]}")

# ── B2Bバナー ─────────────────────────────────────────────
st.markdown("""
<div class="b2b-banner">
  <div class="b2b-icon">🏢</div>
  <div class="b2b-text">
    <h4>事務所・イベント会社のご担当者様へ</h4>
    <p>所属タレントへの一括提供プランをご用意しています。<br>
    複数キャラクターの衣装を月額でまとめてご発注いただけます。<br>
    お問い合わせ: <strong>yoshihiro.okada@miraivision.co.jp</strong></p>
  </div>
</div>
""", unsafe_allow_html=True)

st.divider()
st.caption("VtuberWear | 株式会社mirAI | 月9,800円〜 | 最短3日納品 | 30日動作保証")
