# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from pathlib import Path
from typing import Dict, Any

from dotenv import load_dotenv
from google.adk.agents import LlmAgent, Agent
from google.adk.models.lite_llm import LiteLlm
from google.cloud import logging as google_cloud_logging
import google.auth

# Load environment variables from .env file in root directory
root_dir = Path(__file__).parent.parent
dotenv_path = root_dir / ".env"
load_dotenv(dotenv_path=dotenv_path)

# Use default project from credentials if not in .env
try:
    _, project_id = google.auth.default()
    os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project_id)
except Exception:
    # If no credentials available, continue without setting project
    pass

os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "us-central1")
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")

# Set up Cloud Logging
logging_client = google_cloud_logging.Client()
logger = logging_client.logger("production-adk-agent")


def get_weather(city: str) -> str:
    """Get current weather information for a city.

    Args:
        city (str): The city name to get weather for.

    Returns:
        str: Weather information for the city.
    """
    logger.log_text(f"--- Tool: get_weather called for city: {city} ---", severity="INFO")
    
    # Simulate weather data (in a real app, you'd call a weather API)
    weather_data = {
        "new york": "Sunny, 72°F (22°C). Light breeze from the west at 8 mph. Perfect day for outdoor activities!",
        "london": "Cloudy with light rain, 15°C (59°F). Humidity at 78%. Don't forget your umbrella!",
        "tokyo": "Partly cloudy, 18°C (64°F). Cherry blossoms are in bloom. Great weather for sightseeing.",
        "paris": "Overcast, 16°C (61°F). Light winds from the northwest. Ideal weather for museum visits.",
        "sydney": "Sunny and warm, 25°C (77°F). Perfect beach weather with gentle ocean breeze.",
        "san francisco": "Foggy morning clearing to sunny, 19°C (66°F). Classic San Francisco weather!",
        "default": "Weather information not available for this location. Try a major city like New York, London, or Tokyo."
    }
    
    city_normalized = city.lower().strip()
    return weather_data.get(city_normalized, weather_data["default"])


# Configure the deployed model endpoints
gemma_model_name = os.getenv("GEMMA_MODEL_NAME", "gemma3:4b")  # Gemma model name
llama_model_name = os.getenv("LLAMA_MODEL_NAME", "llama3.1:8b")  # Llama model name

# Gemma Agent - No tool calling support, general conversation
gemma_agent = Agent(
    model=LiteLlm(model=f"ollama_chat/{gemma_model_name}"),
    name="gemma_agent",
    description="A friendly conversational assistant powered by Gemma.",
    instruction="""You are a friendly and helpful conversational assistant powered by the Gemma model.

You can help users with:
- General questions and conversations
- Providing information and explanations
- Creative writing and brainstorming
- Problem-solving discussions
- Educational content and explanations

Since you don't have access to real-time tools, you should be clear when you cannot provide current information like live weather data or perform calculations. Instead, offer to help explain how to do these things or provide general guidance.

Always be helpful, friendly, and engaging in your responses.""",
    tools=[],  # No tools for Gemma
)

# Llama Agent - With tool calling support
llama_agent = Agent(
    model=LiteLlm(model=f"ollama_chat/{llama_model_name}"),
    name="llama_agent", 
    description="A helpful assistant with weather tools.",
    instruction="""You are a friendly and helpful assistant with access to useful tools.

Your capabilities include:
1. **Weather Information**: Get current weather conditions for major cities around the world. Call the get_weather tool for this.

When users ask about weather, use your tools to provide accurate information. Always be helpful, friendly, and provide clear responses based on the tool results. Your responses should be in text format, not JSON.""",
    tools=[get_weather],
)

# Default agent (for backward compatibility) - using Llama with tools
root_agent = llama_agent