#!/bin/bash


VENV_PATH="venv/bin/activate"
BACKEND_CMD="uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
CELERY_CMD="celery -A app.core.celery_app worker --loglevel=info"
FRONTEND_DIR="frontend"
FRONTEND_CMD="npm start"

# PID FILES
BACKEND_PID="backend.pid"
CELERY_PID="celery.pid"
FRONTEND_PID="frontend.pid"
REDIS_PID="redis.pid"


# FUNCTIONS
start_postgres() {
    echo "Checking PostgreSQL..."
    if pgrep -x "postgres" >/dev/null; then
        echo "PostgreSQL already running."
    else
        echo "Starting PostgreSQL..."
        sudo systemctl start postgresql
    fi
}

start_redis() {
    echo "Checking Redis..."
    if pgrep -x "redis-server" >/dev/null; then
        echo "Redis already running."
    else
        echo "Starting Redis..."
        redis-server --daemonize yes
        echo $! > $REDIS_PID
    fi
}

start_backend() {
    echo "Starting Backend..."
    bash -c "source $VENV_PATH && $BACKEND_CMD" &
    echo $! > $BACKEND_PID
}

start_celery() {
    echo "Starting Celery Worker..."
    bash -c "source $VENV_PATH && $CELERY_CMD" &
    echo $! > $CELERY_PID
}

start_frontend() {
    echo "Starting Frontend..."
    (cd $FRONTEND_DIR && nohup npm start >/dev/null 2>&1 & echo $! > ../$FRONTEND_PID)
}

stop_process() {
    PID_FILE=$1
    NAME=$2
    FALLBACK=$3

    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill "$PID" 2>/dev/null; then
            echo "$NAME stopped (PID $PID)."
        else
            echo "$NAME PID $PID not running."
        fi
        rm -f "$PID_FILE"
    fi

    # fallback: pkill by process name
    if [ -n "$FALLBACK" ]; then
        pkill -f "$FALLBACK" 2>/dev/null || true
    fi
}

stop_all() {
    echo "Stopping services..."

    stop_process $BACKEND_PID "Backend" "uvicorn app.main"
    stop_process $CELERY_PID "Celery Worker" "app.core.celery_app"
    stop_process $FRONTEND_PID "Frontend" "node"

    echo "Stopping Redis if started by script..."
    if [ -f "$REDIS_PID" ]; then
        kill $(cat "$REDIS_PID") 2>/dev/null
        rm -f "$REDIS_PID"
        echo "Redis stopped."
    fi

    echo "All services stopped."
}

start_all() {
    echo "Starting all services..."
    start_postgres
    start_redis
    start_backend
    start_celery
    start_frontend
    echo "All services started!"
}

# COMMAND HANDLER
case "$1" in
    start)
        start_all
        ;;
    stop)
        stop_all
        ;;
    restart)
        stop_all
        start_all
        ;;
    *)
        echo "Usage: $0 {start|stop|restart}"
        ;;
esac
