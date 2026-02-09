#!/bin/bash

# ============================================================================
# Script de Auto-Push para GitHub
# ============================================================================
# Este script monitora alterações no repositório e faz push automático
# para o GitHub, trigerando deploy automático no Render.
#
# Uso: ./auto-push.sh
# ============================================================================

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configurações
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$REPO_DIR/.auto-push.log"
WATCH_INTERVAL=5 # segundos
MAX_RETRIES=3
RETRY_DELAY=10 # segundos

# ============================================================================
# Funções
# ============================================================================

log() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} [${level}] ${message}" | tee -a "$LOG_FILE"
}

log_info() {
    log "${BLUE}INFO${NC}" "$@"
}

log_success() {
    log "${GREEN}SUCCESS${NC}" "$@"
}

log_warning() {
    log "${YELLOW}WARNING${NC}" "$@"
}

log_error() {
    log "${RED}ERROR${NC}" "$@"
}

check_git_config() {
    log_info "Verificando configuração do Git..."
    
    if ! git config user.name > /dev/null 2>&1; then
        log_error "Git user.name não configurado"
        return 1
    fi
    
    if ! git config user.email > /dev/null 2>&1; then
        log_error "Git user.email não configurado"
        return 1
    fi
    
    log_success "Git configurado corretamente"
    return 0
}

check_remote() {
    log_info "Verificando conexão com repositório remoto..."
    
    if ! git remote -v | grep -q origin; then
        log_error "Repositório remoto 'origin' não encontrado"
        return 1
    fi
    
    if ! git ls-remote origin > /dev/null 2>&1; then
        log_error "Não conseguiu conectar ao repositório remoto"
        return 1
    fi
    
    log_success "Repositório remoto acessível"
    return 0
}

has_changes() {
    # Verifica se há alterações não commitadas
    if [ -n "$(git status --porcelain)" ]; then
        return 0
    fi
    return 1
}

has_unpushed_commits() {
    # Verifica se há commits não enviados
    local unpushed=$(git rev-list @{u}..HEAD 2>/dev/null | wc -l)
    if [ "$unpushed" -gt 0 ]; then
        return 0
    fi
    return 1
}

get_current_branch() {
    git rev-parse --abbrev-ref HEAD
}

commit_and_push() {
    local branch=$(get_current_branch)
    local commit_message=$1
    local retry_count=0
    
    log_info "Fazendo commit na branch '$branch'..."
    
    # Stage todas as alterações
    git add -A
    
    # Commit com mensagem
    if git commit -m "$commit_message" 2>/dev/null; then
        log_success "Commit realizado: $commit_message"
    else
        log_warning "Nenhuma alteração para fazer commit"
        return 1
    fi
    
    # Tentar push com retry
    while [ $retry_count -lt $MAX_RETRIES ]; do
        log_info "Fazendo push para origin/$branch (tentativa $((retry_count + 1))/$MAX_RETRIES)..."
        
        if git push origin "$branch" 2>/dev/null; then
            log_success "Push realizado com sucesso!"
            log_success "Deploy automático trigerrado no Render"
            return 0
        else
            retry_count=$((retry_count + 1))
            if [ $retry_count -lt $MAX_RETRIES ]; then
                log_warning "Push falhou. Aguardando $RETRY_DELAY segundos antes de tentar novamente..."
                sleep $RETRY_DELAY
            fi
        fi
    done
    
    log_error "Falha ao fazer push após $MAX_RETRIES tentativas"
    return 1
}

watch_changes() {
    log_info "Monitorando alterações no repositório..."
    log_info "Pressione Ctrl+C para parar"
    log_info "Intervalo de verificação: ${WATCH_INTERVAL}s"
    echo ""
    
    local last_check=$(date +%s)
    
    while true; do
        sleep $WATCH_INTERVAL
        
        # Atualizar informações do repositório
        git fetch origin > /dev/null 2>&1 || true
        
        # Verificar alterações locais
        if has_changes; then
            local current_time=$(date '+%Y-%m-%d %H:%M:%S')
            log_warning "Alterações detectadas em $current_time"
            
            # Gerar mensagem de commit com timestamp
            local commit_msg="Auto-push: $(date '+%Y-%m-%d %H:%M:%S')"
            
            if commit_and_push "$commit_msg"; then
                echo ""
            else
                log_error "Falha ao fazer push das alterações"
                echo ""
            fi
        fi
        
        # Verificar commits não enviados
        if has_unpushed_commits; then
            log_warning "Commits não enviados detectados"
            
            local commit_msg="Auto-push: $(date '+%Y-%m-%d %H:%M:%S')"
            
            if commit_and_push "$commit_msg"; then
                echo ""
            else
                log_error "Falha ao fazer push dos commits"
                echo ""
            fi
        fi
    done
}

show_status() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}         Status do Repositório Git                        ${BLUE}║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    
    echo -e "\n${BLUE}Repositório:${NC}"
    echo "  Diretório: $REPO_DIR"
    echo "  Branch: $(get_current_branch)"
    
    echo -e "\n${BLUE}Remoto:${NC}"
    git remote -v | sed 's/^/  /'
    
    echo -e "\n${BLUE}Status:${NC}"
    git status --short | sed 's/^/  /' || echo "  Sem alterações"
    
    echo -e "\n${BLUE}Commits não enviados:${NC}"
    git log origin/$(get_current_branch)..HEAD --oneline | sed 's/^/  /' || echo "  Nenhum"
    
    echo ""
}

# ============================================================================
# Main
# ============================================================================

main() {
    clear
    
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}     Script de Auto-Push para GitHub - Academia Santiago  ${BLUE}║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    # Verificar se estamos em um repositório Git
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        log_error "Não está em um repositório Git válido"
        exit 1
    fi
    
    log_info "Inicializando script de auto-push..."
    
    # Verificações iniciais
    if ! check_git_config; then
        exit 1
    fi
    
    if ! check_remote; then
        exit 1
    fi
    
    # Mostrar status
    show_status
    
    # Iniciar monitoramento
    watch_changes
}

# Tratador para Ctrl+C
trap 'echo ""; log_info "Script interrompido pelo usuário"; exit 0' INT TERM

# Executar main
main "$@"
