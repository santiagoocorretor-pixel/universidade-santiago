#!/usr/bin/env python3

"""
Script de Auto-Push para GitHub com Watchdog
Monitora alterações no repositório e faz push automático para o GitHub
"""

import os
import sys
import subprocess
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent
except ImportError:
    print("❌ Erro: watchdog não está instalado")
    print("   Instale com: pip3 install watchdog")
    sys.exit(1)

# ============================================================================
# Configuração de Logging
# ============================================================================

class ColoredFormatter(logging.Formatter):
    """Formatter com cores para terminal"""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[34m',       # Blue
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'SUCCESS': '\033[32m',    # Green
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        if record.levelname == 'INFO':
            color = self.COLORS['INFO']
        elif record.levelname == 'WARNING':
            color = self.COLORS['WARNING']
        elif record.levelname == 'ERROR':
            color = self.COLORS['ERROR']
        else:
            color = self.COLORS['DEBUG']
        
        record.msg = f"{color}{record.msg}{self.COLORS['RESET']}"
        return super().format(record)

# Configurar logging
log_dir = Path.cwd() / '.logs'
log_dir.mkdir(exist_ok=True)
log_file = log_dir / 'auto-push.log'

logger = logging.getLogger('AutoPush')
logger.setLevel(logging.DEBUG)

# Handler para arquivo
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(file_formatter)

# Handler para console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = ColoredFormatter(
    '%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
console_handler.setFormatter(console_formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

# ============================================================================
# Classe GitManager
# ============================================================================

class GitManager:
    """Gerenciador de operações Git"""
    
    def __init__(self, repo_path: str = '.'):
        self.repo_path = Path(repo_path)
        self.max_retries = 3
        self.retry_delay = 10
    
    def run_git_command(self, *args) -> Tuple[int, str, str]:
        """Executa comando git e retorna (returncode, stdout, stderr)"""
        try:
            result = subprocess.run(
                ['git', *args],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode, result.stdout.strip(), result.stderr.strip()
        except subprocess.TimeoutExpired:
            return 1, '', 'Comando expirou'
        except Exception as e:
            return 1, '', str(e)
    
    def check_config(self) -> bool:
        """Verifica se Git está configurado corretamente"""
        logger.info("Verificando configuração do Git...")
        
        # Verificar user.name
        code, _, _ = self.run_git_command('config', 'user.name')
        if code != 0:
            logger.error("Git user.name não configurado")
            return False
        
        # Verificar user.email
        code, _, _ = self.run_git_command('config', 'user.email')
        if code != 0:
            logger.error("Git user.email não configurado")
            return False
        
        logger.info("✓ Git configurado corretamente")
        return True
    
    def check_remote(self) -> bool:
        """Verifica conexão com repositório remoto"""
        logger.info("Verificando conexão com repositório remoto...")
        
        code, _, _ = self.run_git_command('ls-remote', 'origin')
        if code != 0:
            logger.error("Não conseguiu conectar ao repositório remoto")
            return False
        
        logger.info("✓ Repositório remoto acessível")
        return True
    
    def has_changes(self) -> bool:
        """Verifica se há alterações não commitadas"""
        code, output, _ = self.run_git_command('status', '--porcelain')
        return len(output) > 0
    
    def has_unpushed_commits(self) -> bool:
        """Verifica se há commits não enviados"""
        branch = self.get_current_branch()
        code, output, _ = self.run_git_command(
            'rev-list', f'@{{u}}..HEAD'
        )
        return len(output) > 0
    
    def get_current_branch(self) -> str:
        """Obtém a branch atual"""
        code, output, _ = self.run_git_command(
            'rev-parse', '--abbrev-ref', 'HEAD'
        )
        return output if code == 0 else 'main'
    
    def get_status(self) -> str:
        """Obtém status do repositório"""
        code, output, _ = self.run_git_command('status', '--short')
        return output
    
    def commit_and_push(self, message: str) -> bool:
        """Faz commit e push com retry"""
        branch = self.get_current_branch()
        
        logger.info(f"Fazendo commit na branch '{branch}'...")
        
        # Stage todas as alterações
        code, _, stderr = self.run_git_command('add', '-A')
        if code != 0:
            logger.error(f"Erro ao fazer stage: {stderr}")
            return False
        
        # Commit
        code, output, stderr = self.run_git_command('commit', '-m', message)
        if code != 0:
            if 'nothing to commit' in stderr or 'nothing to commit' in output:
                logger.warning("Nenhuma alteração para fazer commit")
            else:
                logger.error(f"Erro ao fazer commit: {stderr}")
            return False
        
        logger.info(f"✓ Commit realizado: {message}")
        
        # Push com retry
        for attempt in range(1, self.max_retries + 1):
            logger.info(f"Fazendo push para origin/{branch} (tentativa {attempt}/{self.max_retries})...")
            
            code, output, stderr = self.run_git_command('push', 'origin', branch)
            if code == 0:
                logger.info("✓ Push realizado com sucesso!")
                logger.info("✓ Deploy automático trigerrado no Render")
                return True
            else:
                if attempt < self.max_retries:
                    logger.warning(f"Push falhou. Aguardando {self.retry_delay}s antes de tentar novamente...")
                    time.sleep(self.retry_delay)
        
        logger.error(f"Falha ao fazer push após {self.max_retries} tentativas")
        return False

# ============================================================================
# FileSystemEventHandler
# ============================================================================

class RepositoryChangeHandler(FileSystemEventHandler):
    """Handler para detectar alterações no repositório"""
    
    def __init__(self, git_manager: GitManager):
        self.git_manager = git_manager
        self.last_push_time = 0
        self.push_cooldown = 10  # segundos
        self.pending_changes = False
    
    def on_modified(self, event):
        """Chamado quando um arquivo é modificado"""
        if event.is_directory:
            return
        
        # Ignorar arquivos do Git e logs
        if any(x in event.src_path for x in ['.git', '.logs', '.auto-push.log']):
            return
        
        self.pending_changes = True
        logger.debug(f"Alteração detectada: {event.src_path}")
    
    def on_created(self, event):
        """Chamado quando um arquivo é criado"""
        if event.is_directory:
            return
        
        if any(x in event.src_path for x in ['.git', '.logs', '.auto-push.log']):
            return
        
        self.pending_changes = True
        logger.debug(f"Arquivo criado: {event.src_path}")
    
    def on_deleted(self, event):
        """Chamado quando um arquivo é deletado"""
        if event.is_directory:
            return
        
        if any(x in event.src_path for x in ['.git', '.logs', '.auto-push.log']):
            return
        
        self.pending_changes = True
        logger.debug(f"Arquivo deletado: {event.src_path}")
    
    def should_push(self) -> bool:
        """Verifica se deve fazer push"""
        current_time = time.time()
        
        if not self.pending_changes:
            return False
        
        if current_time - self.last_push_time < self.push_cooldown:
            return False
        
        if not self.git_manager.has_changes() and not self.git_manager.has_unpushed_commits():
            self.pending_changes = False
            return False
        
        return True
    
    def do_push(self):
        """Faz push se necessário"""
        if not self.should_push():
            return
        
        self.last_push_time = time.time()
        self.pending_changes = False
        
        message = f"Auto-push: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        self.git_manager.commit_and_push(message)

# ============================================================================
# Main
# ============================================================================

def print_banner():
    """Exibe banner do script"""
    print("\n" + "="*60)
    print("  Script de Auto-Push para GitHub - Academia Santiago")
    print("="*60 + "\n")

def print_status(git_manager: GitManager):
    """Exibe status do repositório"""
    print("\n" + "-"*60)
    print("Status do Repositório")
    print("-"*60)
    
    branch = git_manager.get_current_branch()
    print(f"Branch: {branch}")
    
    status = git_manager.get_status()
    if status:
        print("\nArquivos modificados:")
        for line in status.split('\n'):
            print(f"  {line}")
    else:
        print("Sem alterações")
    
    print("-"*60 + "\n")

def main():
    """Função principal"""
    print_banner()
    
    git_manager = GitManager()
    
    # Verificações iniciais
    if not git_manager.check_config():
        sys.exit(1)
    
    if not git_manager.check_remote():
        sys.exit(1)
    
    print_status(git_manager)
    
    # Configurar observer
    logger.info("Iniciando monitoramento de alterações...")
    logger.info("Pressione Ctrl+C para parar\n")
    
    event_handler = RepositoryChangeHandler(git_manager)
    observer = Observer()
    observer.schedule(event_handler, path=str(git_manager.repo_path), recursive=True)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
            event_handler.do_push()
    except KeyboardInterrupt:
        logger.info("\nScript interrompido pelo usuário")
        observer.stop()
    
    observer.join()
    logger.info("Script finalizado")

if __name__ == '__main__':
    main()
