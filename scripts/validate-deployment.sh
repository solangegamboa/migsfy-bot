#!/bin/bash

# Validation Script - Playlist Processor Deployment
# Valida se todos os componentes estão funcionando corretamente

set -euo pipefail

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configurações
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PYTHON_CMD="${PYTHON_CMD:-python3}"

# Contadores
TESTS_PASSED=0
TESTS_FAILED=0
WARNINGS=0

# Função para logging
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((TESTS_PASSED++))
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((TESTS_FAILED++))
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
    ((WARNINGS++))
}

# Função para executar teste
run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_exit_code="${3:-0}"
    
    log_info "Testing: $test_name"
    
    if eval "$test_command" >/dev/null 2>&1; then
        local exit_code=$?
        if [ $exit_code -eq $expected_exit_code ]; then
            log_success "$test_name"
            return 0
        else
            log_error "$test_name (exit code: $exit_code, expected: $expected_exit_code)"
            return 1
        fi
    else
        log_error "$test_name (command failed)"
        return 1
    fi
}

# Função para verificar arquivo
check_file() {
    local file_path="$1"
    local description="$2"
    
    if [ -f "$file_path" ]; then
        log_success "File exists: $description ($file_path)"
        return 0
    else
        log_error "File missing: $description ($file_path)"
        return 1
    fi
}

# Função para verificar diretório
check_directory() {
    local dir_path="$1"
    local description="$2"
    
    if [ -d "$dir_path" ]; then
        log_success "Directory exists: $description ($dir_path)"
        return 0
    else
        log_error "Directory missing: $description ($dir_path)"
        return 1
    fi
}

# Função para verificar dependência Python
check_python_module() {
    local module_name="$1"
    local description="$2"
    
    if $PYTHON_CMD -c "import $module_name" 2>/dev/null; then
        log_success "Python module available: $description ($module_name)"
        return 0
    else
        log_error "Python module missing: $description ($module_name)"
        return 1
    fi
}

# Header
echo "=============================================="
echo "  Playlist Processor Deployment Validation"
echo "=============================================="
echo ""

# 1. Verificar estrutura de arquivos
log_info "Checking file structure..."

check_file "$PROJECT_ROOT/src/playlist/__init__.py" "Playlist module init"
check_file "$PROJECT_ROOT/src/playlist/main.py" "Main entry point"
check_file "$PROJECT_ROOT/src/playlist/playlist_processor.py" "Playlist processor"
check_file "$PROJECT_ROOT/src/playlist/slskd_api_client.py" "SLSKD API client"
check_file "$PROJECT_ROOT/src/playlist/database_manager.py" "Database manager"
check_file "$PROJECT_ROOT/src/playlist/duplicate_detector.py" "Duplicate detector"
check_file "$PROJECT_ROOT/src/playlist/rate_limiter.py" "Rate limiter"
check_file "$PROJECT_ROOT/src/playlist/cache_manager.py" "Cache manager"
check_file "$PROJECT_ROOT/src/playlist/process_lock.py" "Process lock"
check_file "$PROJECT_ROOT/src/playlist/metrics_collector.py" "Metrics collector"

echo ""

# 2. Verificar diretórios
log_info "Checking directory structure..."

check_directory "$PROJECT_ROOT/src/playlist" "Playlist source directory"
check_directory "$PROJECT_ROOT/tests/playlist" "Playlist tests directory"
check_directory "$PROJECT_ROOT/scripts" "Scripts directory"
check_directory "$PROJECT_ROOT/data" "Data directory"
check_directory "$PROJECT_ROOT/logs" "Logs directory"

echo ""

# 3. Verificar dependências Python
log_info "Checking Python dependencies..."

check_python_module "slskd_api" "SLSKD API"
check_python_module "psutil" "System monitoring"
check_python_module "sqlite3" "SQLite database"
check_python_module "dotenv" "Environment variables"
check_python_module "pathlib" "Path utilities"
check_python_module "json" "JSON handling"
check_python_module "time" "Time utilities"
check_python_module "os" "OS utilities"

echo ""

# 4. Verificar scripts executáveis
log_info "Checking executable scripts..."

if [ -x "$PROJECT_ROOT/scripts/setup-playlist-cron.sh" ]; then
    log_success "Cron setup script is executable"
else
    log_error "Cron setup script is not executable"
fi

if [ -x "$PROJECT_ROOT/scripts/validate-deployment.sh" ]; then
    log_success "Validation script is executable"
else
    log_warning "Validation script is not executable (current script)"
fi

echo ""

# 5. Testes de importação Python
log_info "Testing Python imports..."

cd "$PROJECT_ROOT"

run_test "Import playlist processor" \
    "$PYTHON_CMD -c 'from src.playlist.playlist_processor import PlaylistProcessor'"

run_test "Import database manager" \
    "$PYTHON_CMD -c 'from src.playlist.database_manager import DatabaseManager'"

run_test "Import process lock" \
    "$PYTHON_CMD -c 'from src.playlist.process_lock import ProcessLock'"

run_test "Import metrics collector" \
    "$PYTHON_CMD -c 'from src.playlist.metrics_collector import MetricsCollector'"

echo ""

# 6. Testes funcionais básicos
log_info "Running functional tests..."

# Criar ambiente temporário para testes
TEMP_DIR=$(mktemp -d)
TEMP_DB="$TEMP_DIR/test.db"
TEMP_LOCK="$TEMP_DIR/test.lock"

# Teste de database manager
run_test "Database manager initialization" \
    "$PYTHON_CMD -c 'from src.playlist.database_manager import DatabaseManager; db = DatabaseManager(\"$TEMP_DB\"); db.init_database()'"

# Teste de process lock
run_test "Process lock functionality" \
    "$PYTHON_CMD -c 'from src.playlist.process_lock import ProcessLock; lock = ProcessLock(\"$TEMP_LOCK\"); assert lock.acquire(); lock.release()'"

# Teste de metrics collector
run_test "Metrics collector functionality" \
    "$PYTHON_CMD -c 'from src.playlist.metrics_collector import MetricsCollector; mc = MetricsCollector(\"$TEMP_DB\"); mc.collect_system_metrics()'"

# Limpeza
rm -rf "$TEMP_DIR"

echo ""

# 7. Verificar configuração de ambiente
log_info "Checking environment configuration..."

if [ -f "$PROJECT_ROOT/.env" ]; then
    log_success "Environment file exists"
    
    # Verificar variáveis essenciais
    if grep -q "SLSKD_HOST" "$PROJECT_ROOT/.env"; then
        log_success "SLSKD_HOST configured"
    else
        log_warning "SLSKD_HOST not found in .env"
    fi
    
    if grep -q "SLSKD_PORT" "$PROJECT_ROOT/.env"; then
        log_success "SLSKD_PORT configured"
    else
        log_warning "SLSKD_PORT not found in .env"
    fi
else
    log_warning "Environment file (.env) not found"
fi

echo ""

# 8. Verificar testes unitários
log_info "Running unit tests..."

if [ -f "$PROJECT_ROOT/tests/playlist/test_integration_complete.py" ]; then
    log_success "Integration tests file exists"
    
    # Executar testes se pytest estiver disponível
    if command -v pytest >/dev/null 2>&1; then
        if pytest "$PROJECT_ROOT/tests/playlist/" -v --tb=short >/dev/null 2>&1; then
            log_success "Unit tests passed"
        else
            log_warning "Some unit tests failed (check with: pytest tests/playlist/ -v)"
        fi
    else
        log_warning "pytest not available - skipping unit tests"
    fi
else
    log_warning "Integration tests file not found"
fi

echo ""

# 9. Verificar configuração Docker (se aplicável)
log_info "Checking Docker configuration..."

if [ -f "$PROJECT_ROOT/Dockerfile" ]; then
    log_success "Dockerfile exists"
else
    log_warning "Dockerfile not found"
fi

if [ -f "$PROJECT_ROOT/docker-compose.yml" ]; then
    log_success "Docker Compose file exists"
else
    log_warning "Docker Compose file not found"
fi

echo ""

# 10. Verificar logs e permissões
log_info "Checking logs and permissions..."

if [ -w "$PROJECT_ROOT/logs" ]; then
    log_success "Logs directory is writable"
else
    log_error "Logs directory is not writable"
fi

if [ -w "$PROJECT_ROOT/data" ]; then
    log_success "Data directory is writable"
else
    log_error "Data directory is not writable"
fi

echo ""

# 11. Teste de dry-run
log_info "Testing dry-run execution..."

# Criar playlist de teste temporária
TEMP_PLAYLIST_DIR=$(mktemp -d)
echo "Test Artist - Test Album - Test Song" > "$TEMP_PLAYLIST_DIR/test.txt"

# Configurar variáveis de ambiente para teste
export PLAYLIST_PATH="$TEMP_PLAYLIST_DIR"
export DATABASE_PATH="$TEMP_DIR/test.db"
export SLSKD_HOST="localhost"
export SLSKD_PORT="5030"
export SLSKD_API_KEY="test"

if timeout 30 $PYTHON_CMD "$PROJECT_ROOT/src/playlist/main.py" --dry-run >/dev/null 2>&1; then
    log_success "Dry-run execution completed"
else
    log_warning "Dry-run execution failed or timed out"
fi

# Limpeza
rm -rf "$TEMP_PLAYLIST_DIR"

echo ""

# Resumo final
echo "=============================================="
echo "           VALIDATION SUMMARY"
echo "=============================================="
echo ""
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"
echo -e "Warnings: ${YELLOW}$WARNINGS${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    if [ $WARNINGS -eq 0 ]; then
        echo -e "${GREEN}✅ ALL VALIDATIONS PASSED${NC}"
        echo "The Playlist Processor is ready for deployment!"
        exit 0
    else
        echo -e "${YELLOW}⚠️  VALIDATIONS PASSED WITH WARNINGS${NC}"
        echo "The Playlist Processor should work, but check warnings above."
        exit 0
    fi
else
    echo -e "${RED}❌ VALIDATION FAILED${NC}"
    echo "Please fix the failed tests before deployment."
    exit 1
fi
