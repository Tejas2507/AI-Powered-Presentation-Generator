from typing import List, Optional, Dict, TypedDict
from pydantic  import BaseModel, Field

# A model for a single summarized point with its source
class ContextPoint(BaseModel):
    fact: str = Field(description="A single, summarized key fact or piece of information.")
    source: str = Field(description="The source URL for this fact. If not found, use 'Source not found'.")

# A model for the entire structured context, organized by slide topic
class StructuredContext(BaseModel):
    context_by_slide: Dict[str, List[ContextPoint]] = Field(description="A dictionary where keys are slide titles and values are lists of relevant facts for that slide.")

# The structured plan for the presentation deck
class SlidePlan(BaseModel):
    title: str = Field(description="The main title of the presentation.")
    overview_title: str = Field(description="The title for the overview/agenda slide, e.g., 'Agenda' or 'Presentation Outline'.")
    agenda_points: List[str] = Field(description="A list of the key point titles that will be shown as the agenda.")
    key_points: List[str] = Field(description="A list of exactly 4 key topics, each as a slide title.")
    conclusion_title: str = Field(description="The title for the final slide, e.g., 'Conclusion' or 'Key Takeaways'.")

# The generated content for a single presentation slide
class SlideContent(BaseModel):
    title: str = Field(description="The title of the slide.")
    bullets: List[str] = Field(description="A list of 3-5 concise bullet points. Each bullet should be a short phrase, not a full sentence.")
    references: Optional[List[str]] = Field(default=None, description="An optional list of 1-2 source URLs that support the slide's content.")

# This is the main state that flows through the LangGraph
class GraphState(TypedDict):
    topic: str
    presenter_name: str
    sub_queries: List[str]
    search_results: List[dict]
    slide_plan: SlidePlan
    structured_context: StructuredContext
    slide_contents: List[SlideContent]
    presentation_path: str
    template_name: str
    error: str