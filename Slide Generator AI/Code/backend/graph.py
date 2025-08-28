import os
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_tavily import TavilySearch
from langgraph.graph import StateGraph, END
from pydantic import BaseModel
from .schemas import GraphState, SlidePlan, SlideContent, StructuredContext, ContextPoint
from typing import List

load_dotenv()

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.3)
search_tool = TavilySearch(max_results=4)


def expand_queries(state: GraphState):
    """Node to expand the user's topic into multiple focused sub-queries."""
    print("--- 🔍 Expanding Queries ---")
    topic = state["topic"]
    
    class SubQueries(BaseModel):
        queries: List[str]
    
    query_expander_llm = llm.with_structured_output(SubQueries)
    
    prompt = f"""
    You are an expert research assistant. Your goal is to generate search queries that will find broad and reliable information for a presentation on "{topic}".

    Instructions:
    1.  Create 4-5 diverse search queries.
    2.  Cover: causes, impacts, benchmarks/**statistics** , policies/solutions, and future outlook.
    3.  **Favor broader keywords and simpler questions** over long, academic questions and Try to get statistics (accurate numbers) if possible.
    4.  Focus on core aspects of the topic that are likely to have good search results. ***Think in terms of keywords you would use on a search engine.***

    ---
    ### Example 1: Technology / Business
    Topic: "Applications of AI in Finance"
    - "AI use cases in banking and fintech 2025"
    - "Algorithmic trading using machine learning"
    - "Fraud detection with AI in banking"
    - "Statistics on AI reducing financial fraud and risk"
    - "Future of AI in finance and fintech"
    
    ### Example 2: History
    Topic: "British Rule in India"
    - "Economic impact of British rule on India"
    - "Social reforms during the British Raj"
    - "Indian independence movement key events"
    - "Legacy of British colonialism in India"

    ### Example 3: Science / Health
    Topic: "CRISPR Gene Editing"
    - "How CRISPR-Cas9 works"
    - "Ethical concerns of human gene editing"
    - "CRISPR applications in medicine and agriculture"
    - "Future of CRISPR technology"

    ### Example 4: Environment / Social Issues
    Topic: "Global Water Scarcity"
    - "Causes of global water shortages"
    - "Impact of water scarcity on communities: health and migration statistics 2024"
    - "Solutions for water conservation and management"
    - "Countries most affected by water crisis: recent data and future projections"
    
    ### Example 5: Digital Economy
    Topic: "The Creator Economy"
    - "How the creator economy works on YouTube and TikTok"
    - "Monetization strategies for content creators 2024/5"
    - "Creator economy market size and growth statistics"
    - "Future of creator economy and web3 platforms"
    
    ---

    Based on these instructions and examples, generate the search queries for the topic: "{topic}"
    """
    try:
        result = query_expander_llm.invoke(prompt)
        return {"sub_queries": result.queries}
    except Exception as e:
        return {"error": f"Failed to expand queries: {e}"}



def web_search(state: GraphState):
    """Node to perform web search, correctly parsing the dictionary output from TavilySearch."""
    print("--- 👨‍💻 Performing Web Search for Sub-Queries ---")
    queries = state["sub_queries"]
    all_results = []
    for query in queries:
        print(f"  -> Searching: '{query}'")
        try:
            result_dict = search_tool.invoke({"query": query})
            if isinstance(result_dict, dict) and "results" in result_dict:
                valid_results = [res for res in result_dict["results"] if isinstance(res, dict) and "url" in res]
                all_results.extend(valid_results)
        except Exception as e:
            print(f"Error searching for query '{query}': {e}")

    if not all_results:
        print("  -> Warning: Web search returned no valid results.")
        return {"search_results": []} 
    
    unique_results = list({res["url"]: res for res in all_results}.values())
    return {"search_results": unique_results}

def plan_content(state: GraphState):
    """Node to create a structured plan for the presentation. Runs BEFORE summarization."""
    print("--- 📝 Planning Content Structure ---")
    topic = state["topic"]
    search_results = state.get("search_results", [])
    if not search_results:
        context = f"General knowledge about {topic}."
    else:
        context = "\n".join([res["content"] for res in search_results])
    
    planner_llm = llm.with_structured_output(SlidePlan)
    prompt = f"""
    You are an expert presentation designer. Your goal is to transform raw information into a compelling and logical 7-slide plan for a content-rich presentation on the topic: '{topic}'. Each of the four key point slides must be planned to support 4-6 distinct bullet points.

    Use the following slide-by-slide guide to structure the entire presentation:

    Slide 1: (Main Title) : The title must be engaging and capture the core theme of the presentation.

    Slide 2: (Overview) : The title should be straightforward (e.g., 'Overview', 'Our Roadmap'). Its content will be the titles of the four key point slides.

    Slide 3 (The Hook): The first key point. Should introduce the core concept or the central problem to establish why the topic is important.

    Slide 4 (The Build-Up): The second key point. Should explain the key factors, causes, or processes involved.

    Slide 5 (The Core Message): The third key point. Must focus on the most significant impacts, real-world applications, or challenges.

    Slide 6 (The Outlook): The fourth key point. Should discuss solutions, future trends, or the lasting legacy.

    Slide 7: (Conclusion): The title should be conclusive (e.g., 'Key Takeaways', 'The Path Forward'). It summarizes the main message of the presentation.

    Crucial Rules for All Titles:

    - Be Descriptive: Create engaging, descriptive titles that are specific enough to be filled with 4-6 points.

    - Avoid Generic Labels: You must not use generic, one-word titles like "Introduction," "Impact," "Causes," "Data," or "Conclusion."
    
    - **Format Requirement:** All key point and conclusion titles **must** be in a ** "Main Title - Subtitle" ** format. The hyphen is essential for the design.
    
    - *Format Requirement:** All key point and conclusion titles **must be less than 7 words**

    - Good Example: Instead of "Impact," a good title is "Financial Disruption - The Economic Ripple Effect."

    - Bad Example: "Causes."

    Context:
    {context}
    """
    try:
        plan = planner_llm.invoke(prompt)
        return {"slide_plan": plan}
    except Exception as e:
        return {"error": f"Failed to generate a valid presentation plan: {e}"}

def summarize_results(state: GraphState):
    """
    Node to summarize results into a flat list of facts, then categorize them in Python.
    This avoids the Pydantic JSON Schema error with nested models.
    """
    print("--- 📚 Structuring and Distilling Information ---")
    topic = state["topic"]
    search_results = state["search_results"]
    plan = state["slide_plan"]
    
    class Fact(BaseModel):
        """A single fact with its source and assigned slide title."""
        fact: str
        source: str
        slide_title: str

    class FactList(BaseModel):
        """A list of facts."""
        facts: List[Fact]

    slide_titles = [plan.overview_title] + plan.key_points
    context_str = "\n".join([f"Source: {res['url']}\nContent: {res['content']}" for res in search_results])

    summarizer_llm = llm.with_structured_output(FactList)
    prompt = f"""
    You are an expert data analyst. Your task is to extract key facts from the provided context and assign each fact to a relevant slide.
    The presentation is on "{topic}" and the slide titles are: {', '.join(slide_titles)}.

    Raw search snippets:
    {context_str}

    Instructions:
    1.    Analyze & Synthesize: Read all snippets. Identify the most important facts, statistics, and key points. Synthesize related information from different sources into a single, well-phrased fact. Do not just copy-paste raw sentences.

    2.    Categorize with Best Fit: Assign each synthesized fact to only one slide title from the provided list. Choose the category that is the most direct and logical fit.

    3.    Ensure Uniqueness: Your final output must not contain duplicate or repetitive facts. Each fact should represent a distinct piece of information.

    4.    Attribute Sources Reliably: Every fact must be paired with its source URL. If a specific source is unclear, use the main URL of the document it came from.

    5.    Discard Irrelevant Info: If a fact does not clearly align with any of the slide titles, do not include it.
    
    6.    Try to include facts and figures or accurate statisctics from the search as much as possible ( its important strictly to **not hallucinate**)
    
    7.  **Return a flat list of these fact objects.**
    """
    try:
        fact_list_obj = summarizer_llm.invoke(prompt)
        facts = fact_list_obj.facts if fact_list_obj else []

        context_by_slide = {title: [] for title in slide_titles}
        for fact in facts:
            if fact.slide_title in context_by_slide:
                context_by_slide[fact.slide_title].append(ContextPoint(fact=fact.fact, source=fact.source))

        return {"structured_context": StructuredContext(context_by_slide=context_by_slide)}

    except Exception as e:
        print(f"  -> Error: Failed to generate structured summary: {e}")
        return {
            "structured_context": StructuredContext(context_by_slide={}),
            "error": "Failed to generate structured summary."
        }

def generate_slide_content(state: GraphState):
    """Node to generate the content for each slide using the structured context."""
    print("--- ✍️ Generating Slide Content from Structured Context ---")
    topic = state["topic"]
    
    plan = state["slide_plan"]

    structured_context_obj = state.get("structured_context")
    structured_context_map = structured_context_obj.context_by_slide if structured_context_obj else {}
    
    all_slide_contents = []
    content_generator_llm = llm.with_structured_output(SlideContent)

    # Title & Agenda Slides
    all_slide_contents.append(SlideContent(title=plan.title, bullets=[], references=[]))
    all_slide_contents.append(SlideContent(title=plan.overview_title, bullets=plan.agenda_points, references=[]))

    # Key Point Slides
    for slide_title in plan.key_points:
        print(f"  -> Generating content for slide: '{slide_title}'")
        slide_specific_context = structured_context_map.get(slide_title, [])
        context_str = "\n".join([f"- {p.fact} [Source: {p.source}]" for p in slide_specific_context])

        prompt = f"""
        You are creating a slide titled "{slide_title}" for a presentation on "{topic}".
        Use ONLY the facts provided below for this specific slide. If context is empty, state that.

        Context for "{slide_title}":
        {context_str}

        Rules:
        - Generate 4-5 bullet points based *only* on the provided context [Exact 4 is the best].
        
        - Synthesize, Don't Just List: Do not simply turn each fact into a bullet point. Where possible, combine multiple related facts from the context into a single, more insightful bullet point.
        
        -  **Use the "Two-Part" Style:** Each bullet point **must** use the **"main phrase – clarifying detail"** format.
        
        -  **Concise but Complete:** The entire bullet point (both parts combined) should be strictly **15-20 words.** This provides enough detail without overflowing the slide.
        
        - To emphasize key terms, wrap them in bold markdown like this : **word** (Use this for main phrase).
        
        - You can create sub-points for more detailed explanations by indenting a line with two spaces.
        
        - Use __underline markdown__ (`__word__`) to emphasize important names or terms. (Use this for clarifying phrase)
        
        - **From the context, select the 1-2 most relevant source URLs to list as references.**
        """ 
        try:
            slide_content = content_generator_llm.invoke(prompt)
            all_slide_contents.append(slide_content)
        except Exception as e:
            all_slide_contents.append(SlideContent(title=slide_title, bullets=["Content generation failed."], references=[]))

    # Conclusion Slide
    print(f"  -> Generating content for conclusion slide: {plan.conclusion_title}")
    prompt = f"""
    - You are writing the final conclusion slide titled {plan.conclusion_title} for a presentation on {topic}.
    
    - Your task is to write 3-4 final summary statements that encapsulate the presentation's main points.
    
    - **Concise but Complete:** The entire bullet point should be strictly **13-16 words.** This provides enough detail without overflowing the slide. []  
     
    - These must be declarative sentences summarizing key findings.
    
    - **Do NOT give instructions, suggestions, or calls to action.**
    
    - To emphasize key terms, wrap them in bold markdown like this : **word**.
    - Use __underline markdown__ (`__word__`) to emphasize important names or terms. (Use this for clarifying phrase)
    
    - Example of a good takeaway: "AI-driven algorithms now process over 70% of market trades."
    
    Use the full context to inform your summary:
    {[res['content'] for res in state['search_results']]}
    """
    try:
        conclusion_content = content_generator_llm.invoke(prompt)
        all_slide_contents.append(conclusion_content)
    except Exception as e:
        all_slide_contents.append(SlideContent(title=plan.conclusion_title, bullets=["Summary generation failed."], references=[]))

    return {"slide_contents": all_slide_contents}

def create_presentation(state: GraphState):
    """Node to create the final .pptx file."""
    print("--- 🧑‍🎨 Creating PowerPoint File ---")
    from .presentation import create_presentation_file
    try:
        path = create_presentation_file(
            topic=state["topic"],
            presenter_name=state["presenter_name"],
            template_name=state["template_name"],
            slide_contents=state["slide_contents"]
        )
        return {"presentation_path": path}
    except Exception as e:
        return {"error": f"Failed to create the .pptx file: {e}"}

workflow = StateGraph(GraphState)

workflow.add_node("expand_queries", expand_queries)
workflow.add_node("web_search", web_search)
workflow.add_node("plan_content", plan_content)
workflow.add_node("summarize_results", summarize_results)
workflow.add_node("generate_slide_content", generate_slide_content)
workflow.add_node("create_presentation", create_presentation)

workflow.set_entry_point("expand_queries")
workflow.add_edge("expand_queries", "web_search")
workflow.add_edge("web_search", "plan_content")
workflow.add_edge("plan_content", "summarize_results")
workflow.add_edge("summarize_results", "generate_slide_content")
workflow.add_edge("generate_slide_content", "create_presentation")
workflow.add_edge("create_presentation", END)

app_graph = workflow.compile()
print("✅ LangGraph v4 compiled successfully!")