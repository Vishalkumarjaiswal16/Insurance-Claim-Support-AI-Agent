from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from langchain_groq import ChatGroq
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langgraph.checkpoint.memory import MemorySaver
from langgraph.config import get_config, get_store
from langgraph.prebuilt import create_react_agent
from langgraph.store.memory import InMemoryStore
from langmem import create_manage_memory_tool, create_search_memory_tool

def load_env_file(file_path: Path = Path(".env")) -> None:
	if not file_path.exists():
		return

	for raw_line in file_path.read_text(encoding="utf-8").splitlines():
		line = raw_line.strip()
		if not line or line.startswith("#") or "=" not in line:
			continue
		key, value = line.split("=", 1)
		key = key.strip()
		value = value.strip().strip('"').strip("'")
		if key and key not in os.environ:
			os.environ[key] = value


load_env_file()

google_api_key = os.getenv("GOOGLE_API_KEY")
groq_api_key = os.getenv("GROQ_API_KEY")

if not google_api_key:
	raise RuntimeError("Missing GOOGLE_API_KEY in environment variables or .env")
if not groq_api_key:
	raise RuntimeError("Missing GROQ_API_KEY in environment variables or .env")

embeddings = GoogleGenerativeAIEmbeddings(
	model="gemini-embedding-001",
	google_api_key=google_api_key,
)

llm = ChatGroq(
	model="qwen/qwen3-32b",
	groq_api_key=groq_api_key,
	temperature=0,
)

store = InMemoryStore(
	index={
		"embed": embeddings,
		"dims": 3072,
	}
)

tools = [
	create_search_memory_tool(namespace=("memories", "{langgraph_user_id}")),
	create_manage_memory_tool(namespace=("memories", "{langgraph_user_id}")),
]

checkpointer = MemorySaver()


def prompt(state: dict[str, Any]) -> list[dict[str, Any]]:
	config = get_config()
	user_id = config.get("configurable", {}).get("langgraph_user_id", "default-user")

	memory_store = get_store()
	memories = memory_store.search(("memories", user_id), limit=10)

	lines: list[str] = []
	for item in memories:
		content = item.value.get("content") if isinstance(item.value, dict) else item.value
		if content:
			lines.append(f"- {content}")

	memory_block = "\n".join(lines) if lines else "- No stored memories yet."
	system_msg = (
		"You are an insurance claim support assistant.\n"
		"Use retrieved memories when relevant.\n\n"
		f"<memories>\n{memory_block}\n</memories>"
	)

	return [{"role": "system", "content": system_msg}, *state["messages"]]


agent = create_react_agent(
	llm,
	prompt=prompt,
	tools=tools,
	store=store,
	checkpointer=checkpointer,
)


def main() -> None:
	user_id = os.getenv("LANGGRAPH_USER_ID", "customer-123")
	thread_id = os.getenv("LANGGRAPH_THREAD_ID", "thread-a")

	config = {
		"configurable": {
			"langgraph_user_id": user_id,
			"thread_id": thread_id,
		}
	}

	result = agent.invoke(
		{
			"messages": [
				{
					"role": "user",
					"content": "Do you know which display mode I prefer?",
				}
			]
		},
		config=config,
	)
	print(result["messages"][-1].content)

	result = agent.invoke(
		{
			"messages": [
				{
					"role": "user",
					"content": "I prefer dark mode. Remember that",
				}
			]
		},
		config=config,
	)
	print(result["messages"][-1].content)

	config_b = {
		"configurable": {
			"langgraph_user_id": user_id,
			"thread_id": "thread-b",
		}
	}

	result = agent.invoke(
		{
			"messages": [
				{
					"role": "user",
					"content": "This is a fresh conversation in thread-b.",
				}
			]
		},
		config=config_b,
	)
	print(result["messages"][-1].content)


if __name__ == "__main__":
	main()

