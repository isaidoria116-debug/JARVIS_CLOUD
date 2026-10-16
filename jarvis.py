# --- INTEGRACIÓN ASÍNCRONA CON TELEGRAM ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usuario_id = str(update.effective_user.id)
    # Limpiamos la memoria del usuario al reiniciar el bot con /start
    if usuario_id in MEMORIA_USUARIOS:
        MEMORIA_USUARIOS[usuario_id].clear()
    await update.message.reply_text("Protocolos J.A.R.V.I.S. Cloud v3.5 iniciados. En línea, memoria activa y escuchando, Señor.")

async def responder_telegram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje_usuario = update.message.text
    usuario_id = str(update.effective_user.id)
    
    # El bot simula que está escribiendo en el chat de Telegram
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    # Procesar comando enviando el ID del usuario de Telegram para gestionar su memoria única
    respuesta_jarvis = generar_respuesta_jarvis(usuario_id, mensaje_usuario)
    await update.message.reply_text(respuesta_jarvis)

@app.on_event("startup")
async def iniciar_bot_telegram():
    # --- PONE TUS TOKENS DIRECTAMENTE AQUÍ ---
    token_telegram = "8837254965:AAEMzgOybDw7nV_O9otKjloEoOO-mnTI5-g"
    
    # IMPORTANTE: Reemplaza las comillas de abajo con tu clave real de Google Gemini
    os.environ["GEMINI_API_KEY"] = "AQ.Ab8RN6KYlxDa3q72cLijHrIoSs2JV7mDhCERrhWEbxCnmwzfJw"
    
    if not token_telegram:
        print("ADVERTENCIA CRÍTICA: Variable TELEGRAM_TOKEN no configurada. Servidor web iniciado sin bot.")
        return

    # Inicializa la aplicación del bot sin bloquear el ciclo de FastAPI
    tg_app = Application.builder().token(token_telegram).build()
    tg_app.add_handler(CommandHandler("start", start))
    tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder_telegram))
    
    await tg_app.initialize()
    await tg_app.start()
    asyncio.create_task(tg_app.updater.start_polling())
