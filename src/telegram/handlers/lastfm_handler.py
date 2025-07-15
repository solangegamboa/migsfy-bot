    async def lastfm_tag_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /lastfm_tag para baixar músicas populares de uma tag do Last.fm"""
        if not self._is_authorized(update):
            return
        
        # Verificar se há argumentos
        if not context.args:
            await update.message.reply_text(
                "❌ Por favor, forneça uma tag do Last.fm.\n"
                "Exemplo: `/lastfm_tag rock alternativo`\n"
                "Opcionalmente, você pode especificar o número de músicas: `/lastfm_tag rock alternativo 50`",
                parse_mode='Markdown'
            )
            return
        
        # Verificar se o último argumento é um número (quantidade de músicas)
        limit = 25  # Valor padrão
        tag_parts = context.args.copy()
        
        if tag_parts and tag_parts[-1].isdigit():
            limit = int(tag_parts.pop())
            if limit > 100:
                await update.message.reply_text(
                    "⚠️ Limite máximo é 100 músicas. Usando 100 como limite.",
                    parse_mode='Markdown'
                )
                limit = 100
        
        # Juntar os argumentos restantes para formar a tag
        tag_name = " ".join(tag_parts)
        
        # Informar ao usuário que o processo começou
        status_message = await update.message.reply_text(
            f"🔍 Buscando as {limit} músicas mais populares da tag *{tag_name}* no Last.fm...\n"
            "Este processo pode levar alguns minutos.",
            parse_mode='Markdown'
        )
        
        # Criar uma tarefa assíncrona para o download
        task_id = f"lastfm_tag_{int(time.time())}"
        task_description = f"Download de músicas da tag '{tag_name}' do Last.fm"
        
        # Adicionar à lista de tarefas
        self.tasks[task_id] = {
            "description": task_description,
            "status": "running",
            "start_time": datetime.now(),
            "chat_id": update.effective_chat.id,
            "message_id": status_message.message_id
        }
        
        # Executar o download em uma thread separada
        asyncio.create_task(self._download_lastfm_tag(update, tag_name, limit, task_id, status_message))
    
    async def _download_lastfm_tag(self, update, tag_name, limit, task_id, status_message):
        """Função assíncrona para baixar músicas de uma tag do Last.fm"""
        try:
            # Importar o módulo Last.fm
            from core.lastfm import download_tracks_by_tag
            
            # Atualizar mensagem de status
            await status_message.edit_text(
                f"⏳ Iniciando download das {limit} músicas mais populares da tag *{tag_name}*...\n"
                "As músicas que já foram baixadas anteriormente serão puladas.",
                parse_mode='Markdown'
            )
            
            # Executar o download em uma thread separada para não bloquear o bot
            loop = asyncio.get_event_loop()
            total, successful, failed, skipped = await loop.run_in_executor(
                None, 
                lambda: download_tracks_by_tag(tag_name, limit=limit, skip_existing=True)
            )
            
            # Atualizar status da tarefa
            self.tasks[task_id]["status"] = "completed"
            self.tasks[task_id]["end_time"] = datetime.now()
            
            # Calcular tempo decorrido
            elapsed_time = self.tasks[task_id]["end_time"] - self.tasks[task_id]["start_time"]
            elapsed_str = str(elapsed_time).split('.')[0]  # Remover microssegundos
            
            # Enviar mensagem de conclusão
            if total == 0:
                await status_message.edit_text(
                    f"❌ Nenhuma música encontrada para a tag *{tag_name}*.",
                    parse_mode='Markdown'
                )
            else:
                # Calcular porcentagem de sucesso
                success_rate = (successful / (total - skipped)) * 100 if total > skipped else 0
                
                await status_message.edit_text(
                    f"✅ Download da tag *{tag_name}* concluído em {elapsed_str}!\n\n"
                    f"📊 *Estatísticas:*\n"
                    f"- Total de músicas: {total}\n"
                    f"- Downloads bem-sucedidos: {successful}\n"
                    f"- Downloads com falha: {failed}\n"
                    f"- Músicas puladas (já baixadas): {skipped}\n"
                    f"- Taxa de sucesso: {success_rate:.1f}%",
                    parse_mode='Markdown'
                )
        
        except Exception as e:
            logger.error(f"Erro ao baixar músicas da tag '{tag_name}': {e}")
            
            # Atualizar status da tarefa
            self.tasks[task_id]["status"] = "failed"
            self.tasks[task_id]["end_time"] = datetime.now()
            
            # Enviar mensagem de erro
            await status_message.edit_text(
                f"❌ Erro ao baixar músicas da tag *{tag_name}*:\n`{str(e)}`",
                parse_mode='Markdown'
            )
