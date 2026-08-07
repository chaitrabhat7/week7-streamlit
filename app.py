import streamlit as st
import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You are Archimedes, a warm and encouraging CBSE Mathematics tutor for Class 8, 9 and 10 students.
Students follow NCERT textbooks.

YOUR TEACHING STYLE:
You teach exactly like an experienced Indian maths tutor who knows her students well.

STEP 1 - GAUGE FIRST:
- From the chat history, judge if this topic is fresh or familiar to the student.
- If it's the first time they're asking about this concept, assume it's new.

STEP 2 - IF TOPIC IS NEW:
- Give a brief, friendly introduction to the concept first.
- Then show them HOW to solve it directly using your signature tricks.
- Never jump to Socratic method on a brand new topic — they have nothing to work with yet.

STEP 3 - YOUR SIGNATURE TRICKS (always prefer these over textbook methods):
- For linear equations like x + 2 = 5: teach them to MOVE the number to the other side and FLIP the sign (+ becomes -, × becomes ÷). Never say "do the same operation on both sides" — that's textbook language, not how you teach.
- Always teach the fastest, most intuitive shortcut first. Textbook method only if they ask why it works.

STEP 4 - IF TOPIC IS FAMILIAR OR STUDENT HAS SOME IDEA:
- Use the Socratic method — ask guiding questions that lead them to the answer themselves.
- Judge receptiveness from chat history. If they respond well to questions, keep going.
- If they seem lost after 1-2 Socratic attempts, switch to direct explanation immediately.

STEP 5 - ENCOURAGEMENT:
- Always acknowledge correct answers warmly, but don't be repetitive about it.
- Never sound like a broken record.

STEP 6 - CHECKING ANSWERS:
- ALWAYS verify the student's answer mathematically before responding.
- Use the appropriate verification method for the topic:
  - Equations: substitute back and check if LHS = RHS
  - Geometry: check if the logic/theorem was applied correctly
  - Arithmetic: reverse the operation to verify
- If correct, praise warmly and move on.
- If wrong, NEVER say "Perfect!", "Correct!" or "Well done!".
- Instead, guide them to verify it themselves using the appropriate check method.
- Only praise after the correct answer is confirmed.

YOUR BOUNDARIES:
- Only discuss Maths topics relevant to Class 8-10 NCERT syllabus.
- Warmly redirect if student goes off topic.
- Never do homework directly — guide them to the answer, don't give it."""

# --- Initialize session state FIRST ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Page Config ---
st.set_page_config(page_title="Archimedes", page_icon="🧮", layout="centered")

# --- Sidebar ---
with st.sidebar:
    st.title("⚙️ Settings")
    grade = st.selectbox("Class", ["Class 8", "Class 9", "Class 10"])
    topic = st.selectbox("Topic", ["Algebra", "Geometry", "Trigonometry", "Statistics"])
    st.divider()
    uploaded_file = st.file_uploader("📄 Upload NCERT Chapter (PDF or TXT)", type=["pdf", "txt"])
    st.divider()
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
    st.caption("Archimedes — CBSE Maths Tutor")

# --- Main Area ---
st.title("🧮 Archimedes")
st.subheader(f"Your CBSE {grade} Maths Tutor")
st.divider()

# --- Chapter indicator ---
if st.session_state.get("loaded_file"):
    st.success(f"📖 Answering from: **{st.session_state.loaded_file}**")
else:
    st.warning("⚠️ No chapter uploaded — Archimedes is using general knowledge. Upload a chapter PDF from the sidebar for focused practice.")

# --- Display chat history ---
for message in st.session_state.messages:
    st.chat_message(message["role"]).write(message["content"])

# --- Handle new input ---
user_input = st.chat_input("Type your maths question here...")

# --- Extract text from uploaded file ---
# --- Extract text from uploaded file ---
if uploaded_file:
    if uploaded_file.name != st.session_state.get("loaded_file"):
        if uploaded_file.type == "text/plain":
            st.session_state.chapter_text = uploaded_file.read().decode("utf-8")
        elif uploaded_file.type == "application/pdf":
            try:
                import PyPDF2
                pdf_reader = PyPDF2.PdfReader(uploaded_file)
                st.session_state.chapter_text = ""
                for page in pdf_reader.pages:
                    st.session_state.chapter_text += page.extract_text()
            except Exception as e:
                st.error(f"❌ Could not read PDF: {e}")
        st.session_state.loaded_file = uploaded_file.name
        st.success(f"✅ Loaded: {uploaded_file.name}")

chapter_text = st.session_state.get("chapter_text", "")

if user_input:
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.chat_message("user").write(user_input)

    # Call Claude API with grade context
    with st.spinner("Archimedes is thinking..."):
        # Build system prompt based on whether a file is uploaded
        if chapter_text:
            active_system = SYSTEM_PROMPT + f"\n\nThe student is in {grade}. You are answering STRICTLY from this uploaded chapter: '{st.session_state.loaded_file}'.\nContent:\n{chapter_text}\n\nAlways remind the student which chapter you are teaching from if they seem confused."
        else:
            active_system = SYSTEM_PROMPT + f"\n\nThe student is in {grade}. No chapter is uploaded. Use your general NCERT knowledge."
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=500,
            system=active_system,
            messages=st.session_state.messages
        )
        reply = response.content[0].text

    # Add assistant reply to history
    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.chat_message("assistant").write(reply)
    