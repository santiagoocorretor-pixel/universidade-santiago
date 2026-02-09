# 🚀 Script de Auto-Push para GitHub

Este documento explica como usar os scripts de auto-push para automatizar o envio de alterações para o GitHub e triggar deploy automático no Render.

## 📋 Visão Geral

Quando você faz alterações nos arquivos do projeto, o script automaticamente:

1. **Detecta** as alterações no repositório
2. **Faz commit** com timestamp automático
3. **Faz push** para o GitHub
4. **Trigga deploy automático** no Render

## 🛠️ Opções Disponíveis

### Opção 1: Script Bash (auto-push.sh)

**Vantagens:**
- Simples e leve
- Funciona em qualquer sistema Unix/Linux
- Sem dependências externas
- Fácil de entender e modificar

**Desvantagens:**
- Verificação a cada 5 segundos (menos eficiente)
- Consome mais CPU

**Uso:**

```bash
./auto-push.sh
```

### Opção 2: Script Python (auto-push.py) - RECOMENDADO ⭐

**Vantagens:**
- Monitora alterações em tempo real (mais eficiente)
- Usa watchdog para detecção de eventos
- Melhor performance
- Logs coloridos e estruturados
- Cooldown inteligente entre pushes

**Desvantagens:**
- Requer Python 3 e biblioteca `watchdog`

**Instalação de dependências:**

```bash
pip3 install watchdog
```

**Uso:**

```bash
./auto-push.py
```

## 📦 Instalação

### 1. Clone o repositório (se ainda não tiver)

```bash
git clone https://github.com/santiagoocorretor-pixel/academia-santiago2.git
cd academia-santiago2
```

### 2. Configure o Git (se necessário)

```bash
git config user.name "Seu Nome"
git config user.email "seu.email@example.com"
```

### 3. Escolha o script e execute

**Para usar o script Python (recomendado):**

```bash
# Instalar watchdog
pip3 install watchdog

# Executar script
./auto-push.py
```

**Para usar o script Bash:**

```bash
./auto-push.sh
```

## 🎯 Como Funciona

### Fluxo de Funcionamento

```
┌─────────────────────────────────────────┐
│  Arquivo modificado/criado/deletado    │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  Script detecta alteração               │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  Aguarda cooldown (10s)                 │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  git add -A                             │
│  git commit -m "Auto-push: ..."         │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  git push origin main                   │
│  (com retry automático)                 │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  Render detecta novo commit             │
│  e inicia deploy automático             │
└─────────────────────────────────────────┘
```

### Configurações

**Script Bash (auto-push.sh):**
- `WATCH_INTERVAL=5` - Intervalo de verificação em segundos
- `MAX_RETRIES=3` - Número máximo de tentativas de push
- `RETRY_DELAY=10` - Tempo entre tentativas em segundos

**Script Python (auto-push.py):**
- `push_cooldown=10` - Tempo mínimo entre pushes em segundos
- `max_retries=3` - Número máximo de tentativas de push
- `retry_delay=10` - Tempo entre tentativas em segundos

## 📝 Exemplos de Uso

### Exemplo 1: Iniciar o script em background

```bash
# Bash
nohup ./auto-push.sh > auto-push.log 2>&1 &

# Python
nohup ./auto-push.py > auto-push.log 2>&1 &
```

### Exemplo 2: Monitorar logs em tempo real

```bash
tail -f .logs/auto-push.log
```

### Exemplo 3: Parar o script

```bash
# Encontrar o processo
ps aux | grep auto-push

# Matar o processo
kill <PID>
```

## 🔍 Monitoramento

### Logs

Os scripts geram logs em:
- **Arquivo:** `.logs/auto-push.log`
- **Console:** Saída colorida em tempo real

### Exemplo de log

```
12:34:56 [INFO] Verificando configuração do Git...
12:34:56 [INFO] ✓ Git configurado corretamente
12:34:56 [INFO] Verificando conexão com repositório remoto...
12:34:57 [INFO] ✓ Repositório remoto acessível
12:34:57 [INFO] Iniciando monitoramento de alterações...
12:35:02 [DEBUG] Alteração detectada: index.html
12:35:12 [INFO] Fazendo commit na branch 'main'...
12:35:12 [INFO] ✓ Commit realizado: Auto-push: 2026-02-09 12:35:12
12:35:13 [INFO] Fazendo push para origin/main (tentativa 1/3)...
12:35:14 [INFO] ✓ Push realizado com sucesso!
12:35:14 [INFO] ✓ Deploy automático trigerrado no Render
```

## ⚙️ Configuração do Render

Para que o deploy automático funcione, o Render precisa estar configurado para:

1. **Auto-deploy:** Habilitado para a branch `main`
2. **Build Command:** `npm install --production`
3. **Start Command:** `node server.js`

## 🚨 Troubleshooting

### Erro: "Git user.name não configurado"

```bash
git config user.name "Seu Nome"
git config user.email "seu.email@example.com"
```

### Erro: "Não conseguiu conectar ao repositório remoto"

```bash
# Verificar remoto
git remote -v

# Testar conexão
git ls-remote origin
```

### Erro: "watchdog não está instalado" (Python)

```bash
pip3 install watchdog
```

### Script não está fazendo push

1. Verifique se há alterações: `git status`
2. Verifique os logs: `tail -f .logs/auto-push.log`
3. Verifique conexão com GitHub: `git push origin main` (manual)

## 🔐 Segurança

### Token de Acesso

O token de acesso ao GitHub está configurado na URL remota. Para verificar:

```bash
git remote -v
```

**⚠️ IMPORTANTE:** Não compartilhe o token com ninguém!

### Variáveis de Ambiente

Se preferir usar variáveis de ambiente em vez de token na URL:

```bash
export GITHUB_TOKEN="seu_token_aqui"
git remote set-url origin https://${GITHUB_TOKEN}@github.com/santiagoocorretor-pixel/academia-santiago2.git
```

## 📊 Estatísticas

### Uso de Recursos

**Script Bash:**
- CPU: ~1-2% (verificação a cada 5s)
- Memória: ~5-10 MB

**Script Python:**
- CPU: <1% (monitoramento em tempo real)
- Memória: ~20-30 MB

## 🎓 Dicas e Boas Práticas

1. **Use o script Python** para melhor performance
2. **Monitore os logs** regularmente
3. **Teste manualmente** antes de confiar no script
4. **Verifique o Render** após cada push
5. **Faça commits significativos** com mensagens descritivas

## 📞 Suporte

Se encontrar problemas:

1. Verifique os logs: `tail -f .logs/auto-push.log`
2. Teste manualmente: `git push origin main`
3. Verifique a conexão: `git ls-remote origin`
4. Verifique o Render dashboard para status de deploy

## 📄 Licença

Este script é parte do projeto Academia Santiago e está disponível para uso livre.

---

**Última atualização:** 2026-02-09
**Versão:** 1.0
