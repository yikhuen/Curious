#!/bin/bash
# Start vLLM server with OOM detection and health checks

set -e  # Exit on error

MODEL="${1:-Qwen/Qwen2.5-32B-Instruct}"
PORT="${2:-8000}"
DTYPE="${3:-bfloat16}"
LOG_FILE="${4:-/tmp/vllm_server.log}"

echo "Starting vLLM server..."
echo "Model: $MODEL"
echo "Port: $PORT"
echo "Dtype: $DTYPE"
echo "Log file: $LOG_FILE"
echo ""

# Start vLLM in background and capture PID
vllm serve "$MODEL" --port "$PORT" --dtype "$DTYPE" > "$LOG_FILE" 2>&1 &
VLLM_PID=$!

echo "vLLM started with PID: $VLLM_PID"
echo "Waiting for server to initialize (this may take 1-2 minutes)..."
echo ""

# Function to check for OOM errors in log
check_oom() {
    if grep -qi "out of memory\|CUDA out of memory\|OOM\|not enough GPU memory" "$LOG_FILE"; then
        echo ""
        echo "❌ ERROR: GPU Out of Memory detected!"
        echo ""
        echo "Last 20 lines of log:"
        tail -20 "$LOG_FILE"
        echo ""
        echo "Possible solutions:"
        echo "  1. Use a smaller model (e.g., Qwen/Qwen2.5-14B-Instruct)"
        echo "  2. Use a quantized model (e.g., Qwen/Qwen2.5-32B-Instruct-AWQ)"
        echo "  3. Use a GPU with more VRAM (e.g., H100 80GB)"
        echo "  4. Lower --gpu-memory-utilization (default 0.9)"
        echo ""
        kill $VLLM_PID 2>/dev/null || true
        exit 1
    fi
}

# Function to check if server is responding
check_server() {
    curl -s "http://localhost:$PORT/v1/models" > /dev/null 2>&1
}

# Monitor startup for up to 5 minutes
MAX_WAIT=300
ELAPSED=0
CHECK_INTERVAL=5

while [ $ELAPSED -lt $MAX_WAIT ]; do
    # Check if process is still running
    if ! kill -0 $VLLM_PID 2>/dev/null; then
        echo ""
        echo "❌ ERROR: vLLM process died unexpectedly!"
        echo ""
        echo "Last 30 lines of log:"
        tail -30 "$LOG_FILE"
        echo ""
        check_oom  # This will exit if OOM detected
        echo "Check the log file for details: $LOG_FILE"
        exit 1
    fi
    
    # Check for OOM errors
    check_oom
    
    # Check if server is responding
    if check_server; then
        echo ""
        echo "✅ vLLM server is ready!"
        echo "   API endpoint: http://localhost:$PORT/v1"
        echo "   Log file: $LOG_FILE"
        echo "   PID: $VLLM_PID"
        echo ""
        echo "Server is running. Press Ctrl+C to stop."
        echo ""
        
        # Wait for the process to finish (or be killed)
        wait $VLLM_PID
        exit $?
    fi
    
    sleep $CHECK_INTERVAL
    ELAPSED=$((ELAPSED + CHECK_INTERVAL))
    echo -n "."
done

echo ""
echo "❌ ERROR: Server did not start within $MAX_WAIT seconds"
echo ""
echo "Last 30 lines of log:"
tail -30 "$LOG_FILE"
echo ""
check_oom  # This will exit if OOM detected
echo "Check the log file for details: $LOG_FILE"
kill $VLLM_PID 2>/dev/null || true
exit 1
