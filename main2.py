# main_part1 (Streamlit) 
import io, re, requests
from io import BytesIO
import streamlit as st
from huggingface_hub import InferenceClient
import config
# Switch provider by changing the import line:
from groq_api import generate_response
from image_gen import ImageGenerator
# from hf import generate_response 

MATH_SYSTEM = """You are a Math Mastermind.
Solve with clear step-by-step reasoning, correct notation, and a final answer.
Verify when possible; mention an alternative method briefly if relevant."""

CHAT_CSS = """
<style>
.wrap {max-height: 520px; overflow-y: auto; padding-right: 6px;}
.card{border:1px solid #e6e6e6;background:#fff;border-radius:10px;padding:14px 16px;margin:10px 0;
box-shadow:0 1px 2px rgba(0,0,0,0.04);}
.q{font-weight:700;color:#0a6ebd;margin-bottom:8px;}
.meta{display:inline-block;background:#FF9800;color:#fff;padding:2px 8px;border-radius:12px;font-size:12px;margin-left:8px}
.a{white-space:pre-wrap;color:#333;line-height:1.5;}
</style>
"""

def export_txt(history):
    txt = "".join([f"Q{i}: {h['question']}\nA{i}: {h['answer']}\n\n" for i, h in enumerate(history, 1)])
    bio = io.BytesIO(txt.encode("utf-8")); bio.seek(0); return bio

def teaching_answer(q: str) -> str:
    return generate_response(q, temperature=0.3, max_tokens=1024)

def math_answer(q: str, level: str) -> str:
    prompt = f"{MATH_SYSTEM}\n\nDifficulty: {level}\nMath Problem: {q}"
    return generate_response(prompt, temperature=0.1, max_tokens=1024)

def run_ai_teacher():
    st.title("AI Teaching Assistant")
    st.session_state.setdefault("history_ata", [])
    c1, c2 = st.columns([1, 2])
    if c1.button("Clear", key="c_ata"): st.session_state.history_ata = []; st.rerun()
    if st.session_state.history_ata:
        c2.download_button("Export", export_txt(st.session_state.history_ata), 
                           "AI_Teaching_Assistant_Conversation.txt", "text/plain")
    q = st.text_input("Enter your question:", key="q_ata")
    if st.button("Ask", key="a_ata"):
        if not q.strip(): st.warning("Enter a question.")
        else:
            with st.spinner("Thinking..."):
                st.session_state.history_ata.append({"question":q.strip(), "answer":teaching_answer(q.strip())})
            st.rerun()

    if not st.session_state.history_ata: return
    st.markdown(CHAT_CSS, unsafe_allow_html=True)
    html = '<div class="wrap">'
    for i, qa in enumerate(st.session_state.history_ata, 1):
        html += f'<div class="card"><div class="q">Q{i}: {qa['question']}</div><div class="a">{qa['answer']}</div></div>'
    st.markdown(html + "</div>", unsafe_allow_html=True)

def run_math_mastermind():
    st.title("AI Math Mastermind")
    st.session_state.setdefault("history_mm", [])
    st.session_state.setdefault("k_mm", 0)
    c1, c2 = st.columns([1, 2])
    if c1.button("Clear", key="c_mm"): st.session_state.history_mm = []; st.rerun()
    if st.session_state.history_mm:
        c2.download_button("Export", export_txt(st.session_state.history_ata), 
                           "AI_Math_Mastermind_Conversation.txt", "text/plain")
    with st.form("mm_form", clear_on_submit=True):
        q = st.text_area("Math problem:", height=100, key=f"mm_{st.session_state}")
        a, b = st.columns([3, 1])
        go = a.form_submit_button("Solve", use_container_width=True)
        lvl = b.selectbox("Level", ["Basic", "Intermediate", "Advanced"], index=1)
        if go:
            if not q.strip(): st.warning("Enter a problem.")
            else:
                with st.spinner("Solving..."):
                    ans = math_answer(q.strip(), lvl)
                st.session_state.history_mm.insert(0, {"question": q.strip(), "answer":ans, "difficulty": lvl})
                st.session_state.k_mm += 1; st.rerun()

    if not st.session_state.history_ata: return
    st.markdown(CHAT_CSS, unsafe_allow_html=True)
    html = '<div class="wrap">'
    for i, qa in enumerate(st.session_state.history_mm, 1):
        html += (f'<div class="card"><div class="q">Q{i}: {qa['question']}</div>'
                 f'<span class="meta">{qa['difficulty']}</span></div>'
                 f'<div class="a">{qa['answer']}</div></div>')
    st.markdown(html + "</div>", unsafe_allow_html=True)


# ✅ placeholder: once you paste Part 2 below, safe ai image generation will work
def run_safe_ai_image_generator():
    st.set_page_config(page_title="Safe AI Image Generator", layout="centered")
    st.title("🖼️ Safe AI Image Generator")
    st.info("Flow: Enter a prompt → enhance it → check it using the deployed safety API → generate the image.")

    IG = ImageGenerator
    with st.form("image_form"):
        raw = st.text_area(
            "Image Description",
            height=120,
            placeholder="Example: A cozy cabin in snowy mountains at sunrise, cinematic lighting",
        )
        submit = st.form_submit_button("Generate Image")

    if submit:
        raw = raw.strip()

        if not raw:
            st.warning("⚠️ Please enter an image description.")
            return

        raw_check = IG.check_prompt_with_filter(prompt=raw)
        if not raw_check.get("ok"):
            st.error(f"⚠️ Prompt blocked. {raw_check.get('reason', 'Unsafe prompt')}")
            return

        with st.spinner("Enhancing your prompt..."):
            final_prompt = IG.enhance_prompt(raw)

        enhanced_check = IG.check_prompt_with_filter_api(final_prompt)
        if not enhanced_check.get("ok"):
            st.error(f"⚠️ Enhanced prompt blocked. {enhanced_check.get('reason', 'Unsafe prompt')}")
            return

        st.markdown("#### Enhanced Prompt")
        st.code(final_prompt)

        with st.spinner("Generating image..."):
            img, err = IG.gen_image(prompt=final_prompt)

        if err:
            st.error(err)
            return

        st.image(img, caption="Generated Image", use_container_width=True)
        st.session_state.generated_image = img

def main():
    st.sidebar.title("Choose an AI Feature")
    opt = st.sidebar.selectbox("", ["AI Teaching Assistant", "Math Mastermind", "Safe AI Image Generator"])
    if opt == "AI Teaching Assistant": run_ai_teacher()
    elif opt == "Math Mastermind": run_math_mastermind()
    else: run_safe_ai_image_generator()

if __name__ == "__main__":
    main()
