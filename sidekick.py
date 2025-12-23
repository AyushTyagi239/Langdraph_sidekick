from typing import Annotated, List, Any, Optional, Dict
from typing_extensions import TypedDict
from datetime import datetime
import uuid
import asyncio

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

from langchain_openai import ChatOpenAI
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
)

from sidekick_tools import playwright_tools, other_tools

load_dotenv(override=True)

# -------------------------
# STATE
# -------------------------
class State(TypedDict):
    messages: Annotated[List[Any], add_messages]
    success_criteria: str
    feedback_on_work: Optional[str]
    success_criteria_met: bool
    user_input_needed: bool


# -------------------------
# EVALUATOR OUTPUT (STRICT)
# -------------------------
class EvaluatorOutput(BaseModel):
    feedback: str = Field(
        description="Single-line feedback string. No newlines or markdown."
    )
    success_criteria_met: bool = Field(
        description="True if the success criteria has been met"
    )
    user_input_needed: bool = Field(
        description="True if the user must clarify or provide more input"
    )


# -------------------------
# SIDEKICK CLASS
# -------------------------
class Sidekick:
    def __init__(self):
        self.worker_llm_with_tools = None
        self.evaluator_llm_with_output = None
        self.tools = []
        self.graph = None
        self.sidekick_id = str(uuid.uuid4())
        self.memory = MemorySaver()
        self.browser = None
        self.playwright = None

    # -------------------------
    # SETUP
    # -------------------------
    async def setup(self):
        self.tools, self.browser, self.playwright = await playwright_tools()
        self.tools += await other_tools()

        worker_llm = ChatOpenAI(model="qwen/qwen3-next-80b-a3b-instruct")
        self.worker_llm_with_tools = worker_llm.bind_tools(self.tools)

        evaluator_llm = ChatOpenAI(model="moonshotai/kimi-k2-instruct-0905")
        self.evaluator_llm_with_output = evaluator_llm.with_structured_output(
            EvaluatorOutput
        )

        await self.build_graph()

    # -------------------------
    # WORKER NODE
    # -------------------------
    def worker(self, state: State) -> Dict[str, Any]:
        system_message = f"""
You are a helpful assistant that can use tools to complete tasks.
You should continue working until either:
- The success criteria is met, OR
- You need clarification from the user.

Rules:
- Use tools when needed.
- If using Python, include print() to return output.
- If finished, provide a final answer.
- If clarification is needed, clearly ask a question.

Current date and time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Success criteria:
{state["success_criteria"]}
""".strip()

        if state.get("feedback_on_work"):
            system_message += f"""

Previous attempt was rejected for the following reason:
{state["feedback_on_work"]}

Please correct the issue and continue.
"""

        messages = state["messages"]

        # Ensure exactly one SystemMessage
        found_system = False
        for msg in messages:
            if isinstance(msg, SystemMessage):
                msg.content = system_message
                found_system = True

        if not found_system:
            messages = [SystemMessage(content=system_message)] + messages

        response = self.worker_llm_with_tools.invoke(messages)

        return {"messages": [response]}

    # -------------------------
    # WORKER ROUTER
    # -------------------------
    def worker_router(self, state: State) -> str:
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return "evaluator"

    # -------------------------
    # FORMAT CONVERSATION
    # -------------------------
    def format_conversation(self, messages: List[Any]) -> str:
        text = ""
        for msg in messages:
            if isinstance(msg, HumanMessage):
                text += f"User: {msg.content}\n"
            elif isinstance(msg, AIMessage):
                text += f"Assistant: {msg.content or '[tool use]'}\n"
        return text.strip()

    # -------------------------
    # EVALUATOR NODE (HARDENED)
    # -------------------------
    def evaluator(self, state: State) -> State:
        last_response = state["messages"][-1].content

        system_message = """
You are an evaluator.

CRITICAL OUTPUT RULES:
- Respond ONLY with valid JSON
- feedback MUST be a single-line string
- Do NOT use newlines
- Do NOT use bullet points
- Do NOT use markdown
- Do NOT start feedback with whitespace
""".strip()

        user_message = f"""
Conversation:
{self.format_conversation(state["messages"])}

Success criteria:
{state["success_criteria"]}

Assistant final response:
{last_response}

Evaluate if the success criteria is met.
Decide if user input is required.

If the assistant claims to have written files, assume it did so.
Give benefit of the doubt, but reject if more work is needed.
""".strip()

        eval_result = self.evaluator_llm_with_output.invoke(
            [
                SystemMessage(content=system_message),
                HumanMessage(content=user_message),
            ]
        )

        return {
            "messages": [
                AIMessage(
                    content=f"Evaluator feedback: {eval_result.feedback}"
                )
            ],
            "feedback_on_work": eval_result.feedback,
            "success_criteria_met": eval_result.success_criteria_met,
            "user_input_needed": eval_result.user_input_needed,
        }

    # -------------------------
    # ROUTE BASED ON EVALUATION
    # -------------------------
    def route_based_on_evaluation(self, state: State) -> str:
        if state["success_criteria_met"] or state["user_input_needed"]:
            return END
        return "worker"

    # -------------------------
    # BUILD GRAPH
    # -------------------------
    async def build_graph(self):
        graph = StateGraph(State)

        graph.add_node("worker", self.worker)
        graph.add_node("tools", ToolNode(tools=self.tools))
        graph.add_node("evaluator", self.evaluator)

        graph.add_edge(START, "worker")
        graph.add_conditional_edges(
            "worker",
            self.worker_router,
            {"tools": "tools", "evaluator": "evaluator"},
        )
        graph.add_edge("tools", "worker")
        graph.add_conditional_edges(
            "evaluator",
            self.route_based_on_evaluation,
            {"worker": "worker", END: END},
        )

        self.graph = graph.compile(checkpointer=self.memory)

    # -------------------------
    # RUN SUPERSTEP
    # -------------------------
    async def run_superstep(self, message, success_criteria, history):
        config = {"configurable": {"thread_id": self.sidekick_id}}

        state = {
            "messages": [HumanMessage(content=message)],
            "success_criteria": success_criteria
            or "The answer should be clear and accurate",
            "feedback_on_work": None,
            "success_criteria_met": False,
            "user_input_needed": False,
        }

        result = await self.graph.ainvoke(state, config=config)

        user = {"role": "user", "content": message}
        reply = {"role": "assistant", "content": result["messages"][-2].content}
        feedback = {"role": "assistant", "content": result["messages"][-1].content}

        return history + [user, reply, feedback]

    # -------------------------
    # CLEANUP
    # -------------------------
    def cleanup(self):
        async def _cleanup():
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_cleanup())
        except RuntimeError:
            asyncio.run(_cleanup())
