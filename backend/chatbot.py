from dotenv import load_dotenv
from openai import OpenAI, RateLimitError
import httpx
import json
import os
import re
from rag import RAGPipeline

load_dotenv(override=True)

_VERIFY_SSL = os.getenv("SSL_VERIFY", "true").lower() != "false"

tools = []

class Me:
    def __init__(self):
        self.gemini = OpenAI(
            api_key=os.getenv("GOOGLE_API_KEY", "DUMMY_KEY"),
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            http_client=httpx.Client(verify=_VERIFY_SSL),
        )
        self.model_name = "gemma-4-26b-a4b-it"  # tried: gemma-4-26b-a4b-it (poor instruction following), gemma-4-31b-it
        self.name = "Alice"

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        docs_dir = os.path.join(base_dir, "me")

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

    def system_prompt(self, query=None, history=None):
        rag_context = ""
        if self.rag and query:
            try:
                rag_query = query
                if history:
                    recent_user = [m["content"] for m in history[-4:] if m.get("role") == "user"]
                    if recent_user:
                        rag_query = " ".join(recent_user[-2:]) + " " + query
                rag_context = self.rag.retrieve(rag_query, k=10)
            except Exception as e:
                print(f"RAG retrieval failed: {e}")

        prompt = f"""You are acting as {self.name}, an AI and data science professional. You are answering questions on {self.name}'s personal website.
Your responsibility is to represent {self.name} faithfully and to demonstrate her deep expertise in AI, machine learning, and data science.
Be professional and engaging, as if talking to a potential client or future employer.

You can answer questions about:
- {self.name}'s career, background, skills, and experience
- AI engineering, machine learning, and data science topics

When answering AI/data science questions, always use the ## Relevant Background Information section below. Even if the context is a table of contents or partial text, extract what you can and give the most useful answer possible. For example, if the context shows chapter topics, list them and explain what the chapter covers.

## Side Projects Listing Rule
When the user asks to show, list, or see Alice's side projects (e.g., "show side projects", "what projects has Alice built", "portfolio", "list of side projects"), and the retrieved context contains the "Side Projects: Master List in Priority Order" section, present ALL FIVE projects from that master list in the exact order shown. Never list only some of them, and never reorder them.

## Page Citation Rules (CRITICAL)
When the user asks where information appears in a book or document, follow these rules strictly:
1. The page number for any content MUST come from the [Source: ..., Page N] header that precedes the chunk where that content appears. Never use a different number.
2. NEVER invent a page number. If the chunks do not show a page for some information, say so.
3. Copy the source name verbatim. Do not add file extensions. Do not change the formatting.
4. The book may have its own alphabetical index (often near the end of the book). Index entries look like: "tokenization, 55, 69, 121, 260, 268; defined, 3". You can mention these as additional pages, but make clear they come from the book's own index.
5. Do NOT cite a page number for chunks whose header says "Front matter".

Do NOT offer to send messages or collect email addresses. If you truly cannot answer something, simply say you don't have enough information on that specific topic."""

        if rag_context:
            prompt += f"\n\n## Relevant Background Information:\n{rag_context}\n\n"

        prompt += f"With this context, please chat with the user, always staying in character as {self.name}."
        return prompt

    def chat(self, message, history):
        messages = [{"role": "system", "content": self.system_prompt(query=message, history=history)}]

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
                    temperature=0
                )

                if response.choices[0].finish_reason == "tool_calls":
                    message = response.choices[0].message
                    tool_calls = message.tool_calls
                    results = self.handle_tool_call(tool_calls)
                    messages.append(message)
                    messages.extend(results)
                else:
                    done = True

            except RateLimitError as e:
                print(f"Rate limit hit: {e}")
                return ("I've reached today's free usage limit for the AI service that powers me. "
                        "The quota resets every 24 hours, so please come back tomorrow to chat again. "
                        "Thank you for your patience!")
            except Exception as e:
                err_str = str(e).lower()
                if ("429" in err_str or "quota" in err_str
                        or "rate limit" in err_str or "rate_limit" in err_str
                        or "resource_exhausted" in err_str or "too many requests" in err_str):
                    print(f"Quota/rate error: {e}")
                    return ("I've reached today's free usage limit for the AI service that powers me. "
                            "The quota resets every 24 hours, so please come back tomorrow to chat again. "
                            "Thank you for your patience!")
                print(f"Error with Gemini API: {e}")
                return "Sorry, the system is currently experiencing an issue. Please try again in a moment."

        content = response.choices[0].message.content or ""
        content = re.sub(r"<thought>.*?</thought>", "", content, flags=re.DOTALL).strip()
        return content

    def chat_stream(self, message, history):
        messages = [{"role": "system", "content": self.system_prompt(query=message, history=history)}]

        for msg in history:
            if msg["role"] in ("user", "assistant"):
                messages.append({"role": msg["role"], "content": msg["content"]})

        messages.append({"role": "user", "content": message})

        try:
            stream = self.gemini.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0,
                stream=True,
            )
        except RateLimitError as e:
            print(f"Rate limit hit: {e}")
            yield ("I've reached today's free usage limit for the AI service that powers me. "
                   "The quota resets every 24 hours, so please come back tomorrow to chat again. "
                   "Thank you for your patience!")
            return
        except Exception as e:
            err_str = str(e).lower()
            if ("429" in err_str or "quota" in err_str
                    or "rate limit" in err_str or "rate_limit" in err_str
                    or "resource_exhausted" in err_str or "too many requests" in err_str):
                print(f"Quota/rate error: {e}")
                yield ("I've reached today's free usage limit for the AI service that powers me. "
                       "The quota resets every 24 hours, so please come back tomorrow to chat again. "
                       "Thank you for your patience!")
                return
            print(f"Error with Gemini API: {e}")
            yield "Sorry, the system is currently experiencing an issue. Please try again in a moment."
            return

        buffer = ""
        state = "detecting"  # detecting | skipping_thought | streaming

        try:
            for chunk in stream:
                delta = (chunk.choices[0].delta.content or "") if chunk.choices else ""
                if not delta:
                    continue

                if state == "streaming":
                    yield delta
                    continue

                buffer += delta

                if state == "detecting":
                    stripped = buffer.lstrip()
                    if stripped.startswith("<thought>"):
                        state = "skipping_thought"
                    elif len(stripped) >= 12 and not stripped.startswith("<"):
                        state = "streaming"
                        yield buffer
                        buffer = ""

                if state == "skipping_thought" and "</thought>" in buffer:
                    after = buffer.split("</thought>", 1)[1].lstrip()
                    state = "streaming"
                    buffer = ""
                    if after:
                        yield after

            if state != "streaming" and buffer:
                cleaned = re.sub(r"<thought>.*?</thought>", "", buffer, flags=re.DOTALL).strip()
                if cleaned:
                    yield cleaned
        except Exception as e:
            print(f"Stream interrupted: {e}")
            yield "\n\n[The connection was interrupted. Please try again.]"
