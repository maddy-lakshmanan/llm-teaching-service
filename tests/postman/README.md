# Postman Collection for LLM Teaching Service

This directory contains Postman collections and environments for testing the LLM Teaching Service API.

## Files

- **LLM-Teaching-Service.postman_collection.json**: Main API collection with all endpoints
- **Local.postman_environment.json**: Environment variables for local testing
- **Production.postman_environment.json**: Environment variables for production testing

## Collection Structure

### 1. Health Checks
- Health Check - Basic health endpoint
- Readiness Check - Service readiness with dependencies
- Liveness Check - Simple liveness probe

### 2. Teaching Endpoints
**Happy Scenarios:**
- Ask Question - Elementary Math (simple question)
- Ask Question - High School Science (complex question with context)
- Ask Question - With Conversation History (context-aware)
- Get History - Retrieve conversation history
- Get Usage - Get student usage metrics

**Negative Scenarios:**
- Missing Required Fields (422 validation error)
- Invalid Subject (422 validation error)
- Invalid Grade Level (422 validation error)
- Empty Question (422 validation error)
- Invalid Student ID (empty results)

### 3. Admin Endpoints
**Happy Scenarios:**
- List Models - Get available LLM models
- Get Cache Stats - Cache performance metrics
- Invalidate Cache - Clear cache by pattern
- Get Usage Summary - Aggregated usage metrics

**Negative Scenarios:**
- Invalidate Cache without pattern (422 error)

## Environment Variables

### Local Environment
```json
{
  "base_url": "http://localhost:8080",
  "student_id": "test-student-123",
  "api_version": "v1"
}
```

### Production Environment
```json
{
  "base_url": "https://llm-teaching-service-YOUR_PROJECT_ID.a.run.app",
  "student_id": "prod-student-456",
  "api_version": "v1",
  "auth_token": "your-auth-token-here"
}
```

## Usage

### Import into Postman

1. **Import Collection:**
   - Open Postman
   - Click "Import" button
   - Select `LLM-Teaching-Service.postman_collection.json`
   - Collection will appear in your workspace

2. **Import Environments:**
   - Click "Import" button
   - Select `Local.postman_environment.json` and `Production.postman_environment.json`
   - Environments will appear in the environment dropdown

3. **Select Environment:**
   - Use the environment dropdown (top-right) to select "Local Environment" or "Production Environment"

### Running Tests

#### Run Entire Collection
1. Click on the collection name
2. Click "Run" button
3. Select environment
4. Click "Run LLM Teaching Service"

#### Run Individual Folders
1. Expand the collection
2. Right-click on a folder (e.g., "Health Checks")
3. Select "Run folder"

#### Run Individual Requests
1. Navigate to a specific request
2. Click "Send" button
3. View response and test results

### Command Line (Newman)

Install Newman:
```bash
npm install -g newman
```

Run collection:
```bash
# Run with local environment
newman run tests/postman/LLM-Teaching-Service.postman_collection.json \
  -e tests/postman/Local.postman_environment.json

# Run with production environment
newman run tests/postman/LLM-Teaching-Service.postman_collection.json \
  -e tests/postman/Production.postman_environment.json

# Generate HTML report
newman run tests/postman/LLM-Teaching-Service.postman_collection.json \
  -e tests/postman/Local.postman_environment.json \
  --reporters cli,html \
  --reporter-html-export newman-report.html
```

## Test Scenarios

### Happy Path Testing
- ✅ All endpoints return 200 status
- ✅ Response bodies contain expected fields
- ✅ Data types are correct
- ✅ Business logic validation

### Negative Testing
- ❌ Missing required fields → 422 Unprocessable Entity
- ❌ Invalid enum values → 422 Validation Error
- ❌ Empty strings → 422 Validation Error
- ❌ Non-existent resources → 200 with empty results or 404

### Performance Testing
- Response time assertions (< 2000ms for most endpoints)
- Token usage tracking
- Cost monitoring

## Automated Tests

Each request includes test scripts that validate:
- HTTP status codes
- Response structure
- Required fields presence
- Data type validation
- Business logic rules

## Environment-Specific Configuration

### Local Development
- Uses `localhost:8080`
- No authentication required
- Test student ID: `test-student-123`

### Production
- Uses Cloud Run URL
- May require authentication token
- Production student ID: `prod-student-456`
- Update `base_url` with your actual Cloud Run URL

## Customization

### Adding New Tests
1. Add new request to appropriate folder
2. Add test scripts in "Tests" tab:
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Response has expected field", function () {
    const jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('field_name');
});
```

### Adding Environment Variables
1. Edit environment JSON files
2. Add new variables to `values` array
3. Use in requests with `{{variable_name}}`

### Example: Add Authentication
```json
{
  "key": "auth_token",
  "value": "Bearer your-token-here",
  "type": "secret",
  "enabled": true
}
```

Then in request headers:
```json
{
  "key": "Authorization",
  "value": "{{auth_token}}"
}
```

## CI/CD Integration

### GitHub Actions Example
```yaml
- name: Run Postman Tests
  run: |
    npm install -g newman
    newman run tests/postman/LLM-Teaching-Service.postman_collection.json \
      -e tests/postman/Local.postman_environment.json \
      --reporters cli,junit \
      --reporter-junit-export results.xml
```

## Troubleshooting

### Connection Refused
- Ensure service is running: `docker-compose up`
- Check URL in environment variables
- Verify port is correct (8080)

### 422 Validation Errors
- Check request body matches schema
- Verify enum values (subject, grade_level)
- Ensure all required fields are present

### 500 Internal Server Error
- Check service logs: `docker-compose logs app`
- Verify Ollama is running
- Check Redis connection

## Support

For issues or questions:
1. Check service logs
2. Verify environment configuration
3. Review API documentation
4. Test with curl for debugging:
```bash
curl -X POST http://localhost:8080/api/v1/teach \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "test-123",
    "question": "What is 2+2?",
    "subject": "math",
    "grade_level": "elementary"
  }'
```
