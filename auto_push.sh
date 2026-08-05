#!/bin/bash
# Auto-push script for energy-storage-tracker
# This script will keep trying to push until it succeeds or times out

REPO_DIR="/workspace/competitor-monitor"
MAX_ATTEMPTS=30
ATTEMPT=0

cd "$REPO_DIR"

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    ATTEMPT=$((ATTEMPT + 1))
    
    # Try to get token
    source /root/.codebuddy/skills/github-connector/scripts/get_token.sh github 2>/dev/null
    
    if [ -n "$GITHUB_TOKEN" ]; then
        echo "[$ATTEMPT/$MAX_ATTEMPTS] Token acquired, pushing..."
        git push "https://oauth2:${GITHUB_TOKEN}@github.com/HealerLYMYYY/energy-storage-tracker.git" main 2>&1
        
        if [ $? -eq 0 ]; then
            echo "✅ Push successful!"
            exit 0
        fi
    else
        echo "[$ATTEMPT/$MAX_ATTEMPTS] Waiting for GitHub OAuth authorization..."
    fi
    
    sleep 10
done

echo "❌ Timed out after $MAX_ATTEMPTS attempts"
exit 1
