"""LangChain Agent for Ngulisik chatbot"""
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from tools import CHATBOT_TOOLS
from prompts import SYSTEM_PROMPT
import os

def create_agent():
    """Create and return agent executor"""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not in environment")
    
    # Temperature 0 terlalu rigid, 0.3 lebih flexible namun tetap konsisten
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        api_key=api_key,
        temperature=0.3,
        top_p=0.9
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    agent = create_tool_calling_agent(llm, CHATBOT_TOOLS, prompt)
    executor = AgentExecutor(
        agent=agent,
        tools=CHATBOT_TOOLS,
        verbose=False,
        max_iterations=10,
        handle_parsing_errors=True,
        early_stopping_method="generate"
    )
    
    return executor

def chat(message: str, history: list = None):
    """
    Process user message and return response
    Add timeout handling dan better error messages
    """
    try:
        executor = create_agent()
        
        indonesian_instruction = f"Balas HANYA dalam bahasa Indonesia. Pertanyaan user: {message}"
        
        response = executor.invoke({
            "input": indonesian_instruction,
            "chat_history": history or []
        })
        
        output = response.get("output", "")
        
        if not output:
            output = "Maaf, saya mengalami kesulitan memproses pertanyaan Anda. Silahkan coba lagi."
        
        return {"status": "success", "response": output}
    except Exception as e:
        error_msg = str(e)
        return {
            "status": "error",
            "response": "Maaf, terjadi kesalahan. Silahkan coba lagi dalam beberapa saat."
        }
