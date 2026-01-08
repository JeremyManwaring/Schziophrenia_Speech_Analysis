# How to Download Changes as CSV

## Quick Start

### Option 1: Using the Script
```bash
# If the endpoint is at localhost:8080 (default)
./download_changes_csv.sh

# Or specify a custom URL
./download_changes_csv.sh "https://api.example.com"
```

### Option 2: Manual curl Command
```bash
# Basic download
curl -o changes.csv "http://localhost:8080/analytics/ai-code/changes.csv"

# With authentication (if required)
curl -H "Authorization: Bearer YOUR_TOKEN" \
     -o changes.csv \
     "http://localhost:8080/analytics/ai-code/changes.csv"

# With verbose output (to see what's happening)
curl -v -o changes.csv "http://localhost:8080/analytics/ai-code/changes.csv"
```

### Option 3: Using Python
```python
import requests
import csv

# Simple download
url = "http://localhost:8080/analytics/ai-code/changes.csv"
response = requests.get(url)
with open('changes.csv', 'wb') as f:
    f.write(response.content)

# With authentication
headers = {'Authorization': 'Bearer YOUR_TOKEN'}
response = requests.get(url, headers=headers)
with open('changes.csv', 'wb') as f:
    f.write(response.content)
```

## If You Need Authentication

### Getting Authentication Token

1. **Check Cursor Settings**:
   - Open Cursor
   - Go to Settings → Account or API
   - Look for API token or access token

2. **Browser DevTools Method**:
   - Open Cursor
   - Open DevTools (Cmd+Option+I on Mac)
   - Go to Network tab
   - Make a request that triggers the analytics
   - Look at the request headers for authentication

### Using Token in curl
```bash
TOKEN="your-token-here"
curl -H "Authorization: Bearer ${TOKEN}" \
     -o changes.csv \
     "http://localhost:8080/analytics/ai-code/changes.csv"
```

## Alternative: Export from Cursor UI

If there's a UI option:
1. Open Cursor
2. Look for Settings → Analytics or Export
3. Look for "Export as CSV" or "Download data"
4. Check if there's an analytics dashboard

## Troubleshooting

### 403 Forbidden
- Authentication required
- Check if you need a token

### 404 Not Found
- Endpoint might be different
- Check Cursor's API documentation
- The path might be: `/api/analytics/changes.csv` or similar

### Connection Refused
- Service might not be running
- Check if Cursor has a local server
- Port might be different (check Cursor settings)

### Empty File
- Endpoint might return empty data
- Check with `curl -v` to see response headers
- Might need query parameters like `?format=csv`

## Check What's Available

```bash
# Try to see what endpoints are available
curl -v "http://localhost:8080/analytics/" 2>&1 | grep -i "location\|href"

# Check response headers
curl -I "http://localhost:8080/analytics/ai-code/changes.csv"
```

