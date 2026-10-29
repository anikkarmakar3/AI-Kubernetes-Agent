
from langchain.agents import create_agent
from langchain_ollama import ChatOllama

from tools import list_files, read_file, write_file
from planner import load_specification, build_review_prompt

MODEL = "qwen3:8b"

llm = ChatOllama(
    model=MODEL,
    temperature=0,
)

system_prompt = """
You are an autonomous local coding agent working in an existing repository.

The user has already authorized implementation when they explicitly ask
you to implement, fix, or complete a project.

MANDATORY WORKFLOW:

1. Call list_files to inspect the existing project.
2. Locate the prompts/ directory.
3. Call read_file on EVERY Markdown file in prompts/.
4. Read relevant existing source code before making changes.
5. Treat each Markdown file as a project specification.
6. Identify the requirements from all prompt files.
7. Determine which requirements are already implemented and which
   are incomplete or missing.
8. Implement the requested work in dependency order.
9. Use write_file for actual source-code changes.
10. Verify each proposed change and report any limitations.

IMPLEMENTATION RULES:

- Never claim to have inspected a file unless you actually read it.
- Never ask whether to review or implement something the user has
  already explicitly requested.
- Do not stop after listing files or describing a plan.
- Continue implementing until the requested scope is completed,
  a genuine blocker occurs, or the user must make a decision.
- Preserve existing working functionality.
- Make small, focused changes instead of rewriting the whole project.
- Never modify the Markdown specification files.
- Never claim tests passed unless they were actually executed.
- If the task is too large for one pass, implement one coherent
  milestone at a time and report the remaining work.
- Explain any missing tools or capabilities honestly.

TOOLS:

Use list_files to discover project files.
Use read_file to inspect actual file contents.
Use write_file to create or modify permitted source files.
The write_file tool requires user approval for each change.

Start by inspecting the repository. Then execute the requested work.
"""

agent = create_agent(
    model=llm,
    tools=[list_files, read_file, write_file],
    system_prompt=system_prompt,
)


def main():
    print("\nLocal Ollama Coding Agent")
    print("Type 'review' to inspect your specification.")
    print("Type 'exit' to quit.\n")

    while True:
        request = input("You: ").strip()

        if request.lower() in {"exit", "quit"}:
            break

        if not request:
            continue

        try:
            if request.lower() == "review":
                spec_path, specification = load_specification()
                request = build_review_prompt(
                    spec_path,
                    specification,
                )

            result = agent.invoke({
                "messages": [
                    {"role": "user", "content": request}
                ]
            })

            for message in result["messages"]:
                if getattr(message, "type", "") == "ai":
                    if message.content:
                        print(f"\nAgent: {message.content}\n")

        except Exception as exc:
            print(f"\nError: {type(exc).__name__}: {exc}\n")


if __name__ == "__main__":
    main()

