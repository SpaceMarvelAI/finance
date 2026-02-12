#!/bin/bash
# CURL Commands for Financial Automation API
# Server: http://localhost:8000

API="http://localhost:8000"

echo "======================================"
echo "1. Health Check"
echo "======================================"
curl -s -X GET "$API/health" | jq '.'
echo ""

echo "======================================"
echo "2. User Registration"
echo "======================================"
REGISTER=$(curl -s -X POST "$API/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@test.com",
    "password": "SecurePass123",
    "full_name": "Test User",
    "company_id": "comp_001"
  }')
echo "$REGISTER" | jq '.'
JWT=$(echo "$REGISTER" | jq -r '.token')
USER_ID=$(echo "$REGISTER" | jq -r '.user_id')
echo "JWT Token: $JWT"
echo "User ID: $USER_ID"
echo ""

echo "======================================"
echo "3. Validate Token"
echo "======================================"
curl -s -X POST "$API/api/v1/auth/validate" \
  -H "Authorization: Bearer $JWT" | jq '.'
echo ""

echo "======================================"
echo "4. Company Setup (Colors, DSO, SLA, Currency)"
echo "======================================"
COMPANY=$(curl -s -X POST "$API/api/v1/company/setup" \
  -H "Authorization: Bearer $JWT" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Acme Corporation",
    "currency": "INR",
    "primary_color": "#1976D2",
    "secondary_color": "#424242",
    "accent_color": "#FF6B6B",
    "dso_target": 45,
    "sla_days": 30,
    "tax_id": "GST123456789",
    "address": "123 Business Ave, Mumbai",
    "phone": "+91-9876543210"
  }')
echo "$COMPANY" | jq '.'
COMPANY_ID=$(echo "$COMPANY" | jq -r '.company_id')
echo "Company ID: $COMPANY_ID"
echo ""

echo "======================================"
echo "5. Get Company Profile"
echo "======================================"
curl -s -X GET "$API/api/v1/company/$COMPANY_ID" \
  -H "Authorization: Bearer $JWT" | jq '.'
echo ""

echo "======================================"
echo "6. Query AP Aging Report (LLM Routing + Workflow)"
echo "======================================"
QUERY=$(curl -s -X POST "$API/api/v1/chat/query" \
  -H "Authorization: Bearer $JWT" \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"Show me AP aging report for unpaid invoices\",
    \"user_id\": \"$USER_ID\",
    \"company_id\": \"$COMPANY_ID\",
    \"agent_type\": \"ap_aging\"
  }")
echo "$QUERY" | jq '.'
SESSION_ID=$(echo "$QUERY" | jq -r '.session_id')
WORKFLOW_ID=$(echo "$QUERY" | jq -r '.workflow_id')
echo "Session ID: $SESSION_ID"
echo "Workflow ID: $WORKFLOW_ID"
echo ""

echo "======================================"
echo "7. Get Workflow Nodes (Interactive Visualization)"
echo "======================================"
curl -s -X GET "$API/api/v1/workflow/$SESSION_ID/$WORKFLOW_ID" \
  -H "Authorization: Bearer $JWT" | jq '.'
echo ""

echo "======================================"
echo "8. Update Workflow Node Parameter"
echo "======================================"
curl -s -X PUT "$API/api/v1/workflow/$SESSION_ID/$WORKFLOW_ID/node/fetch_invoices" \
  -H "Authorization: Bearer $JWT" \
  -H "Content-Type: application/json" \
  -d '{
    "date_range": "last_60_days",
    "vendor_filter": "AWS"
  }' | jq '.'
echo ""

echo "======================================"
echo "9. Execute Workflow"
echo "======================================"
curl -s -X POST "$API/api/v1/workflow/$SESSION_ID/$WORKFLOW_ID/execute" \
  -H "Authorization: Bearer $JWT" \
  -H "Content-Type: application/json" \
  -d '{
    "execute": true,
    "generate_report": true
  }' | jq '.'
echo ""

echo "======================================"
echo "10. Query AR Aging Report"
echo "======================================"
curl -s -X POST "$API/api/v1/chat/query" \
  -H "Authorization: Bearer $JWT" \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"Generate AR aging summary\",
    \"user_id\": \"$USER_ID\",
    \"company_id\": \"$COMPANY_ID\",
    \"agent_type\": \"ar_aging\"
  }" | jq '.'
echo ""

echo "======================================"
echo "11. Get System Status"
echo "======================================"
curl -s -X GET "$API/status" \
  -H "Authorization: Bearer $JWT" | jq '.'
echo ""

echo "======================================"
echo "12. Get System Capabilities"
echo "======================================"
curl -s -X GET "$API/capabilities" \
  -H "Authorization: Bearer $JWT" | jq '.'
echo ""

echo "======================================"
echo "13. User Logout"
echo "======================================"
curl -s -X POST "$API/api/v1/auth/logout" \
  -H "Authorization: Bearer $JWT" | jq '.'
echo ""

echo "✅ Pipeline Test Complete!"
echo ""
echo "Next: Check logs at /Users/apple/Downloads/FA/logs/app.log"
echo "Reports at: /Users/apple/Downloads/FA/output/reports/"
