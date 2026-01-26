# server.py
import asyncio
import os
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import Tool, TextContent
from groq import Groq

# Initialize Groq client (reads GROQ_API_KEY from environment)
groq_client = Groq()

server = Server("groq-helper")

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    return [
        Tool(
            name="ask_larger_model",
            description="""Use this powerful 70B parameter model when you need help with:
            - Questions requiring deep knowledge or expertise
            - Complex reasoning, analysis, or problem-solving
            - Detailed explanations of technical topics
            - Current events or recent information
            - When you're uncertain about your answer
            
            This model is much larger and more capable than you, so use it for challenging questions.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The question or task to send to the larger model"
                    }
                },
                "required": ["question"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "ask_larger_model":
        question = arguments["question"]
        
        try:
            # Call Groq API with Llama 70B
            completion = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "user", "content": question}
                ],
                temperature=0.7,
                max_completion_tokens=4096,
                stream=False
            )
            
            answer = completion.choices[0].message.content
            
            return [
                TextContent(
                    type="text",
                    text=answer
                )
            ]
        except Exception as e:
            return [
                TextContent(
                    type="text",
                    text=f"Error calling larger model: {str(e)}"
                )
            ]

async def main():
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="groq-helper",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())