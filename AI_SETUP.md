# AI Configuration Guide for Rental Management System

This guide explains how to enable and configure AI features in your Django rental management system.

## 🚀 Quick Start

1. **Copy environment template:**
   ```bash
   cp env.example .env
   ```

2. **Configure your API keys:**
   - Get an OpenAI API key from [OpenAI Platform](https://platform.openai.com/)
   - Update the `.env` file with your actual API key

3. **Enable AI features:**
   - Set `AI_ENABLED=True` in your `.env` file
   - Configure which specific AI features you want to use

4. **Test the configuration:**
   ```bash
   python manage.py test_ai_config
   ```

## 🔧 Environment Variables

### Core AI Configuration
```bash
# Enable/disable AI functionality
AI_ENABLED=True

# OpenAI Configuration
OPENAI_API_KEY=your-actual-api-key-here
OPENAI_MODEL=gpt-4
AI_MAX_TOKENS=2000
AI_TEMPERATURE=0.7
AI_REQUEST_TIMEOUT=30
```

### AI Features
```bash
# Enable specific AI features
AI_PROPERTY_ANALYSIS=True
AI_MAINTENANCE_PREDICTION=True
AI_TENANT_SCREENING=True
AI_RENT_OPTIMIZATION=True
AI_CHATBOT_ENABLED=True
```

### Service Configuration
```bash
# AI service provider
AI_SERVICE_PROVIDER=openai
AI_FALLBACK_PROVIDER=anthropic
```

## 🤖 Available AI Features

### 1. Property Analysis
- **Purpose:** Analyze property data and provide insights
- **Use Case:** Market analysis, property valuation, investment recommendations
- **API:** `ai_service.analyze_property(property_data)`

### 2. Maintenance Prediction
- **Purpose:** Predict when maintenance will be needed
- **Use Case:** Preventive maintenance scheduling, cost estimation
- **API:** `ai_service.predict_maintenance(property_history)`

### 3. Tenant Screening
- **Purpose:** Analyze tenant applications using AI
- **Use Case:** Risk assessment, approval recommendations
- **API:** `ai_service.screen_tenant(tenant_data)`

### 4. Rent Optimization
- **Purpose:** Optimize rent pricing based on market data
- **Use Case:** Competitive pricing, revenue maximization
- **API:** `ai_service.optimize_rent(property_data, market_data)`

### 5. AI Chatbot
- **Purpose:** Provide intelligent customer support
- **Use Case:** Tenant inquiries, property information, support
- **API:** `ai_service.chatbot_response(user_message, context)`

## 📱 Usage Examples

### In Django Views
```python
from rental_management.ai_utils import get_ai_service

def property_analysis_view(request, property_id):
    ai_service = get_ai_service()
    
    if ai_service.is_available():
        property_data = get_property_data(property_id)
        analysis = ai_service.analyze_property(property_data)
        return JsonResponse(analysis)
    else:
        return JsonResponse({"error": "AI service not available"})
```

### In Django Admin
```python
from rental_management.ai_utils import get_ai_service

class PropertyAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Add AI analysis to admin
        return qs
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        
        # Trigger AI analysis on save
        ai_service = get_ai_service()
        if ai_service.is_available():
            analysis = ai_service.analyze_property(obj.__dict__)
            # Store analysis results
```

### In Templates
```html
{% if ai_enabled %}
<div class="ai-insights">
    <h3>AI Insights</h3>
    <div id="ai-analysis">
        <!-- AI analysis content -->
    </div>
</div>
{% endif %}
```

## 🔒 Security Considerations

1. **API Key Protection:**
   - Never commit API keys to version control
   - Use environment variables for sensitive data
   - Rotate API keys regularly

2. **Rate Limiting:**
   - Implement rate limiting for AI API calls
   - Monitor API usage and costs
   - Set appropriate timeouts

3. **Data Privacy:**
   - Ensure tenant data is handled securely
   - Comply with data protection regulations
   - Log AI interactions for audit purposes

## 📊 Monitoring and Logging

### Check AI Status
```bash
python manage.py test_ai_config --verbose
```

### View AI Logs
```python
import logging
logger = logging.getLogger('rental_management.ai_utils')
```

### Monitor API Usage
- Track OpenAI API usage in your OpenAI dashboard
- Set up alerts for high usage
- Monitor response times and success rates

## 🛠️ Troubleshooting

### Common Issues

1. **AI service not available:**
   - Check if `AI_ENABLED=True` in `.env`
   - Verify `OPENAI_API_KEY` is set correctly
   - Ensure API key has sufficient credits

2. **API rate limits:**
   - Implement exponential backoff
   - Use request queuing
   - Consider upgrading OpenAI plan

3. **High response times:**
   - Adjust `AI_REQUEST_TIMEOUT`
   - Use async processing for non-critical features
   - Implement caching for repeated requests

### Debug Mode
```python
# Enable debug logging
AI_LOG_LEVEL=DEBUG
```

## 🚀 Advanced Configuration

### Multiple AI Providers
```python
# Configure fallback providers
AI_SERVICE_PROVIDER=openai
AI_FALLBACK_PROVIDER=anthropic

# Custom provider configuration
CUSTOM_AI_PROVIDER_URL=https://your-ai-service.com/api
CUSTOM_AI_PROVIDER_KEY=your-custom-key
```

### Custom AI Models
```python
# Use different models for different tasks
AI_PROPERTY_ANALYSIS_MODEL=gpt-4
AI_MAINTENANCE_MODEL=gpt-3.5-turbo
AI_CHATBOT_MODEL=gpt-4-turbo
```

## 📚 Additional Resources

- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Django Environment Variables](https://django-environ.readthedocs.io/)
- [AI Best Practices](https://platform.openai.com/docs/guides/best-practices)

## 🤝 Support

If you encounter issues with AI configuration:

1. Check the logs for error messages
2. Verify environment variable configuration
3. Test with the management command
4. Review OpenAI API status and quotas

---

**Note:** This AI configuration is designed to enhance your rental management system with intelligent features. Ensure you comply with all applicable laws and regulations when implementing AI-powered tenant screening and data analysis.
