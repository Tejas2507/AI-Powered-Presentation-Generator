Of course. Here is a comprehensive `README.md` file for your project.

You can copy and paste the following content directly into a new file named `README.md` in the root of your project directory.

-----


# 🤖 AI Presentation Generator

[](https://www.python.org/)
[](https://fastapi.tiangolo.com/)
[](https://www.langchain.com/)
[](https://ai.google.dev/)
[](https://developer.mozilla.org/en-US/docs/Web/JavaScript)

An intelligent application that automates the creation of professional PowerPoint presentations. Simply provide a topic, and the AI will handle the research, content structuring, and slide design, delivering a downloadable `.pptx` file.

-----

## ✨ Features

  * **AI-Powered Content:** Leverages the **Google Gemini** model to generate human-like, coherent content for each slide.
  * **Real-Time Web Research:** Integrates **Tavily Search API** to gather up-to-date information, ensuring presentations are relevant and fact-based.
  * **Intelligent Slide Planning:** Uses an AI agent to create a logical 7-slide structure (Title, Agenda, 4 Key Points, Conclusion) before writing content.
  * **Dynamic Theming:** Choose from multiple design themes. The backend uses `python-pptx` to dynamically apply colors, fonts, and layouts.
  * **Streaming Progress Updates:** A responsive frontend provides a real-time log of the AI's progress, from generating search queries to creating the final file.
  * **Simple Web Interface:** A clean, easy-to-use interface built with vanilla HTML, CSS, and JavaScript.

-----

## 🛠️ Tech Stack & Architecture

The application is built with a modern, decoupled architecture. The frontend communicates with a powerful FastAPI backend that orchestrates the entire AI workflow.

### Architecture Flow

1.  **Frontend Request:** The user enters a topic and theme into the web UI and clicks "Generate." A request is sent to the backend.
2.  **Backend Orchestration (LangGraph):** The FastAPI server receives the request and triggers a **LangGraph** state machine.
3.  **Research & Planning:**
      * The graph's first nodes use the Gemini LLM to expand the topic into focused search queries.
      * The Tavily API executes these queries to fetch real-time web results.
      * Another LLM-powered node analyzes the search context to create a logical slide-by-slide plan.
4.  **Content Generation:** The graph then generates bullet points for each planned slide, ensuring the content is concise and well-formatted.
5.  **Slide Assembly (`python-pptx`):** The final node takes the structured content and uses the `python-pptx` library to programmatically build the PowerPoint presentation, applying the selected theme's colors and fonts.
6.  **File Download:** The server saves the `.pptx` file and signals completion to the frontend, enabling the download button.

----
## 🚀 Getting Started

Follow these instructions to set up and run the project locally.

### Prerequisites

  * Python 3.9 or higher
  * A virtual environment tool (like `venv`)

### Installation

1.  **Clone the repository:**

    ```sh
    git clone https://github.com/your-username/ai-presentation-generator.git
    cd ai-presentation-generator
    ```

2.  **Create and activate a virtual environment:**

      * **On macOS/Linux:**
        ```sh
        python3 -m venv venv
        source venv/bin/activate
        ```
      * **On Windows:**
        ```sh
        python -m venv venv
        .\venv\Scripts\activate
        ```

3.  **Install the required dependencies:**

    ```sh
    pip install -r requirements.txt
    ```

4.  **Set up your environment variables:**

      * Create a file named `.env` in the root of the project directory.
      * Add your API keys to this file. You will need keys for Google Gemini and Tavily.

    <!-- end list -->

    ```env
    # .env file

    # Get from Google AI Studio: https://makersuite.google.com/app/apikey
    GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY"

    # Get from Tavily: https://app.tavily.com/
    TAVILY_API_KEY="YOUR_TAVILY_API_KEY"
    ```

-----

## ▶️ Running the Application

1.  **Start the backend server:**

      * Run the following command from the project's root directory:

    <!-- end list -->

    ```sh
    uvicorn main:app --reload
    ```

      * The server will start, typically on `http://127.0.0.1:8000`.

2.  **Open the frontend:**

      * Simply open the `index.html` file in your web browser.

-----

## 📋 Usage

1.  **Open `index.html`** in your browser.
2.  **Enter a topic** for your presentation (e.g., "The Future of Renewable Energy").
3.  **Enter your name** (optional).
4.  **Select a theme** from the available options.
5.  Click the **"Generate Presentation"** button.
6.  Watch the **real-time progress log** as the AI works.
7.  Once complete, click the **"Download PowerPoint"** button.

-----

## 📂 Project Structure

```
.
├── backend/
│   ├── graph.py          # Defines the LangGraph workflow and AI agents.
│   ├── presentation.py   # Handles .pptx file creation and theming.
│   ├── schemas.py        # Pydantic models for data structures.
│   └── __init__.py
├── outputs/              # Generated PowerPoint files are saved here.
├── .env                  # Stores API keys (you must create this).
├── index.html            # The main frontend file for the user interface.
├── main.py               # FastAPI application entry point and API endpoints.
├── requirements.txt      # Lists all Python dependencies for the project.
└── README.md             # You are here!
```

-----


