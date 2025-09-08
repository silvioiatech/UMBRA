#!/bin/bash

# Creator v1 (CRT4) - Automated Installation Script
# Comprehensive setup script for Creator v1 Content Creation System

set -euo pipefail  # Exit on error, undefined vars, and pipe failures

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="creator-v1"
INSTALL_DIR="${INSTALL_DIR:-/opt/creator-v1}"
DATA_DIR="${DATA_DIR:-/var/lib/creator-v1}"
LOG_DIR="${LOG_DIR:-/var/log/creator-v1}"
CONFIG_DIR="${CONFIG_DIR:-/etc/creator-v1}"
PYTHON_VERSION="3.11"
INSTALL_TYPE="${INSTALL_TYPE:-docker}"  # docker, python, or development

# Functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

banner() {
    echo -e "${CYAN}"
    cat << 'EOF'
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║                    Creator v1 (CRT4)                         ║
    ║              Advanced Content Creation System                 ║
    ║                                                               ║
    ║                     Installation Script                      ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
}

check_requirements() {
    log "Checking system requirements..."
    
    # Check OS
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
        DISTRO=$(lsb_release -si 2>/dev/null || echo "unknown")
        log "Detected OS: Linux ($DISTRO)"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        log "Detected OS: macOS"
    else
        error "Unsupported operating system: $OSTYPE"
    fi
    
    # Check if running as root (for system-wide installation)
    if [[ $EUID -eq 0 ]]; then
        warn "Running as root. This will install system-wide."
        SUDO=""
    else
        info "Running as non-root user. Will use sudo for system operations."
        SUDO="sudo"
    fi
    
    # Check required commands
    local required_commands=()
    
    if [[ "$INSTALL_TYPE" == "docker" ]]; then
        required_commands+=("docker" "docker-compose")
    else
        required_commands+=("python3" "pip3" "git")
    fi
    
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            error "Required command not found: $cmd"
        else
            log "✓ Found: $cmd"
        fi
    done
    
    # Check Python version if needed
    if [[ "$INSTALL_TYPE" != "docker" ]]; then
        local python_version=$(python3 --version | cut -d' ' -f2)
        local python_major=$(echo "$python_version" | cut -d'.' -f1)
        local python_minor=$(echo "$python_version" | cut -d'.' -f2)
        
        if [[ $python_major -lt 3 ]] || [[ $python_major -eq 3 && $python_minor -lt 8 ]]; then
            error "Python 3.8+ required, found: $python_version"
        fi
        
        log "✓ Python version: $python_version"
    fi
    
    # Check available disk space (need at least 5GB)
    local available_space=$(df / | awk 'NR==2 {print $4}')
    local required_space=5242880  # 5GB in KB
    
    if [[ $available_space -lt $required_space ]]; then
        error "Insufficient disk space. Need at least 5GB, available: $(($available_space/1024/1024))GB"
    fi
    
    log "✓ System requirements met"
}

install_dependencies() {
    log "Installing system dependencies..."
    
    case "$OS" in
        "linux")
            if command -v apt-get &> /dev/null; then
                $SUDO apt-get update
                $SUDO apt-get install -y \
                    curl \
                    wget \
                    git \
                    build-essential \
                    python3-dev \
                    python3-pip \
                    python3-venv \
                    postgresql-client \
                    redis-tools \
                    htop \
                    nginx \
                    supervisor \
                    logrotate
            elif command -v yum &> /dev/null; then
                $SUDO yum update -y
                $SUDO yum install -y \
                    curl \
                    wget \
                    git \
                    gcc \
                    python3-devel \
                    python3-pip \
                    postgresql \
                    redis \
                    htop \
                    nginx \
                    supervisor
            else
                warn "Unknown package manager. Please install dependencies manually."
            fi
            ;;
        "macos")
            if command -v brew &> /dev/null; then
                brew update
                brew install \
                    python@3.11 \
                    postgresql \
                    redis \
                    nginx \
                    git
            else
                warn "Homebrew not found. Please install dependencies manually."
            fi
            ;;
    esac
    
    log "✓ System dependencies installed"
}

setup_directories() {
    log "Setting up directories..."
    
    # Create directories
    $SUDO mkdir -p "$INSTALL_DIR"
    $SUDO mkdir -p "$DATA_DIR"/{analytics,cache,backups,exports}
    $SUDO mkdir -p "$LOG_DIR"
    $SUDO mkdir -p "$CONFIG_DIR"
    
    # Set permissions
    if [[ $EUID -eq 0 ]]; then
        # Create creator user if running as root
        if ! id "creator" &>/dev/null; then
            useradd -r -d "$INSTALL_DIR" -s /bin/bash creator
        fi
        chown -R creator:creator "$INSTALL_DIR" "$DATA_DIR" "$LOG_DIR"
        chmod -R 755 "$INSTALL_DIR"
        chmod -R 750 "$DATA_DIR" "$LOG_DIR"
        chmod -R 640 "$CONFIG_DIR"
    fi
    
    log "✓ Directories created"
}

install_docker() {
    log "Installing Creator v1 using Docker..."
    
    # Copy files
    cp "$SCRIPT_DIR/docker-compose.yml" "$INSTALL_DIR/"
    cp "$SCRIPT_DIR/Dockerfile" "$INSTALL_DIR/"
    cp -r "$SCRIPT_DIR/config" "$INSTALL_DIR/" 2>/dev/null || true
    
    # Create environment file
    cat > "$INSTALL_DIR/.env" << 'EOF'
# Creator v1 Environment Configuration

# Basic Settings
DEBUG=false
LOG_LEVEL=INFO
VERSION=latest

# Ports
CREATOR_APP_PORT=8080
CREATOR_API_PORT=8000
HTTP_PORT=80
HTTPS_PORT=443
POSTGRES_PORT=5432
REDIS_PORT=6379
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000

# Security (CHANGE THESE!)
DB_PASSWORD=change_me_postgres_password
REDIS_PASSWORD=change_me_redis_password
JWT_SECRET=change_me_jwt_secret_very_long_and_random
ENCRYPTION_PASSWORD=change_me_encryption_password
GRAFANA_PASSWORD=change_me_grafana_password

# AI Provider API Keys (ADD YOUR KEYS)
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
STABILITY_API_KEY=your_stability_api_key_here

# Development Tools (set to admin@your-domain.com)
PGADMIN_EMAIL=admin@creator.local
PGADMIN_PASSWORD=change_me_pgadmin_password
EOF

    # Generate secure passwords
    if command -v openssl &> /dev/null; then
        log "Generating secure passwords..."
        sed -i "s/change_me_postgres_password/$(openssl rand -hex 16)/g" "$INSTALL_DIR/.env"
        sed -i "s/change_me_redis_password/$(openssl rand -hex 16)/g" "$INSTALL_DIR/.env"
        sed -i "s/change_me_jwt_secret_very_long_and_random/$(openssl rand -hex 32)/g" "$INSTALL_DIR/.env"
        sed -i "s/change_me_encryption_password/$(openssl rand -hex 16)/g" "$INSTALL_DIR/.env"
        sed -i "s/change_me_grafana_password/$(openssl rand -hex 8)/g" "$INSTALL_DIR/.env"
        sed -i "s/change_me_pgadmin_password/$(openssl rand -hex 8)/g" "$INSTALL_DIR/.env"
        log "✓ Secure passwords generated"
    else
        warn "OpenSSL not found. Please update passwords in $INSTALL_DIR/.env manually"
    fi
    
    # Build and start services
    cd "$INSTALL_DIR"
    
    log "Building Docker images..."
    docker-compose build
    
    log "Starting services..."
    docker-compose up -d postgres redis
    
    # Wait for database to be ready
    log "Waiting for database to be ready..."
    sleep 30
    
    # Start main application
    docker-compose up -d
    
    log "✓ Docker installation completed"
}

install_python() {
    log "Installing Creator v1 using Python..."
    
    # Create virtual environment
    log "Creating Python virtual environment..."
    python3 -m venv "$INSTALL_DIR/venv"
    source "$INSTALL_DIR/venv/bin/activate"
    
    # Upgrade pip
    pip install --upgrade pip setuptools wheel
    
    # Copy source code
    cp -r "$SCRIPT_DIR"/* "$INSTALL_DIR/"
    cd "$INSTALL_DIR"
    
    # Install dependencies
    log "Installing Python dependencies..."
    pip install -r requirements.txt
    
    # Install the package
    pip install -e .
    
    # Create configuration
    python -c "
from umbra.modules.creator.utils import DevelopmentTools
config_path = '$CONFIG_DIR/creator_config.yaml'
DevelopmentTools.generate_test_data('$DATA_DIR/test', 10)
print('✅ Default configuration and test data created')
"
    
    log "✓ Python installation completed"
}

setup_services() {
    log "Setting up system services..."
    
    if [[ "$INSTALL_TYPE" == "python" ]]; then
        # Create systemd service for Python installation
        cat > "/tmp/creator-v1.service" << EOF
[Unit]
Description=Creator v1 Content Creation System
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=creator
Group=creator
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$INSTALL_DIR/venv/bin
ExecStart=$INSTALL_DIR/venv/bin/python -m umbra.modules.creator.dashboard --host 0.0.0.0 --port 8080
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
        $SUDO mv "/tmp/creator-v1.service" "/etc/systemd/system/"
        $SUDO systemctl daemon-reload
        $SUDO systemctl enable creator-v1
        
        log "✓ Systemd service created"
    fi
    
    # Setup logrotate
    cat > "/tmp/creator-v1-logrotate" << EOF
$LOG_DIR/*.log {
    daily
    missingok
    rotate 30
    compress
    notifempty
    create 0644 creator creator
    postrotate
        systemctl reload creator-v1 > /dev/null 2>&1 || true
    endscript
}
EOF
    $SUDO mv "/tmp/creator-v1-logrotate" "/etc/logrotate.d/creator-v1"
    
    log "✓ Log rotation configured"
}

configure_firewall() {
    log "Configuring firewall..."
    
    if command -v ufw &> /dev/null; then
        $SUDO ufw allow 80/tcp
        $SUDO ufw allow 443/tcp
        $SUDO ufw allow 8080/tcp
        log "✓ UFW firewall configured"
    elif command -v firewall-cmd &> /dev/null; then
        $SUDO firewall-cmd --permanent --add-port=80/tcp
        $SUDO firewall-cmd --permanent --add-port=443/tcp
        $SUDO firewall-cmd --permanent --add-port=8080/tcp
        $SUDO firewall-cmd --reload
        log "✓ Firewalld configured"
    else
        warn "No firewall tool found. Please configure firewall manually."
    fi
}

create_scripts() {
    log "Creating management scripts..."
    
    # Create start script
    cat > "$INSTALL_DIR/start.sh" << 'EOF'
#!/bin/bash
# Creator v1 Start Script

INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$INSTALL_DIR"

if [[ -f "docker-compose.yml" ]]; then
    echo "Starting Creator v1 with Docker..."
    docker-compose up -d
    echo "✓ Services started"
    echo "Dashboard: http://localhost:8080"
    echo "API: http://localhost:8000"
else
    echo "Starting Creator v1 with Python..."
    source venv/bin/activate
    python -m umbra.modules.creator.dashboard --host 0.0.0.0 --port 8080 &
    echo "✓ Creator v1 started"
    echo "Dashboard: http://localhost:8080"
fi
EOF

    # Create stop script
    cat > "$INSTALL_DIR/stop.sh" << 'EOF'
#!/bin/bash
# Creator v1 Stop Script

INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$INSTALL_DIR"

if [[ -f "docker-compose.yml" ]]; then
    echo "Stopping Creator v1 Docker services..."
    docker-compose down
    echo "✓ Services stopped"
else
    echo "Stopping Creator v1 Python process..."
    pkill -f "umbra.modules.creator.dashboard"
    echo "✓ Creator v1 stopped"
fi
EOF

    # Create status script
    cat > "$INSTALL_DIR/status.sh" << 'EOF'
#!/bin/bash
# Creator v1 Status Script

INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$INSTALL_DIR"

if [[ -f "docker-compose.yml" ]]; then
    echo "Creator v1 Docker Status:"
    docker-compose ps
else
    echo "Creator v1 Python Status:"
    if pgrep -f "umbra.modules.creator.dashboard" > /dev/null; then
        echo "✓ Creator v1 is running"
    else
        echo "✗ Creator v1 is not running"
    fi
fi

echo ""
echo "System Health Check:"
curl -s http://localhost:8080/api/health | python3 -m json.tool 2>/dev/null || echo "API not responding"
EOF

    # Create update script
    cat > "$INSTALL_DIR/update.sh" << 'EOF'
#!/bin/bash
# Creator v1 Update Script

INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$INSTALL_DIR"

echo "Updating Creator v1..."

if [[ -f "docker-compose.yml" ]]; then
    echo "Updating Docker images..."
    docker-compose pull
    docker-compose up -d
    echo "✓ Docker update completed"
else
    echo "Updating Python installation..."
    source venv/bin/activate
    pip install --upgrade -r requirements.txt
    echo "✓ Python update completed"
fi

echo "Update completed successfully!"
EOF

    # Create backup script
    cat > "$INSTALL_DIR/backup.sh" << 'EOF'
#!/bin/bash
# Creator v1 Backup Script

INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="/var/backups/creator-v1"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

echo "Creating Creator v1 backup..."

if [[ -f "docker-compose.yml" ]]; then
    # Docker backup
    docker-compose exec -T postgres pg_dump -U creator creator > "$BACKUP_DIR/database_$DATE.sql"
    docker run --rm -v creator-v1_creator-data:/data -v "$BACKUP_DIR":/backup alpine tar czf "/backup/data_$DATE.tar.gz" -C /data .
else
    # Python backup
    cp -r "$INSTALL_DIR/data" "$BACKUP_DIR/data_$DATE"
    tar czf "$BACKUP_DIR/data_$DATE.tar.gz" -C "$BACKUP_DIR" "data_$DATE"
    rm -rf "$BACKUP_DIR/data_$DATE"
fi

echo "✓ Backup created: $BACKUP_DIR"
echo "Files:"
ls -la "$BACKUP_DIR"/*$DATE*
EOF

    # Make scripts executable
    chmod +x "$INSTALL_DIR"/*.sh
    
    log "✓ Management scripts created"
}

post_install() {
    log "Running post-installation tasks..."
    
    # Create desktop shortcut if in user session
    if [[ -n "${DISPLAY:-}" ]] && [[ -d "$HOME/Desktop" ]]; then
        cat > "$HOME/Desktop/Creator-v1.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Creator v1 Dashboard
Comment=Advanced Content Creation System
Exec=xdg-open http://localhost:8080
Icon=applications-internet
Terminal=false
Categories=Development;
EOF
        chmod +x "$HOME/Desktop/Creator-v1.desktop"
        log "✓ Desktop shortcut created"
    fi
    
    # Setup completion
    if [[ "$INSTALL_TYPE" == "python" ]]; then
        echo "export PATH=\"$INSTALL_DIR/venv/bin:\$PATH\"" >> ~/.bashrc 2>/dev/null || true
    fi
    
    log "✓ Post-installation completed"
}

verify_installation() {
    log "Verifying installation..."
    
    local health_url="http://localhost:8080/api/health"
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -s "$health_url" > /dev/null 2>&1; then
            log "✓ Creator v1 is responding"
            break
        fi
        
        if [[ $attempt -eq $max_attempts ]]; then
            error "Installation verification failed. Creator v1 is not responding after $max_attempts attempts."
        fi
        
        info "Attempt $attempt/$max_attempts: Waiting for Creator v1 to start..."
        sleep 10
        ((attempt++))
    done
    
    # Test API endpoints
    local api_tests=(
        "/api/status"
        "/api/health"
        "/api/components"
    )
    
    for endpoint in "${api_tests[@]}"; do
        if curl -s "http://localhost:8080$endpoint" | grep -q "version\|status\|health"; then
            log "✓ API endpoint working: $endpoint"
        else
            warn "API endpoint not responding properly: $endpoint"
        fi
    done
    
    log "✓ Installation verification completed"
}

show_summary() {
    echo -e "${GREEN}"
    cat << 'EOF'
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║                 🎉 INSTALLATION COMPLETE! 🎉                 ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
    
    log "Creator v1 (CRT4) has been successfully installed!"
    echo ""
    info "📊 Dashboard URL: ${CYAN}http://localhost:8080${NC}"
    info "🔌 API URL: ${CYAN}http://localhost:8000${NC}"
    info "📁 Installation Directory: ${CYAN}$INSTALL_DIR${NC}"
    info "📄 Configuration Directory: ${CYAN}$CONFIG_DIR${NC}"
    info "💾 Data Directory: ${CYAN}$DATA_DIR${NC}"
    info "📝 Log Directory: ${CYAN}$LOG_DIR${NC}"
    echo ""
    
    if [[ "$INSTALL_TYPE" == "docker" ]]; then
        info "🐳 Docker Management:"
        echo "  • Start: cd $INSTALL_DIR && docker-compose up -d"
        echo "  • Stop: cd $INSTALL_DIR && docker-compose down"
        echo "  • Logs: cd $INSTALL_DIR && docker-compose logs -f"
        echo "  • Status: cd $INSTALL_DIR && docker-compose ps"
    else
        info "🐍 Python Management:"
        echo "  • Start: $INSTALL_DIR/start.sh"
        echo "  • Stop: $INSTALL_DIR/stop.sh"
        echo "  • Status: $INSTALL_DIR/status.sh"
        echo "  • Update: $INSTALL_DIR/update.sh"
    fi
    
    echo ""
    info "🔧 Management Scripts:"
    echo "  • $INSTALL_DIR/start.sh - Start Creator v1"
    echo "  • $INSTALL_DIR/stop.sh - Stop Creator v1"
    echo "  • $INSTALL_DIR/status.sh - Check status"
    echo "  • $INSTALL_DIR/update.sh - Update system"
    echo "  • $INSTALL_DIR/backup.sh - Create backup"
    
    echo ""
    warn "🔐 IMPORTANT SECURITY NOTES:"
    if [[ "$INSTALL_TYPE" == "docker" ]]; then
        warn "  • Update API keys in: $INSTALL_DIR/.env"
        warn "  • Change default passwords in: $INSTALL_DIR/.env"
    fi
    warn "  • Configure firewall for production use"
    warn "  • Set up SSL/TLS certificates for HTTPS"
    warn "  • Review and update security settings"
    
    echo ""
    info "📚 Next Steps:"
    echo "  1. Configure API keys for AI providers"
    echo "  2. Set up your brand voice and content templates"
    echo "  3. Configure external integrations (optional)"
    echo "  4. Set up monitoring and alerts"
    echo "  5. Create content and test the system"
    
    echo ""
    log "For more information, visit: https://docs.creator-v1.com"
    echo ""
}

# Main installation flow
main() {
    banner
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --install-type)
                INSTALL_TYPE="$2"
                shift 2
                ;;
            --install-dir)
                INSTALL_DIR="$2"
                shift 2
                ;;
            --help)
                echo "Creator v1 Installation Script"
                echo ""
                echo "Usage: $0 [options]"
                echo ""
                echo "Options:"
                echo "  --install-type TYPE    Installation type: docker, python, or development (default: docker)"
                echo "  --install-dir DIR      Installation directory (default: /opt/creator-v1)"
                echo "  --help                 Show this help message"
                echo ""
                echo "Environment Variables:"
                echo "  INSTALL_DIR           Installation directory"
                echo "  DATA_DIR              Data directory"
                echo "  LOG_DIR               Log directory"
                echo "  CONFIG_DIR            Configuration directory"
                echo ""
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                ;;
        esac
    done
    
    # Validate install type
    if [[ ! "$INSTALL_TYPE" =~ ^(docker|python|development)$ ]]; then
        error "Invalid install type: $INSTALL_TYPE. Must be: docker, python, or development"
    fi
    
    log "Starting Creator v1 installation..."
    log "Installation type: $INSTALL_TYPE"
    log "Installation directory: $INSTALL_DIR"
    
    # Installation steps
    check_requirements
    install_dependencies
    setup_directories
    
    case "$INSTALL_TYPE" in
        "docker")
            install_docker
            ;;
        "python"|"development")
            install_python
            setup_services
            ;;
    esac
    
    configure_firewall
    create_scripts
    post_install
    verify_installation
    show_summary
    
    log "Installation completed successfully! 🎉"
}

# Error handling
trap 'error "Installation failed at line $LINENO"' ERR

# Run main function
main "$@"
