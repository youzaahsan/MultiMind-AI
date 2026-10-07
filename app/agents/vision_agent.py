from pathlib import Path
from typing import Any, Dict
from app.agents.state import AgentState, ToolCallRecord
from app.agents.tools import ToolRegistry
from app.services.llm_service import LLMService
from app.config.settings import settings

class VisionAgent:
    """Specialized agent for analyzing diagrams, charts, screenshots, and visual assets."""

    def __init__(self, tools: ToolRegistry, llm: LLMService):
        self.tools = tools
        self.llm = llm

    def run(self, state: AgentState) -> AgentState:
        query = state.resolved_query or state.user_query

        # Check if an image path was provided in state metadata
        image_path = state.metadata.get("image_path")
        if not image_path or not Path(image_path).exists():
            # Check uploads directory for latest uploaded image
            images = list(settings.UPLOAD_DIR.glob("*.png")) + list(settings.UPLOAD_DIR.glob("*.jpg"))
            if images:
                image_path = str(images[-1])

        if image_path and Path(image_path).exists():
            res = self.tools.analyze_image(image_path=image_path, prompt=query)
            state.tool_calls.append(ToolCallRecord(
                tool_name="analyze_image",
                arguments={"image_path": Path(image_path).name, "prompt": query},
                output={"dimensions": res["metadata"].get("width"), "format": res["metadata"].get("format")},
            ))
            state.final_response = res["analysis"]
            state.sources = [{"filename": Path(image_path).name, "page": 1, "section": "Visual Diagram"}]
        else:
            # Fallback analysis based on query
            state.final_response = self.llm.generate(
                prompt=f"Explain and interpret this visual diagram request: '{query}'."
            )

        return state
