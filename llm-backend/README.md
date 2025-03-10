# Health check

curl http://localhost:5152/health

# Run analysis

curl -X POST http://localhost:5152/api/analyze \
 -H "Content-Type: application/json" \
 -d '{"query": "your query here"}'
