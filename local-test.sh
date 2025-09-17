#!/bin/bash

echo "🚀 Starting AWS SAM Local testing..."

# Stop any existing SAM local processes
echo "📋 Stopping existing SAM processes..."
pkill -f "sam local" || true

# Build and start SAM Local API
echo "🔧 Building and starting SAM Local API Gateway..."
sam build
sam local start-api --port 3000 --env-vars env.json &

# Wait for SAM to start
echo "⏳ Waiting for SAM to start..."
sleep 10

# Test the endpoints
echo ""
echo "🧪 Testing endpoints..."
echo ""

echo "1️⃣  Testing user existence (existing user):"
curl -s http://localhost:3000/users/user_123 | jq .

echo ""
echo "2️⃣  Testing user existence (non-existent user):"
curl -s http://localhost:3000/users/nonexistent_user | jq .

echo ""
echo "3️⃣  Testing create new user:"
curl -s -X POST http://localhost:3000/users \
  -H "Content-Type: application/json" \
  -d '{"user_id": "sam_test_user"}' | jq .

echo ""
echo "4️⃣  Testing get permissions:"
curl -s http://localhost:3000/permissions/user_123 | jq .

echo ""
echo "5️⃣  Testing add permission to existing user:"
curl -s -X POST http://localhost:3000/permissions/user_123/agents \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "sam-test-agent"}' | jq .

echo ""
echo "6️⃣  Testing add permission to newly created user:"
curl -s -X POST http://localhost:3000/permissions/sam_test_user/agents \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "code-reviewer"}' | jq .

echo ""
echo "✅ SAM Local testing complete!"
echo "🌐 SAM Local API running at: http://localhost:3000"
echo "📖 To stop: pkill -f 'sam local'"