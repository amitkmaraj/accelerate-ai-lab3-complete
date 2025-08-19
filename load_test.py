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
    """Load test user for the Production ADK Agent - Gemma conversational agent."""
    
    wait_time = between(1, 3)  # Faster requests to trigger scaling
    
    def on_start(self):
        """Set up user session when starting."""
        self.user_id = f"user_{uuid.uuid4()}"
        self.session_id = f"session_{uuid.uuid4()}"
        
        # Create session for the Gemma agent using proper ADK API format
        session_data = {"state": {"user_type": "load_test_user"}}
        
        self.client.post(
            f"/apps/gemma_agent/users/{self.user_id}/sessions/{self.session_id}",
            headers={"Content-Type": "application/json"},
            json=session_data,
        )

    @task(4)
    def test_conversations(self):
        """Test conversational capabilities - high frequency to trigger scaling."""
        topics = [
            "What is machine learning?",
            "Explain cloud computing",
            "Tell me about renewable energy",
            "What are the benefits of AI?",
            "How does quantum computing work?",
            "Describe blockchain technology",
            "What is sustainable development?",
            "Explain neural networks"
        ]

        # Use proper ADK API format for sending messages
        message_data = {
            "app_name": "gemma_agent",
            "user_id": self.user_id,
            "session_id": self.session_id,
            "new_message": {
                "role": "user",
                "parts": [{
                    "text": random.choice(topics)
                }]
            }
        }

        self.client.post(
            "/run",
            headers={"Content-Type": "application/json"},
            json=message_data,
        )

    @task(1)
    def health_check(self):
        """Test the health endpoint."""
        self.client.get("/health")