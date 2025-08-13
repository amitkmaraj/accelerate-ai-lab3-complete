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

import random
import uuid
from locust import HttpUser, task, between


class ProductionAgentUser(HttpUser):
    """Load test user for the Production ADK Agents - Gemma (conversational) and Llama (with tools)."""
    
    wait_time = between(2, 5)  # Wait 2-5 seconds between requests to simulate real usage
    
    def on_start(self):
        """Set up user session when starting."""
        self.user_id = f"user_{uuid.uuid4()}"
        self.session_id = f"session_{uuid.uuid4()}"
        
        # Create session for the agent
        session_data = {"state": {"user_type": "general_user", "session_count": 1}}
        
        # Create sessions for both agents
        self.client.put(
            f"/apps/llama_agent/users/{self.user_id}/sessions/{self.session_id}",
            headers={"Content-Type": "application/json"},
            json=session_data,
        )
        
        self.client.put(
            f"/apps/gemma_agent/users/{self.user_id}/sessions/{self.session_id}",
            headers={"Content-Type": "application/json"},
            json=session_data,
        )

    @task(3)
    def test_weather_queries(self):
        """Test weather information capabilities."""
        # Random cities for weather queries
        cities = ["New York", "London", "Tokyo", "Paris", "Sydney", "San Francisco", "Berlin", "Miami"]
        
        city = random.choice(cities)
        
        # Vary the message format for realistic testing
        message_formats = [
            f"What's the weather like in {city}?",
            f"Can you check the weather for {city}?",
            f"How's the weather in {city} today?",
            f"Tell me about the weather in {city}",
            f"Get me the current weather for {city}",
            f"What are the weather conditions in {city}?"
        ]
        
        message_data = {
            "message": random.choice(message_formats),
            "session_id": self.session_id,
        }
        
        response = self.client.post(
            f"/apps/llama_agent/users/{self.user_id}/conversations",
            headers={"Content-Type": "application/json"},
            json=message_data,
        )
        
        if response.status_code == 200:
            data = response.json()
            # Validate response structure
            if "response" in data and "conversation_id" in data:
                self.conversation_id = data["conversation_id"]

    @task(2)
    def test_tip_calculations(self):
        """Test tip calculation capabilities."""
        # Random bill amounts and tip percentages
        bill_amounts = [25.50, 45.80, 78.25, 120.00, 89.99, 156.75, 67.40, 95.20]
        tip_percentages = [15, 18, 20, 22, 25]
        
        bill = random.choice(bill_amounts)
        tip_pct = random.choice(tip_percentages)
        
        message_formats = [
            f"Calculate the tip for a ${bill} bill with {tip_pct}% tip",
            f"What's the tip on ${bill} at {tip_pct} percent?",
            f"Help me calculate a {tip_pct}% tip on a ${bill} bill",
            f"I need to calculate the tip for ${bill} with {tip_pct}% gratuity",
            f"What should I tip on a ${bill} bill? Use {tip_pct}%",
            f"Calculate tip: bill is ${bill}, tip rate {tip_pct}%"
        ]
        
        message_data = {
            "message": random.choice(message_formats),
            "session_id": self.session_id,
        }
        
        self.client.post(
            f"/apps/llama_agent/users/{self.user_id}/conversations",
            headers={"Content-Type": "application/json"},
            json=message_data,
        )



    @task(2)
    def test_gemma_conversations(self):
        """Test conversational capabilities with Gemma agent (no tools)."""
        # General conversational topics
        conversation_topics = [
            "Tell me about artificial intelligence",
            "What are some creative writing tips?",
            "Explain how photosynthesis works",
            "What's the difference between machine learning and deep learning?",
            "Can you help me brainstorm ideas for a blog post?",
            "How do I solve quadratic equations?",
            "What are the benefits of renewable energy?",
            "Explain the concept of blockchain in simple terms"
        ]
        
        topic = random.choice(conversation_topics)
        
        message_data = {
            "message": topic,
            "session_id": self.session_id,
        }
        
        self.client.post(
            f"/apps/gemma_agent/users/{self.user_id}/conversations",
            headers={"Content-Type": "application/json"},
            json=message_data,
        )

    @task(1)
    def health_check(self):
        """Test the health endpoint."""
        self.client.get("/health")

    def on_stop(self):
        """Clean up when user session ends."""
        # Submit feedback if we have a conversation
        if hasattr(self, 'conversation_id'):
            feedback_data = {
                "score": random.randint(4, 5),  # Simulate positive feedback
                "text": "Load test feedback - both Gemma and Llama agents working well",
                "invocation_id": self.conversation_id,
                "user_id": self.user_id
            }
            
            self.client.post(
                "/feedback",
                headers={"Content-Type": "application/json"},
                json=feedback_data,
            )