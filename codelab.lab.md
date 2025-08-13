---
description: In this codelab, you'll learn how to deploy your ADK agent to production on Cloud Run, connecting it to deployed Llama models for scalable AI applications.
id: accelerate-ai-lab3/cloud-run-deployment
keywords: docType:Codelab
analytics_account: UA-49880327-14
analytics_ga4_account:
authors: Google Cloud AI Team
project: /devsite/_project.yaml
book: /devsite/_book.yaml
layout: scrolling
---

# Lab 3: Deploy Your ADK Agent to Cloud Run with Llama Integration

## Before you begin

Duration: 2:00

Welcome to the final lab in the "Accelerate with AI" series! In this lab, you'll complete the prototype-to-production journey by taking a working ADK agent and deploying it as a scalable, robust application on Google Cloud Run with GPU support.

The key focus of this lab is **modifying your agent to call the deployed version of Llama on Cloud Run**, transforming your local prototype into a production-ready service that can handle real-world traffic.

### Prerequisites

- Google Cloud Project with billing enabled
- Google Cloud SDK installed and configured (`gcloud` command available)
- Basic understanding of containers and cloud deployment
- Completion of Lab 2 (or familiarity with ADK agents)

### What you learn

- How to modify ADK agents to use deployed Llama models on Cloud Run
- How to containerize ADK agents using Docker
- How to deploy containerized agents to Cloud Run with GPU acceleration
- How to manage production configurations and environment variables
- How to test and monitor live applications in production
- How to apply load testing to validate performance and scalability

### What you need

- A Google Cloud Project with billing enabled
- Terminal or command line access
- Text editor for configuration files

## Understanding the Production Architecture

Duration: 5:00

Before we dive into deployment, let's understand what we're building and how the deployed Llama integration works.

### Agent Architecture Overview

```

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Request  │ -> │  Llama Agent    │ -> │  Llama Model    │
│                 │    │                 │    │  (Cloud Run)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              v
                       ┌─────────────────┐
                       │  Weather Tool   │
                       │                 │
                       └─────────────────┘
```

### Key Components

You'll be working with these important files:

- **`production_agent/agent.py`**: Contains an ADK agent - Llama (with tools)
- **`server.py`**: FastAPI server with health checks and feedback endpoints
- **`Dockerfile`**: Container configuration for Cloud Run deployment
- **`load_test.py`**: Locust-based load testing script

### The Llama Integration Focus

The core learning objective of this lab is understanding how to **modify your agent to make requests to deployed Llama models** rather than running models locally. This involves:

1. **Configuring model endpoints**: Setting up your agent to call the deployed Llama service
2. **Environment management**: Managing API endpoints and authentication
3. **Production scaling**: Handling multiple concurrent requests to the deployed model

> aside positive
> The deployed Llama model runs on Cloud Run with GPU acceleration, providing much better performance and scalability than local execution.

## Set Up Your Development Environment

Duration: 10:00

Let's start by setting up the local development environment and understanding the agent configuration.

### Navigate to the Lab Directory

```bash
cd accelerate-ai-lab3
```

### Create Environment Configuration

The key to connecting to the deployed Llama model is proper environment configuration. Create your `.env` file:

```bash
cat > .env << EOF
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GEMMA_MODEL_NAME=gemma3:4b
LLAMA_MODEL_NAME=llama3.2:3b
OLLAMA_API_BASE=https://ollama-gemma-795845071313.europe-west1.run.app
EOF
```

> aside negative
> **Important**: Replace `your-project-id` with your actual Google Cloud Project ID. The `OLLAMA_API_BASE` URL points to the pre-deployed Llama service that your agent will call.

### Install Dependencies

```bash
# Install all required dependencies
uv sync
```

### Understanding the Agent Configuration

Let's examine how the agent is configured to use the deployed Llama model. Open `production_agent/agent.py` and look at this key section:

```python
# Configure the deployed model endpoints
gemma_model_name = os.getenv("GEMMA_MODEL_NAME", "gemma3:4b")
llama_model_name = os.getenv("LLAMA_MODEL_NAME", "llama3.1:8b")

# Llama Agent - With tool calling support
llama_agent = Agent(
    model=LiteLlm(model=f"ollama_chat/{llama_model_name}"),
    name="llama_agent",
    description="A helpful assistant with weather tools.",
    instruction="""You are a friendly and helpful assistant with access to useful tools.

Your capabilities include:
1. **Weather Information**: Get current weather conditions for major cities around the world.

When users ask about weather, use your tools to provide accurate information.""",
    tools=[get_weather],
)
```

The `LiteLlm` model configuration automatically uses the `OLLAMA_API_BASE` environment variable to connect to the deployed Llama service instead of running locally.

## Test the Agent Locally

Duration: 10:00

Before deploying to production, let's test that our agent can successfully connect to the deployed Llama model.

### Start the Development Server

```bash
# Start the local server
uv run python server.py
```

You should see output indicating the server is running:

```console
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080
```

### Access the Web Interface

The agent will be available at `http://localhost:8080`. You can:

- Visit the web interface at `http://localhost:8080`
- View API documentation at `http://localhost:8080/docs`
- Test the health endpoint at `http://localhost:8080/health`

### Test Agent Capabilities

Now let's test both agents to ensure they're working with the deployed models:

**Test the Gemma Agent** (Conversational):

Try these sample interactions by selecting "gemma_agent" in the web interface:

- "Tell me about artificial intelligence"
- "What are some creative writing tips?"
- "Explain how photosynthesis works"

**Test the Llama Agent** (With Tools):

Select "llama_agent" and try these interactions:

- "What's the weather like in New York?"
- "How's the weather in Tokyo today?"
- "Can you tell me about the weather in London?"

> aside positive
> Notice how the Llama agent can use the `get_weather` tool, while the Gemma agent provides conversational responses without tools. Both are now using deployed models via the API endpoint!

### Verify the Connection

Check your terminal output. You should see log messages indicating successful connections to the deployed Llama service. If you see connection errors, verify your `.env` configuration.

## Understanding Containerization

Duration: 5:00

Now let's examine how the agent is containerized for production deployment. Understanding the `Dockerfile` is crucial for production deployment.

### Examine the Dockerfile

Open the `Dockerfile` in your editor:

```dockerfile
# Use Python 3.13 slim base image for efficiency
FROM python:3.13-slim

# Add uv package manager for fast dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install system dependencies
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Set working directory and copy files
WORKDIR /app
COPY . .

# Install Python dependencies using uv
RUN uv sync --frozen

# Expose port and start the application
EXPOSE 8080
CMD ["uv", "run", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Key Production Considerations

**Slim Base Image**:

- Reduces attack surface and image size
- Faster deployment and startup times

**UV Package Manager**:

- Provides faster dependency resolution than pip
- Better for production builds

**Frozen Dependencies**:

- `uv sync --frozen` ensures reproducible builds
- Prevents dependency conflicts in production

**Health Checks**:

- Built-in `/health` endpoint for monitoring
- Used by Cloud Run for health verification

> aside positive
> The container includes all the environment configuration needed to connect to the deployed Llama model, making it truly portable across environments.

## Deploy to Cloud Run with GPU

Duration: 15:00

Now comes the exciting part - deploying your agent to Cloud Run where it will serve production traffic while calling the deployed Llama model.

### Configure Google Cloud

First, let's set up your Google Cloud environment:

```bash
# Set your project ID (replace with your actual project ID)
export PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID

# Set the region (choose one with GPU availability)
export REGION="us-central1"
gcloud config set run/region $REGION

# Enable required APIs
gcloud services enable run.googleapis.com \
                       cloudbuild.googleapis.com \
                       aiplatform.googleapis.com
```

### Deploy to Cloud Run

Now let's deploy your agent with GPU support. This single command will build your container and deploy it:

```bash
# Deploy with GPU support and Llama model configuration
gcloud run deploy production-adk-agent \
    --source . \
    --region $REGION \
    --allow-unauthenticated \
    --memory 4Gi \
    --cpu 2 \
    --gpu 1 \
    --gpu-type nvidia-l4 \
    --max-instances 5 \
    --min-instances 1 \
    --concurrency 10 \
    --timeout 300 \
    --set-env-vars GOOGLE_CLOUD_PROJECT=$PROJECT_ID \
    --set-env-vars GOOGLE_CLOUD_LOCATION=$REGION \
    --set-env-vars GEMMA_MODEL_NAME=gemma3:4b \
    --set-env-vars LLAMA_MODEL_NAME=llama3.2:3b \
    --set-env-vars OLLAMA_API_BASE=https://ollama-gemma-795845071313.europe-west1.run.app \
    --no-cpu-throttling
```

### Understanding the Deployment Configuration

**GPU Configuration**:

- **NVIDIA L4 GPU**: Provides AI model acceleration (though in this case, the actual model runs on the remote Llama service)
- **Memory/CPU**: Sufficient resources for AI agent processing and API calls

**Scaling Configuration**:

- **Auto-scaling**: Between 1-5 instances based on demand
- **Concurrency**: Handle up to 10 concurrent requests per instance
- **Min instances**: Keeps at least 1 instance warm to reduce cold starts

**Environment Variables**:

- **OLLAMA_API_BASE**: The crucial configuration that points your agent to the deployed Llama service
- **Model names**: Specify which models to use on the remote service

### Get Your Service URL

```bash
# Get the deployed service URL
export SERVICE_URL=$(gcloud run services describe production-adk-agent \
    --region=$REGION \
    --format='value(status.url)')

echo "🎉 Agent deployed at: $SERVICE_URL"
```

> aside positive
> Your agent is now deployed and ready to serve production traffic while making calls to the deployed Llama model!

## Test the Live Application

Duration: 10:00

Let's test your deployed agent to ensure it's working correctly with the deployed Llama integration.

### Test the Deployment Health

```bash
# Test health endpoint
curl $SERVICE_URL/health
```

You should see a response like:

```json
{
  "status": "healthy",
  "service": "production-adk-agent",
  "version": "1.0.0"
}
```

### Set Up Proxy for Interactive Testing

For secure testing of the deployed service:

```bash
# Start the proxy (run this in a separate terminal)
gcloud run services proxy production-adk-agent --port=8080
```

### Interactive Testing

With the proxy running, you can now test your deployed agent:

- **Web interface**: `http://localhost:8080`
- **API documentation**: `http://localhost:8080/docs`

### Test Both Agent Types

**Test the Gemma Agent** (Conversational):

Try these queries to test general conversation capabilities:

- "What's the difference between machine learning and deep learning?"
- "Can you help me brainstorm ideas for a blog post about cloud computing?"
- "Explain the benefits of containerization"

**Test the Llama Agent** (With Tools):

Test the tool-calling capabilities that use the deployed Llama model:

- "What's the weather like in London?"
- "How's the weather in San Francisco today?"
- "Can you check the weather in Tokyo?"

### Verify Llama Integration

The key test is ensuring that the Llama agent successfully:

1. **Receives your request** through the web interface
2. **Calls the deployed Llama model** via the OLLAMA_API_BASE URL
3. **Uses the weather tool** when appropriate
4. **Returns formatted responses** to the user

> aside positive
> If the weather queries work correctly, your agent is successfully integrating with the deployed Llama model on Cloud Run!

## Load Testing and Performance Validation

Duration: 10:00

Load testing ensures your agent can handle production traffic and that the deployed Llama integration performs well under load.

### Prepare Load Testing

```bash
# Create results directory
mkdir -p .results

# Install locust if not already available
pip install locust
```

### Run Comprehensive Load Tests

```bash
# Run load test against your deployed service
locust -f load_test.py \
    -H $SERVICE_URL \
    --headless \
    -t 60s \
    -u 20 \
    -r 2 \
    --csv=.results/results \
    --html=.results/report.html
```

### Load Test Configuration Explained

- **Duration**: 60 seconds of sustained testing
- **Users**: 20 concurrent users
- **Spawn Rate**: 2 users per second ramp-up
- **Scenarios**:
  - Gemma conversations
  - Llama tool usage (weather queries)
  - Health checks

### Monitor the Test

During the load test, watch for:

```console
[2024-01-15 10:30:00,000] INFO/locust.main: Starting Locust 2.x.x
[2024-01-15 10:30:00,100] INFO/locust.runners: Spawning 20 users at the rate 2 users/s (0 users already running)...
[2024-01-15 10:30:10,000] INFO/locust.runners: All users spawned: GemmaUser: 10, LlamaUser: 10
```

### Analyze Results

```bash
# View the detailed HTML report
open .results/report.html

# Check CSV results for key metrics
cat .results/results_stats.csv
```

### Key Metrics to Monitor

**Response Time Targets**:

- **Health checks**: < 1 second
- **Simple conversations**: < 5 seconds
- **Tool-based queries**: < 10 seconds (includes Llama model call time)

**Performance Indicators**:

- **Throughput**: Requests per second handled
- **Error Rate**: Should be minimal (< 1%)
- **95th Percentile Response Time**: Should meet your SLA requirements

> aside negative
> If you see high error rates or timeouts, the deployed Llama service might be under heavy load. The load test validates both your agent and the upstream Llama integration.

## Production Best Practices

Duration: 5:00

Now that your agent is deployed and tested, let's cover some production best practices for managing the Llama integration.

### Environment Management

For production deployments, use Google Secret Manager instead of plain environment variables:

```bash
# Create a secret with your configuration
gcloud secrets create production-config --data-file=.env

# Update your deployment to use secrets
gcloud run services update production-adk-agent \
    --set-env-vars GOOGLE_CLOUD_PROJECT=$PROJECT_ID \
    --set-secrets /app/.env=production-config:latest
```

### Monitoring and Observability

Set up comprehensive monitoring for your deployed agent:

**Cloud Logging**:

- Automatic logging of all agent interactions
- Monitor calls to the deployed Llama service
- Track tool usage patterns

**Cloud Monitoring**:

- Set up alerts for error rates and latency
- Monitor the health of the Llama integration
- Track resource utilization

**Cloud Trace**:

- Monitor request performance and bottlenecks
- Identify slow calls to the deployed Llama model
- Optimize the integration performance

### Scaling Configuration

Adjust scaling parameters based on your traffic patterns:

```bash
# Update scaling for production load
gcloud run services update production-adk-agent \
    --min-instances 2 \
    --max-instances 10 \
    --concurrency 5
```

### Error Handling and Resilience

Ensure your agent handles Llama service failures gracefully:

- **Retry logic**: Implement retries for transient failures
- **Fallback responses**: Provide helpful messages when the Llama service is unavailable
- **Circuit breaker**: Prevent cascading failures

> aside positive
> Production-ready agents need robust error handling, especially when integrating with external services like the deployed Llama model.

## Advanced Monitoring and Troubleshooting

Duration: 5:00

Let's set up monitoring and learn how to troubleshoot common issues with the Llama integration.

### Cloud Console Monitoring

1. Navigate to **Cloud Run** in the Google Cloud Console
2. Select your `production-adk-agent` service
3. Monitor these key metrics:
   - **CPU and Memory**: Resource utilization
   - **Request Count**: Traffic patterns
   - **Request Latency**: Response time including Llama calls
   - **Error Rate**: Failed requests

### Setting Up Alerts

Create alerts for critical issues:

```bash
# Example: Alert on high error rate
gcloud alpha monitoring policies create \
    --notification-channels=$NOTIFICATION_CHANNEL \
    --display-name="ADK Agent Error Rate" \
    --condition-threshold-value=0.05 \
    --condition-threshold-duration=300s
```

### Common Issues and Solutions

**Llama Integration Issues**:

- **Connection timeouts**: Check `OLLAMA_API_BASE` configuration
- **Authentication errors**: Verify service account permissions
- **Rate limiting**: Implement request throttling

**Performance Issues**:

- **Cold starts**: Increase `min-instances` to keep services warm
- **Memory errors**: Increase memory allocation
- **Slow responses**: Monitor Llama service performance

### Debug Commands

```bash
# Check service status
gcloud run services describe production-adk-agent --region=$REGION

# View recent logs
gcloud logs read "resource.type=cloud_run_revision" --limit=50

# Test Llama connectivity locally
curl -X POST $OLLAMA_API_BASE/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model": "llama3.2:3b", "prompt": "Hello"}'
```

> aside negative
> Always test the Llama integration connectivity separately when troubleshooting agent issues. Network problems can manifest as agent failures.

## Key Takeaways and Next Steps

Duration: 3:00

Congratulations! You've successfully deployed your ADK agent to production with deployed Llama integration.

### What You've Accomplished

✅ **Modified your agent** to call deployed Llama models instead of local ones
✅ **Containerized** your agent for production deployment  
✅ **Deployed to Cloud Run** with GPU support and proper scaling
✅ **Configured environment variables** for the Llama integration
✅ **Load tested** the complete system including Llama calls
✅ **Set up monitoring** for production operations

### Key Technical Learnings

1. **Deployed Model Integration**: How to configure ADK agents to call remote model services
2. **Production Architecture**: Containerization and Cloud Run deployment patterns
3. **Environment Management**: Secure configuration for production services
4. **Performance Testing**: Validating integrations under load
5. **Observability**: Monitoring distributed AI applications

### Architecture Benefits

Your deployed solution provides:

- **Scalability**: Auto-scales based on demand
- **Reliability**: Health checks and error handling
- **Performance**: GPU acceleration and optimized containers
- **Maintainability**: Separation of agent logic and model serving
- **Cost Efficiency**: Pay-per-use scaling

### Next Steps

**Immediate Actions**:

- Set up production monitoring and alerting
- Configure automated deployment pipelines
- Implement additional error handling and retries

**Advanced Enhancements**:

- Add more sophisticated tools and integrations
- Implement A/B testing for different model versions
- Add caching layers for frequently requested data
- Explore multi-region deployments

**Business Applications**:

- Customize the agent for your specific use case
- Add domain-specific tools and knowledge
- Integrate with your existing business systems

> aside positive
> You now have a production-ready AI agent that can scale to handle real business workloads while leveraging powerful deployed language models!

## Congratulations!

Duration: 1:00

🎉 **You've successfully completed Lab 3!**

Your ADK agent is now:

- ✅ **Production-deployed** on Cloud Run with GPU support
- ✅ **Integrated** with deployed Llama models for scalable AI
- ✅ **Load-tested** and validated for production traffic
- ✅ **Monitored** with comprehensive observability
- ✅ **Ready** to handle real business intelligence workloads

### What's Next?

This completes the "Accelerate with AI" series, but your journey with production AI agents is just beginning:

- **Explore advanced ADK features** and custom tool development
- **Implement CI/CD pipelines** for automated deployments
- **Add sophisticated business logic** and domain expertise
- **Scale to multi-region deployments** for global availability

### Questions or Issues?

- Check the **troubleshooting section** for common solutions
- Review **Cloud Run documentation** for deployment guidance
- Explore **ADK documentation** for advanced agent features

---

**Total Lab Duration**: ~60 minutes

**Lab Focus**: Deploying ADK agents with deployed Llama model integration on Cloud Run
