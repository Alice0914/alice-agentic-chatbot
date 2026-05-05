from dotenv import load_dotenv
from openai import OpenAI
import json
import os
from rag import RAGPipeline

load_dotenv(override=True)

tools = []

class Me:
    def __init__(self):
        self.gemini = OpenAI(
            api_key=os.getenv("GOOGLE_API_KEY", "DUMMY_KEY"),
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )
        self.model_name = "gemini-2.0-flash"
        self.name = "Alice"

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        docs_dir = os.path.join(base_dir, "me")

        try:
            with open(os.path.join(docs_dir, "summary.txt"), "r", encoding="utf-8") as f:
                self.summary = f.read()
        except FileNotFoundError:
            self.summary = "Summary not available"

        try:
            self.rag = RAGPipeline(docs_dir)
            print("RAG pipeline ready.")
        except Exception as e:
            print(f"RAG initialization failed: {e}")
            self.rag = None

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

    def system_prompt(self, query=None):
        rag_context = ""
        if self.rag and query:
            try:
                rag_context = self.rag.retrieve(query, k=10)
            except Exception as e:
                print(f"RAG retrieval failed: {e}")

        prompt = f"""You are acting as {self.name}, an AI and data science professional. You are answering questions on {self.name}'s personal website.
Your responsibility is to represent {self.name} faithfully and to demonstrate her deep expertise in AI, machine learning, and data science.
Be professional and engaging, as if talking to a potential client or future employer.

You can answer questions about:
- {self.name}'s career, background, skills, and experience
- AI engineering, machine learning, and data science topics

When answering AI/data science questions, always use the ## Relevant Background Information section below. Even if the context is a table of contents or partial text, extract what you can and give the most useful answer possible. For example, if the context shows chapter topics, list them and explain what the chapter covers.

Do NOT offer to send messages or collect email addresses. If you truly cannot answer something, simply say you don't have enough information on that specific topic."""

        prompt += f"\n\n## Summary:\n{self.summary}\n\n"

        if rag_context:
            prompt += f"## Relevant Background Information:\n{rag_context}\n\n"

        prompt += f"With this context, please chat with the user, always staying in character as {self.name}."
        return prompt

    def chat(self, message, history):
        messages = [{"role": "system", "content": self.system_prompt(query=message)}]

        for msg in history:
            if msg["role"] in ("user", "assistant"):
                messages.append({"role": msg["role"], "content": msg["content"]})

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
