#!/bin/bash
# AITM Docker Development Scripts

set -e

show_help() {
    echo "🐳 AITM Docker Development Helper"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  start      Start all services in development mode"
    echo "  stop       Stop all services"
    echo "  restart    Restart all services"
    echo "  build      Build all containers"
    echo "  rebuild    Clean build all containers"
    echo "  logs       Show logs for all services"
    echo "  backend    Show logs for backend only"
    echo "  frontend   Show logs for frontend only"
    echo "  status     Show container status"
    echo "  shell      Open shell in backend container"
    echo "  clean      Clean up containers, volumes, and images"
    echo "  test       Run tests in backend"
    echo "  help       Show this help message"
    echo ""
}

start_services() {
    echo "🚀 Starting AITM development environment with Docker..."
    
    # Check if .env file exists
    if [ ! -f .env ]; then
        echo "📝 Creating .env file from template..."
        if [ -f .env.example ]; then
            cp .env.example .env
            echo "⚠️  Please edit .env file with your API keys before running the application"
        else
            echo "❌ No .env.example file found. Please create a .env file manually."
            exit 1
        fi
    fi
    
    docker-compose up --build -d
    echo ""
    echo "✅ Services started successfully!"
    echo ""
    echo "🌟 Access your application:"
    echo "  🔗 Frontend: http://localhost:41241"
    echo "  🔗 Backend API: http://localhost:38527"
    echo "  📚 API Docs: http://localhost:38527/docs"
    echo ""
    echo "📋 To view logs: ./docker-dev.sh logs"
    echo "🛑 To stop services: ./docker-dev.sh stop"
}

stop_services() {
    echo "🛑 Stopping AITM services..."
    docker-compose down
    echo "✅ Services stopped"
}

restart_services() {
    echo "🔄 Restarting AITM services..."
    docker-compose restart
    echo "✅ Services restarted"
}

build_containers() {
    echo "🔨 Building AITM containers..."
    docker-compose build
    echo "✅ Build complete"
}

rebuild_containers() {
    echo "🔨 Rebuilding AITM containers from scratch..."
    docker-compose down
    docker-compose build --no-cache
    echo "✅ Rebuild complete"
}

show_logs() {
    docker-compose logs -f
}

show_backend_logs() {
    docker-compose logs -f backend
}

show_frontend_logs() {
    docker-compose logs -f frontend
}

show_status() {
    echo "📊 Container Status:"
    docker-compose ps
    echo ""
    echo "🔍 Health Status:"
    docker-compose ps --format "table {{.Service}}\t{{.Status}}\t{{.Ports}}"
}

open_shell() {
    echo "🐚 Opening shell in backend container..."
    docker-compose exec backend /bin/bash
}

clean_up() {
    echo "🧹 Cleaning up Docker resources..."
    read -p "⚠️  This will remove containers, volumes, and unused images. Continue? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose down -v
        docker system prune -f
        echo "✅ Cleanup complete"
    else
        echo "❌ Cleanup cancelled"
    fi
}

run_tests() {
    echo "🧪 Running backend tests..."
    docker-compose exec backend python -m pytest tests/ -v
}

# Main command handling
case "${1:-help}" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    build)
        build_containers
        ;;
    rebuild)
        rebuild_containers
        ;;
    logs)
        show_logs
        ;;
    backend)
        show_backend_logs
        ;;
    frontend)
        show_frontend_logs
        ;;
    status)
        show_status
        ;;
    shell)
        open_shell
        ;;
    clean)
        clean_up
        ;;
    test)
        run_tests
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "❌ Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
