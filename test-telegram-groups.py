#!/usr/bin/env python3
"""
Script de teste para verificar configurações de grupos e threads do bot Telegram
"""

import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

def test_group_thread_config():
    """Testa configurações de grupos e threads"""
    
    print("🧪 Testando configurações de grupos e threads\n")
    
    # Obtém configurações
    allowed_users = os.getenv('TELEGRAM_ALLOWED_USERS', '')
    allowed_groups = os.getenv('TELEGRAM_ALLOWED_GROUPS', '')
    allowed_threads = os.getenv('TELEGRAM_ALLOWED_THREADS', '')
    
    print("📋 Configurações atuais:")
    print(f"TELEGRAM_ALLOWED_USERS: {allowed_users or '(não configurado)'}")
    print(f"TELEGRAM_ALLOWED_GROUPS: {allowed_groups or '(não configurado)'}")
    print(f"TELEGRAM_ALLOWED_THREADS: {allowed_threads or '(não configurado)'}")
    print()
    
    # Testa parsing de usuários
    if allowed_users:
        try:
            users = [int(user_id.strip()) for user_id in allowed_users.split(',') if user_id.strip()]
            print(f"✅ Usuários permitidos: {users}")
        except ValueError as e:
            print(f"❌ Erro ao processar usuários: {e}")
    
    # Testa parsing de grupos
    if allowed_groups:
        try:
            groups = [int(group_id.strip()) for group_id in allowed_groups.split(',') if group_id.strip()]
            print(f"✅ Grupos permitidos: {groups}")
        except ValueError as e:
            print(f"❌ Erro ao processar grupos: {e}")
    
    # Testa parsing de threads
    if allowed_threads:
        try:
            threads_dict = {}
            for thread_config in allowed_threads.split(','):
                if ':' in thread_config:
                    group_id, thread_id = thread_config.strip().split(':', 1)
                    group_id = int(group_id)
                    thread_id = int(thread_id)
                    
                    if group_id not in threads_dict:
                        threads_dict[group_id] = []
                    threads_dict[group_id].append(thread_id)
            
            print(f"✅ Threads permitidas: {threads_dict}")
            
            # Verifica consistência
            if allowed_groups:
                groups = [int(group_id.strip()) for group_id in allowed_groups.split(',') if group_id.strip()]
                for group_id in threads_dict.keys():
                    if group_id not in groups:
                        print(f"⚠️  Aviso: Grupo {group_id} tem threads configuradas mas não está em TELEGRAM_ALLOWED_GROUPS")
            
        except ValueError as e:
            print(f"❌ Erro ao processar threads: {e}")
    
    print("\n🔍 Simulando cenários de autorização:")
    
    # Obtém IDs reais das configurações para teste
    real_users = []
    real_groups = []
    
    if allowed_users:
        try:
            real_users = [int(user_id.strip()) for user_id in allowed_users.split(',') if user_id.strip()]
        except:
            pass
    
    if allowed_groups:
        try:
            real_groups = [int(group_id.strip()) for group_id in allowed_groups.split(',') if group_id.strip()]
        except:
            pass
    
    # Simula diferentes cenários com IDs reais quando possível
    test_scenarios = [
        {
            'name': 'Chat privado com usuário permitido',
            'chat_type': 'private',
            'chat_id': real_users[0] if real_users else 123456789,
            'user_id': real_users[0] if real_users else 123456789,
            'thread_id': None
        },
        {
            'name': 'Chat privado com usuário não permitido',
            'chat_type': 'private',
            'chat_id': 999999999,
            'user_id': 999999999,
            'thread_id': None
        },
        {
            'name': 'Grupo permitido sem thread específica',
            'chat_type': 'supergroup',
            'chat_id': real_groups[0] if real_groups else -1001234567890,
            'user_id': real_users[0] if real_users else 123456789,
            'thread_id': None
        },
        {
            'name': 'Thread permitida',
            'chat_type': 'supergroup',
            'chat_id': real_groups[0] if real_groups else -1001234567890,
            'user_id': real_users[0] if real_users else 123456789,
            'thread_id': 123
        },
        {
            'name': 'Thread não permitida',
            'chat_type': 'supergroup',
            'chat_id': real_groups[0] if real_groups else -1001234567890,
            'user_id': real_users[0] if real_users else 123456789,
            'thread_id': 999
        }
    ]
    
    for scenario in test_scenarios:
        result = simulate_authorization(scenario, allowed_users, allowed_groups, allowed_threads)
        status = "✅ Permitido" if result else "❌ Negado"
        print(f"{status} - {scenario['name']}")

def simulate_authorization(scenario, allowed_users_str, allowed_groups_str, allowed_threads_str):
    """Simula lógica de autorização"""
    
    # Parse configurações com tratamento de erro
    allowed_users = []
    if allowed_users_str:
        try:
            allowed_users = [int(user_id.strip()) for user_id in allowed_users_str.split(',') if user_id.strip() and ':' not in user_id.strip()]
        except ValueError:
            pass
    
    allowed_groups = []
    if allowed_groups_str:
        try:
            allowed_groups = [int(group_id.strip()) for group_id in allowed_groups_str.split(',') if group_id.strip()]
        except ValueError:
            pass
    
    allowed_threads = {}
    if allowed_threads_str:
        for thread_config in allowed_threads_str.split(','):
            if ':' in thread_config:
                try:
                    group_id, thread_id = thread_config.strip().split(':', 1)
                    group_id = int(group_id)
                    thread_id = int(thread_id)
                    
                    if group_id not in allowed_threads:
                        allowed_threads[group_id] = []
                    allowed_threads[group_id].append(thread_id)
                except ValueError:
                    continue
    
    # Lógica de autorização
    chat_type = scenario['chat_type']
    chat_id = scenario['chat_id']
    user_id = scenario['user_id']
    thread_id = scenario['thread_id']
    
    # Chat privado
    if chat_type == 'private':
        if not allowed_users:
            return True  # Se não há lista, permite todos em privado
        return user_id in allowed_users
    
    # Grupo/supergrupo
    elif chat_type in ['group', 'supergroup']:
        # Verifica se o grupo está permitido
        if allowed_groups and chat_id not in allowed_groups:
            return False
        
        # Se há configuração de threads específicas para este grupo
        if chat_id in allowed_threads:
            # Se a mensagem não tem thread_id (mensagem no grupo principal)
            if thread_id is None:
                return False
            
            # Verifica se a thread está permitida
            return thread_id in allowed_threads[chat_id]
        
        # Se não há configuração específica de threads, permite o grupo todo
        elif allowed_groups and chat_id in allowed_groups:
            return True
        
        # Se não há configuração de grupos, nega acesso
        return False
    
    return False

if __name__ == "__main__":
    test_group_thread_config()
