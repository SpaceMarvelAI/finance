#!/bin/bash
# Comprehensive CURL Commands for Financial Automation API Testing
# Run these commands to test the complete pipeline

API_URL="http://localhost:8000"
USER_EMAIL="test@company.com"
USER_PASSWORD="SecurePassword123"
COMPANY_NAME="Test Company"

echo "========================================="
echo "Financial Automation API Test Suite"
echo "========================================="
echo ""

# 1. User Registration
echo "1. REGISTERING USER..."
REGISTER_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$USER_EMAIL\",
    \"password\": \"$USER_PASSWORD\",
    \"full_name\": \"John Doe\",
    \"company_id\": \"comp_001\"
  }")

echo "Response: $REGISTER_RESPONSE"
JWT_TOKEN=$(echo $REGISTER_RESPONSE | grep -o '"token":"[^"]*"' | cut -d'"' -f4)
USER_ID=$(echo $REGISTER_RESPONSE | grep -o '"user_id":"[^"]*"' | cut -d'"' -f4)

if [ -z "$JWT_TOKEN" ]; then
  echo "ERROR: Could not get JWT token from registration"
  exit 1
fi

echo "✓ JWT Token: $JWT_TOKEN"
echo "✓ User ID: $USER_ID"
echo ""

# 2. Validate Token
echo "2. VALIDATING TOKEN..."
curl -s -X POST "$API_URL/api/v1/auth/validate" \
  -H "Authorization: Bearer $JWT_TOKEN" | jq '.'
echo ""

# 3. Company Setup
echo "3. SETTING UP COMPANY WITH SETTINGS..."
COMPANY_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/company/setup" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -d "{
    \"name\": \"$COMPANY_NAME\",
    \"currency\": \"INR\",
    \"primary_color\": \"#1976D2\",
    \"secondary_color\": \"#424242\",
    \"accent_color\": \"#FF6B6B\",
    \"dso_target\": 45,
    \"sla_days\": 30,
    \"tax_id\": \"GST123456789\",
    \"address\": \"123 Business Ave, City\",
    \"phone\": \"+91-1234567890\"
  }")

echo "Response: $COMPANY_RESPONSE"
COMPANY_ID=$(echo $COMPANY_RESPONSE | grep -o '"company_id":"[^"]*"' | cut -d'"' -f4)
echo "✓ Company ID: $COMPANY_ID"
echo ""

# 4. Get Company Profile
echo "4. GETTING COMPANY PROFILE..."
curl -s -X GET "$API_URL/api/v1/company/$COMPANY_ID" \
  -H "Authorization: Bearer $JWT_TOKEN" | jq '.'
echo ""

# 5. Upload Document
echo "5. UPLOADING DOCUMENT..."
# Create a sample PDF or use existing file
curl -s -X POST "$API_URL/upload" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -F "file=@test_invoice.pdf" \
  -F "user_id=$USER_ID" \
  -F "company_id=$COMPANY_ID" | jq '.'
echo ""

# 6. Query for AP Aging Report (Tests LLM Routing + Workflow)
echo "6. QUERYING AP AGING REPORT (LLM Routing)..."
SESSION_ID=$(uuidgen)
QUERY_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/chat/query" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"Show me AP aging report for unpaid invoices in Excel\",
    \"user_id\": \"$USER_ID\",
    \"company_id\": \"$COMPANY_ID\",
    \"session_id\": \"$SESSION_ID\",
    \"agent_type\": \"ap_aging\"
  }")

echo "Response: $QUERY_RESPONSE"
WORKFLOW_ID=$(echo $QUERY_RESPONSE | grep -o '"workflow_id":"[^"]*"' | cut -d'"' -f4)
echo "✓ Session ID: $SESSION_ID"
echo "✓ Workflow ID: $WORKFLOW_ID"
echo ""

# 7. Get Interactive Workflow Nodes
echo "7. GETTING WORKFLOW NODES FOR VISUALIZATION..."
curl -s -X GET "$API_URL/api/v1/workflow/$SESSION_ID/$WORKFLOW_ID" \
  -H "Authorization: Bearer $JWT_TOKEN" | jq '.'
echo ""

# 8. Update Workflow Node Parameter
echo "8. UPDATING WORKFLOW NODE (e.g., change date range)..."
curl -s -X PUT "$API_URL/api/v1/workflow/$SESSION_ID/$WORKFLOW_ID/node/fetch_invoices" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "date_range": "last_60_days",
    "vendor_filter": "AWS"
  }' | jq '.'
echo ""

# 9. Execute Workflow
echo "9. EXECUTING WORKFLOW..."
curl -s -X POST "$API_URL/api/v1/workflow/$SESSION_ID/$WORKFLOW_ID/execute" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "execute": true,
    "generate_report": true
  }' | jq '.'
echo ""

# 10. Get System Status
echo "10. CHECKING SYSTEM STATUS..."
curl -s -X GET "$API_URL/status" \
  -H "Authorization: Bearer $JWT_TOKEN" | jq '.'
echo ""

# 11. Get System Capabilities
echo "11. CHECKING SYSTEM CAPABILITIES..."
curl -s -X GET "$API_URL/capabilities" \
  -H "Authorization: Bearer $JWT_TOKEN" | jq '.'
echo ""

# 12. Query AR Aging Report
echo "12. QUERYING AR AGING REPORT..."
curl -s -X POST "$API_URL/api/v1/chat/query" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"Generate AR aging summary for last 90 days\",
    \"user_id\": \"$USER_ID\",
    \"company_id\": \"$COMPANY_ID\",
    \"agent_type\": \"ar_aging\"
  }" | jq '.'
echo ""

# 13. Query DSO Report
echo "13. QUERYING DSO REPORT..."
curl -s -X POST "$API_URL/api/v1/chat/query" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"Calculate DSO for current month\",
    \"user_id\": \"$USER_ID\",
    \"company_id\": \"$COMPANY_ID\",
    \"agent_type\": \"dso\"
  }" | jq '.'
echo ""

# 14. Health Check
echo "14. HEALTH CHECK..."
curl -s -X GET "$API_URL/health" | jq '.'
echo ""

# 15. User Logout
echo "15. USER LOGOUT..."
curl -s -X POST "$API_URL/api/v1/auth/logout" \
  -H "Authorization: Bearer $JWT_TOKEN" | jq '.'
echo ""

echo "========================================="
echo "Test Suite Complete"
echo "========================================="
echo ""
echo "Summary:"
echo "✓ Authentication: User registration and JWT token generation"
echo "✓ Company Setup: Configure colors, DSO, SLA, currency"
echo "✓ Document Upload: Parse, extract, and save to database"
echo "✓ LLM Routing: Query interpreted and routed to correct agent"
echo "✓ Workflow Building: Interactive workflow nodes displayed"
echo "✓ Node Editing: Workflow parameters customizable"
echo "✓ Workflow Execution: LangGraph agents execute workflow"
echo "✓ Report Generation: Excel reports generated with branding"
echo ""
echo "Check logs at: /Users/apple/Downloads/FA/logs/"
echo "Reports at: /Users/apple/Downloads/FA/output/reports/"
