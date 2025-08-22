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

os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "europe-west1")
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")

# Set up Cloud Logging
logging_client = google_cloud_logging.Client()
logger = logging_client.logger("production-adk-agent")


# Note: Weather tools removed to focus on Gemma's core conversational strengths
# For production deployments requiring tools, consider models that support function calling


# Configure the deployed model endpoint
gemma_model_name = os.getenv("GEMMA_MODEL_NAME", "gemma3:4b")  # Gemma model name

# Production Gemma Agent - GPU-accelerated conversational assistant
gemma_agent = Agent(
    model=LiteLlm(model=f"ollama_chat/{gemma_model_name}"),
    name="gemma_agent",
    description="A production-ready conversational assistant powered by GPU-accelerated Gemma.",
    instruction="""You are a friendly and helpful conversational assistant powered by the Gemma model running on Cloud Run with GPU acceleration.

You can help users with:
- General questions and conversations
- Providing information and explanations
- Creative writing and brainstorming
- Problem-solving discussions
- Educational content and explanations
- Technical concepts and programming guidance

You provide fast, accurate responses thanks to GPU acceleration. Always be helpful, friendly, and engaging in your responses. When discussing technical topics, provide clear explanations suitable for the user's level of understanding.""",
    tools=[],  # Gemma focuses on conversational capabilities
)

# Set as root agent
root_agent = gemma_agent