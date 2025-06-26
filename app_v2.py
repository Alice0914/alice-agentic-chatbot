from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import requests
from pypdf import PdfReader
import streamlit as st
from datetime import datetime
import time

load_dotenv(override=True)

def push(text):
    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": os.getenv("PUSHOVER_TOKEN"),
            "user": os.getenv("PUSHOVER_USER"),
            "message": text,
        }
    )

def record_user_details(email, name="Name not provided", notes="not provided"):
    push(f"Recording {name} with email {email} and notes {notes}")
    return {"recorded": "ok"}

def record_unknown_question(question):
    push(f"Recording {question}")
    return {"recorded": "ok"}

record_user_details_json = {
    "name": "record_user_details",
    "description": "Use this tool to record that a user is interested in being in touch and provided an email address",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "description": "The email address of this user"
            },
            "name": {
                "type": "string",
                "description": "The user's name, if they provided it"
            },
            "notes": {
                "type": "string",
                "description": "Any additional information about the conversation that's worth recording to give context"
            }
        },
        "required": ["email"],
        "additionalProperties": False
    }
}

record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Always use this tool to record any question that couldn't be answered as you didn't know the answer",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question that couldn't be answered"
            },
        },
        "required": ["question"],
        "additionalProperties": False
    }
}

tools = [{"type": "function", "function": record_user_details_json},
        {"type": "function", "function": record_unknown_question_json}]

class Me:
    def __init__(self):
        google_api_key = os.getenv('GOOGLE_API_KEY')
        self.gemini = OpenAI(
            api_key=google_api_key, 
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )
        self.model_name = "gemini-2.0-flash"
        self.name = "Alice"
        
        try:
            reader = PdfReader("me/linkedin.pdf")
            self.linkedin = ""
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    self.linkedin += text
        except FileNotFoundError:
            self.linkedin = "LinkedIn profile not available"
                
        try:
            with open("me/summary.txt", "r", encoding="utf-8") as f:
                self.summary = f.read()
        except FileNotFoundError:
            self.summary = "Summary not available"

    def handle_tool_call(self, tool_calls):
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            print(f"Tool called: {tool_name}", flush=True)
            tool = globals().get(tool_name)
            result = tool(**arguments) if tool else {}
            results.append({
                "role": "tool",
                "content": json.dumps(result),
                "tool_call_id": tool_call.id
            })
        return results
    
    def system_prompt(self):
        system_prompt = f"You are acting as {self.name}. You are answering questions on {self.name}'s website and AI and data related carrer questions. \
particularly questions related to {self.name}'s career, background, skills and experience. \
Your responsibility is to represent {self.name} for interactions on the website as faithfully as possible. \
You are given a summary of {self.name}'s background and LinkedIn profile which you can use to answer questions. \
Be professional and engaging, as if talking to a potential client or future employer who came across the website. \
if user asked about questions that are not related to {self.name}'s career, background, skills and experience, tell them that you are not sure about the answer and you will send a text message to {self.name} to answer the question if users want to get in touch with {self.name}. \
If you don't know the answer to any question, use your record_unknown_question tool to record the question that you couldn't answer, even if it's about something trivial or unrelated to career. \
If you don't know the answer to any questions, tell users that you will send a text message to Alice to answer the question if users want to get in touch with Alice. If so, ask for their email and record it using your record_user_details tool. \
If the user is engaging in discussion, try to steer them towards getting in touch via email; ask for their email and record it using your record_user_details tool. "

        system_prompt += f"\n\n## Summary:\n{self.summary}\n\n## LinkedIn Profile:\n{self.linkedin}\n\n"
        system_prompt += f"With this context, please chat with the user, always staying in character as {self.name}."
        return system_prompt

    def chat(self, message, history):
        messages = [{"role": "system", "content": self.system_prompt()}]
        
        for msg in history:
            if msg["role"] == "user":
                messages.append({"role": "user", "content": msg["content"]})
            elif msg["role"] == "assistant":
                messages.append({"role": "assistant", "content": msg["content"]})
        
        messages.append({"role": "user", "content": message})
        
        done = False
        while not done:
            try:
                response = self.gemini.chat.completions.create(
                    model=self.model_name, 
                    messages=messages, 
                    tools=tools
                )
                
                if response.choices[0].finish_reason == "tool_calls":
                    message = response.choices[0].message
                    tool_calls = message.tool_calls
                    results = self.handle_tool_call(tool_calls)
                    messages.append(message)
                    messages.extend(results)
                else:
                    done = True
                    
            except Exception as e:
                print(f"Error with Gemini API: {e}")
                return "Sorry, the system is currently experiencing an issue. Please try again in a moment."
                
        return response.choices[0].message.content

st.set_page_config(
    page_title="Alice - AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)


st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .main-header h1 {
        color: white;
        text-align: center;
        margin: 0;
        font-size: 2.5rem;
        font-weight: 600;
    }
    .main-header p {
        color: white;
        text-align: center;
        margin: 0.5rem 0 0 0;
        font-size: 1.2rem;
        opacity: 0.9;
    }
    .chat-container {
        border: 1px solid #e1e5e9;
        border-radius: 10px;
        padding: 1rem;
        background-color: #fafafa;
        min-height: 400px;
        max-height: 600px;
        overflow-y: auto;
    }
    .user-message {
        background-color: #007bff;
        color: white;
        padding: 10px 15px;
        border-radius: 18px;
        margin: 5px 0;
        margin-left: 20%;
        text-align: right;
    }
    .assistant-message {
        background-color: white;
        color: #333;
        padding: 10px 15px;
        border-radius: 18px;
        margin: 5px 0;
        margin-right: 20%;
        border: 1px solid #e1e5e9;
    }
    .sidebar-info {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
    }
    .status-online {
        color: #28a745;
        font-weight: bold;
    }
    .footer {
        text-align: center;
        padding: 2rem;
        color: #6c757d;
        border-top: 1px solid #e1e5e9;
        margin-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <h1>🤖 Alice - AI Assistant</h1>
    <p>AI & Data Career Expert | Professional Consultant</p>
</div>
""", unsafe_allow_html=True)

# with st.sidebar:
#     st.markdown("### 💼 About Alice")
#     st.markdown(
#         """
#         <div class="sidebar-info">
#             <h4>🎯 Expertise</h4>
#             <ul>
#                 <li>Agentic Gen AI Data Science</li>
#                 <li>ML/DL Data Science</li>
#                 <li>Analytics Engineer</li>
#                 <li>Data Analyst</li>
#                 <li>Career Development Consultant</li>
#                 <li>AI & Data Technical Consultant</li>
#             </ul>
#         </div>
#         """, unsafe_allow_html=True)


with st.sidebar:
    st.markdown("---")
    st.markdown("### 🔧 Settings")
    
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.rerun()
    st.markdown("---")
    
    st.markdown("### 📅 Schedule a Meeting")
    
    st.markdown("""
    <div style="text-align: center; margin: 10px 0;">
        <a href="https://calendly.com/alicek0914/career-coffee-chat" 
           target="_blank" 
           style="
               display: inline-block;
               background: linear-gradient(45deg, #667eea, #764ba2);
               color: white;
               padding: 10px 20px;
               text-decoration: none;
               border-radius: 20px;
               font-weight: bold;
               font-size: 14px;
               box-shadow: 0 3px 10px rgba(0, 0, 0, 0.2);
               transition: all 0.3s ease;
               width: 90%;
           "
           onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 5px 15px rgba(0, 0, 0, 0.3)';"
           onmouseout="this.style.transform='translateY(0px)'; this.style.boxShadow='0 3px 10px rgba(0, 0, 0, 0.2)';">
           📅 Book 15-30 min Meeting
        </a>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### ✉️ Direct Contact - Linkedin")
    
    st.markdown("""
    <div style="text-align: center; margin: 8px 0;">
        <a href="https://www.linkedin.com/in/alice-k-31049b165/" 
           target="_blank"
           style="
               display: inline-block;
               background: #0077b5;
               color: white;
               padding: 8px 18px;
               text-decoration: none;
               border-radius: 18px;
               font-weight: 500;
               font-size: 13px;
               box-shadow: 0 2px 8px rgba(0, 119, 181, 0.3);
               transition: all 0.3s ease;
               width: 85%;
           "
           onmouseover="this.style.background='#005885'; this.style.transform='translateY(-1px)';"
           onmouseout="this.style.background='#0077b5'; this.style.transform='translateY(0px)';">
           💼 LinkedIn
        </a>
    </div>
    """, unsafe_allow_html=True)
    
    # st.subheader("💼 About Alice")
    # st.write("🔹ML/DL Data Science")
    # st.write("🔹Analytics Engineer") 
    # st.write("🔹Data Analyst")
    # st.write("🔹Career Development Consultant")
    # st.write("🔹AI & Data Technical Consultant")
        

    
    # st.markdown("---")
    # st.markdown("### 📧 Stay Updated")
    
    # st.markdown("""
    # <div style="
    #     background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    #     padding: 20px;
    #     border-radius: 15px;
    #     text-align: center;
    #     margin: 10px 0;
    #     box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    # ">
    #     <h4 style="color: white; margin: 0 0 10px 0;">🚀 AI Trends Newsletter</h4>
    #     <p style="color: white; margin: 0 0 15px 0; font-size: 14px;">
    #         Get the latest AI trends and insights delivered to your inbox!
    #     </p>
    # </div>
    # """, unsafe_allow_html=True)
    
    # st.markdown("""
    # <div style="text-align: center; margin: 15px 0;">
    #     <a href="https://docs.google.com/forms/d/1RZ6ABHHbYef0IBSzdisH6x6tYuuQK8pS5fBz1YfhoAc/edit" 
    #        target="_blank" 
    #        style="
    #            display: inline-block;
    #            background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
    #            color: white;
    #            padding: 12px 30px;
    #            text-decoration: none;
    #            border-radius: 25px;
    #            font-weight: bold;
    #            font-size: 16px;
    #            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    #            transition: all 0.3s ease;
    #            border: none;
    #            cursor: pointer;
    #        "
    #        onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 20px rgba(0, 0, 0, 0.3)';"
    #        onmouseout="this.style.transform='translateY(0px)'; this.style.boxShadow='0 4px 15px rgba(0, 0, 0, 0.2)';">
    #        📬 Subscribe Now
    #     </a>
    # </div>
    # """, unsafe_allow_html=True)
    
    # st.markdown("""
    # <div style="
    #     background-color: #f8f9fa;
    #     padding: 10px;
    #     border-radius: 8px;
    #     border-left: 4px solid #28a745;
    #     margin: 10px 0;
    # ">
    #     <small style="color: #666;">
    #         ✅ Weekly AI updates<br>
    #         ✅ Industry insights<br>
    #         ✅ Career tips<br>
    #         ✅ Free & No spam
    #     </small>
    # </div>
    # """, unsafe_allow_html=True)

col1, spacer, col2 = st.columns([4, 0.3, 1.5])

with col1:
    # stat_col1, stat_col2, stat_col3 = st.columns(3)
    
    # with stat_col1:
    #     current_time = datetime.now().strftime("%H:%M:%S")
    #     st.metric("🕐 Current Time", current_time)
    
    # with stat_col2:
    #     if "messages" in st.session_state:
    #         user_messages = len([m for m in st.session_state.messages if m["role"] == "user"])
    #         st.metric("👤 Your Messages", user_messages)
    #     else:
    #         st.metric("👤 Your Messages", 0)
    
    # with stat_col3:
    #     if "messages" in st.session_state:
    #         assistant_messages = len([m for m in st.session_state.messages if m["role"] == "assistant"])
    #         st.metric("🤖 My Responses", assistant_messages)
    #     else:
    #         st.metric("🤖 My Responses", 0)
    st.info("""
    💡 **Conversation Tips:**
    - “Which AI & data jobs suit my personality?”
    - “How should I prepare for a career transition?”
    - “Please recommend a curriculum for Deep Learning, LLMs, RAG, and Agentic AI?”
    """)
# Which AI & data jobs suit my personality?
# How should I prepare for a career transition?
# What’s the AI & data learning path?|
# Please recommend a curriculum for DL, LLM, RAG or Agentic AI?

    # - “Which specific roles within AI and data science would best fit my profile, considering my personality type?”
    # - “How should I prepare for and navigate a career transition into a different AI- or data-focused role, given my current background?”
    # - “Could you propose a detailed study curriculum for Deep Learning, LLMs, RAG, and Agentic AI?”
    
    
    st.markdown("---")
    st.markdown("### 💬 Chat with Alice")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.messages.append({
            "role": "assistant", 
            "content": "Hello! I'm Alice, your AI assistant. I'm here to help with questions about my career in AI and data science. Feel free to ask about my experience, skills, or if you'd like to get in touch!"
        })
    
    if "me_instance" not in st.session_state:
        st.session_state.me_instance = Me()

    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    if prompt := st.chat_input("Ask me anything about my career and experience..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = st.session_state.me_instance.chat(prompt, st.session_state.messages[:-1])
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    error_msg = "Sorry, I'm experiencing some technical difficulties. Please try again."
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

with col2:
    st.subheader("💼 About Alice")
    st.markdown("""
    <div style="
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 8px;
        border-left: 4px solid #28a745;
        margin: 10px 0;
    ">
        <div style="color: #333; font-size: 16px; font-weight: 600;">
            🔹 ML/DL Data Science<br>
            🔹 Analytics Engineer<br>
            🔹 Data Analyst<br>
            🔹 Career Development Consultant<br>
            🔹 AI & Data Technical Consultant
        </div>
    </div>
    """, unsafe_allow_html=True)
        
    # st.markdown("---")
    # st.markdown("### 🔧 Settings")
    
    # if st.button("🗑️ Clear Chat History"):
    #     st.session_state.messages = []
    #     st.rerun()
    
    st.markdown("---")
    st.markdown("### 📧 Stay Updated")
    
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        margin: 10px 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    ">
        <h4 style="color: white; margin: 0 0 10px 0;">🚀 AI Trends Newsletter</h4>
        <p style="color: white; margin: 0 0 15px 0; font-size: 14px;">
            Get the latest AI trends and insights delivered to your inbox!
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="text-align: center; margin: 15px 0;">
        <a href="https://docs.google.com/forms/d/1RZ6ABHHbYef0IBSzdisH6x6tYuuQK8pS5fBz1YfhoAc/edit" 
           target="_blank" 
           style="
               display: inline-block;
               background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
               color: white;
               padding: 12px 30px;
               text-decoration: none;
               border-radius: 25px;
               font-weight: bold;
               font-size: 16px;
               box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
               transition: all 0.3s ease;
               border: none;
               cursor: pointer;
           "
           onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 20px rgba(0, 0, 0, 0.3)';"
           onmouseout="this.style.transform='translateY(0px)'; this.style.boxShadow='0 4px 15px rgba(0, 0, 0, 0.2)';">
           📬 Subscribe Now
        </a>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 8px;
        border-left: 4px solid #28a745;
        margin: 10px 0;
    ">
        <small style="color: #666;">
            ✅ Weekly AI updates<br>
            ✅ Industry insights<br>
            ✅ Career tips<br>
            ✅ Free & No spam
        </small>
    </div>
    """, unsafe_allow_html=True)
    
    # st.markdown("---")
    # st.markdown("### 🎯 Conversation Tips")
    # st.info("""
    # 💡 **Best Questions:**
    # - "Tell me about your AI experience"
    # - "What projects have you worked on?"
    # - "How can I contact you?"
    # - "What's your background in data science?"
    # """)

# 푸터
st.markdown("""
<div class="footer">
    <p>🤖 Powered by Gemini AI | Built with Streamlit</p>
    <p><small>This AI assistant represents Alice's professional profile and expertise</small></p>
</div>
""", unsafe_allow_html=True)

if __name__ == "__main__":
    pass  # Streamlit 앱은 streamlit run 명령으로 실행됩니다
