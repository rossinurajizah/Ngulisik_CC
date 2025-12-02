"""
LangChain Agent untuk Ngulisik chatbot
Mengintegrasikan dengan database Ngulisik_CC yang sudah ada
"""
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_tool_calling_agent, AgentExecutor 
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.chatbot_tools import CHATBOT_TOOLS
from app.chatbot_prompts import SYSTEM_PROMPT
from config import Config
import os
import logging

# Setup logging untuk debugging
logger = logging.getLogger(__name__)

def create_agent():
    """Create dan return agent executor"""
    api_key = Config.GOOGLE_API_KEY or os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        error_msg = "GOOGLE_API_KEY tidak ditemukan di environment variables atau config.py"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info("Initializing ChatGoogleGenerativeAI with gemini-2.0-flash")
    
    # Temperature 0.3 untuk balance antara konsistensi dan fleksibilitas
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
        verbose=True,
        max_iterations=10,
        handle_parsing_errors=True,
        early_stopping_method="generate"
    )
    
    return executor


def chat(message: str, history: list = None):
    """
    Process user message dan return response
    Mendukung chat history untuk konteks yang lebih baik
    """
    try:
        executor = create_agent()
        
        # Pastikan respons dalam Bahasa Indonesia
        indonesian_instruction = f"Balas HANYA dalam bahasa Indonesia. Pertanyaan user: {message}"
        
        logger.info(f"Processing message: {message}")
        
        response = executor.invoke({
            "input": indonesian_instruction,
            "chat_history": history or []
        })
        
        output = response.get("output", "")
        
        if not output:
            output = "Maaf, saya mengalami kesulitan memproses pertanyaan Anda. Silahkan coba lagi."
        
        logger.info(f"Response: {output}")
        return {"status": "success", "response": output}
    
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error in chat function: {error_msg}", exc_info=True)
        return {
            "status": "error",
            "response": f"Maaf, terjadi kesalahan: {error_msg}. Silahkan pastikan GOOGLE_API_KEY sudah diatur."
        }
