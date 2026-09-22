import json
import random
from pathlib import Path

import streamlit as st

# ---------- Config ----------
DATA_FILE = Path(__file__).parent / "words.json"
DISTRACTOR_COUNT = 1  # set to 0 to disable distractor letters

st.set_page_config(page_title="Hebrew Word Builder", layout="wide")

# ---------- Data ----------
@st.cache_data
def load_words():
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)

WORDS = load_words()
ALL_LETTERS = list({letter for w in WORDS for letter in w["letters"]})

# ---------- Session state ----------
def new_round(word_index: int):
    word = WORDS[word_index]
    pool = list(word["letters"])
    if DISTRACTOR_COUNT:
        candidates = [l for l in ALL_LETTERS if l not in word["letters"]]
        pool += random.sample(candidates, min(DISTRACTOR_COUNT, len(candidates)))
    random.shuffle(pool)
    st.session_state.word_index = word_index
    st.session_state.pool = pool
    st.session_state.assembled = []
    st.session_state.status = None  # None | "correct" | "wrong"

if "word_index" not in st.session_state:
    new_round(0)

word = WORDS[st.session_state.word_index]

# ---------- Layout ----------
left, right = st.columns([1, 1], gap="large")

with left:
    st.image(str(Path(__file__).parent / word["image"]), use_container_width=True)

with right:
    st.subheader("Build the word")

    # Assembled word, displayed right-to-left explicitly
    slots = st.session_state.assembled + ["_"] * (len(word["letters"]) - len(st.session_state.assembled))
    assembled_html = " ".join(slots)
    st.markdown(
        f"""
        <div style="
            direction: rtl;
            unicode-bidi: bidi-override;
            font-size: 3rem;
            letter-spacing: 0.3rem;
            text-align: center;
            border: 2px solid #ccc;
            border-radius: 10px;
            padding: 1rem;
            margin-bottom: 1rem;">
            {assembled_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Letter bank
    st.caption("Tap the letters in order")
    cols = st.columns(len(st.session_state.pool) or 1)
    for i, letter in enumerate(st.session_state.pool):
        if cols[i].button(letter, key=f"letter_{i}_{letter}", use_container_width=True):
            st.session_state.assembled.append(letter)
            st.session_state.pool.pop(i)
            if len(st.session_state.assembled) == len(word["letters"]):
                st.session_state.status = (
                    "correct" if st.session_state.assembled == word["letters"] else "wrong"
                )
            st.rerun()

    c1, c2 = st.columns(2)
    if c1.button("↩ Undo", use_container_width=True, disabled=not st.session_state.assembled):
        last = st.session_state.assembled.pop()
        st.session_state.pool.append(last)
        st.session_state.status = None
        st.rerun()
    if c2.button("🔄 Reset word", use_container_width=True):
        new_round(st.session_state.word_index)
        st.rerun()

    # Feedback
    if st.session_state.status == "correct":
        st.success(f"✅ Correct! **{word['translit']}** — {word['gloss']}")
        if st.button("Next card ▶", type="primary"):
            new_round((st.session_state.word_index + 1) % len(WORDS))
            st.rerun()
    elif st.session_state.status == "wrong":
        st.error("❌ Not quite — try again.")
        if st.button("Try again"):
            new_round(st.session_state.word_index)
            st.rerun()
