import os
import re
import requests
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

API_USERS = "https://ultrabuscax-1.onrender.com/api/users"
API_LIBERAR = "https://ultrabuscax-1.onrender.com/api/liberar-acesso"

SITE_CADASTRO = "https://felipethanzin.github.io/UltraBuscaX/cadastro/cadastro.html"
SITE_HOME = "https://felipethanzin.github.io/UltraBuscaX/home/home.html"

menu = ReplyKeyboardMarkup(
    [
        ["🔐 Liberar acesso"],
        ["🌐 Site", "📝 Cadastro"],
        ["ℹ️ Ajuda", "📞 Suporte"]
    ],
    resize_keyboard=True
)


def email_valido(email):
    padrao = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(padrao, email)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    mensagem = """
🔍✨ BEM-VINDO AO BOT ULTRABUSCAX ✨🔍

Aqui você pode:

🔐 Liberar seu acesso ao sistema
📧 Validar seu e-mail cadastrado
🌐 Acessar o site oficial
📝 Fazer cadastro
📞 Pedir suporte

Clique em uma opção abaixo:
"""

    await update.message.reply_text(mensagem, reply_markup=menu)


async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        """
ℹ️ AJUDA - ULTRABUSCAX

1️⃣ Clique em "🔐 Liberar acesso"
2️⃣ Digite seu e-mail cadastrado
3️⃣ Envie o código que apareceu no site
4️⃣ Volte para o site e use as ferramentas

Comandos:
/start - Iniciar bot
/cancelar - Cancelar operação
/ajuda - Ver ajuda
"""
    )


async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "❌ Operação cancelada.\nDigite /start para começar novamente.",
        reply_markup=menu
    )


async def mensagens(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()
    etapa = context.user_data.get("etapa")

    if texto == "🔐 Liberar acesso":
        context.user_data.clear()
        context.user_data["etapa"] = "email"

        await update.message.reply_text(
            "📧 Digite seu e-mail cadastrado no UltraBuscaX:"
        )
        return

    if texto == "🌐 Site":
        await update.message.reply_text(f"🌐 Acesse o site:\n{SITE_HOME}")
        return

    if texto == "📝 Cadastro":
        await update.message.reply_text(f"📝 Faça seu cadastro aqui:\n{SITE_CADASTRO}")
        return

    if texto == "ℹ️ Ajuda":
        await ajuda(update, context)
        return

    if texto == "📞 Suporte":
        await update.message.reply_text(
            "📞 Suporte UltraBuscaX\n\n"
            "Envie uma mensagem explicando seu problema.\n"
            "Exemplo: Não consigo liberar meu acesso."
        )
        return

    if etapa == "email":
        email_usuario = texto.lower()

        if not email_valido(email_usuario):
            await update.message.reply_text(
                "⚠️ E-mail inválido.\nDigite um e-mail correto.\n\nExemplo:\nusuario@gmail.com"
            )
            return

        context.user_data["email"] = email_usuario

        await update.message.reply_text("🔎 Verificando e-mail no sistema...")

        try:
            resposta = requests.get(API_USERS, timeout=15)

            if resposta.status_code != 200:
                await update.message.reply_text("⚠️ Erro ao acessar a API.")
                return

            resultado = resposta.json()
            usuarios = resultado.get("data", [])

            usuario_encontrado = None

            for usuario in usuarios:
                email_api = usuario.get("email", "").strip().lower()

                if email_api == email_usuario:
                    usuario_encontrado = usuario
                    break

            if usuario_encontrado:
                nome = usuario_encontrado.get("nome", "Usuário")
                context.user_data["nome"] = nome
                context.user_data["etapa"] = "codigo"

                await update.message.reply_text(
                    f"✅ E-mail encontrado!\n\n"
                    f"👤 Usuário: {nome}\n"
                    f"📧 E-mail: {email_usuario}\n\n"
                    f"🔐 Agora envie o código que apareceu no site:"
                )
            else:
                await update.message.reply_text(
                    "❌ E-mail não encontrado no sistema.\n\n"
                    "📝 Faça seu cadastro aqui:\n"
                    f"{SITE_CADASTRO}"
                )

        except requests.exceptions.Timeout:
            await update.message.reply_text(
                "⏳ O servidor demorou para responder.\nTente novamente em alguns instantes."
            )

        except Exception as erro:
            print("Erro ao verificar e-mail:", erro)
            await update.message.reply_text(
                "🚫 Não foi possível conectar ao servidor."
            )

        return

    if etapa == "codigo":
        codigo_acesso = texto.upper()
        email_usuario = context.user_data.get("email")

        if len(codigo_acesso) < 4:
            await update.message.reply_text(
                "⚠️ Código muito curto.\nEnvie o código correto que apareceu no site."
            )
            return

        await update.message.reply_text("🔐 Validando código...")

        try:
            dados = {
                "email": email_usuario,
                "codigo": codigo_acesso
            }

            resposta = requests.post(API_LIBERAR, json=dados, timeout=15)

            if resposta.status_code == 200:
                await update.message.reply_text(
                    "🔓 ACESSO LIBERADO COM SUCESSO!\n\n"
                    "✅ Agora volte para o site.\n"
                    "🌐 As ferramentas serão desbloqueadas automaticamente.\n\n"
                    f"{SITE_HOME}",
                    reply_markup=menu
                )

                context.user_data.clear()

            elif resposta.status_code == 400:
                await update.message.reply_text(
                    "❌ Código inválido.\nConfira o código no site e tente novamente."
                )

            elif resposta.status_code == 404:
                await update.message.reply_text(
                    "❌ E-mail ou código não encontrado."
                )

            else:
                await update.message.reply_text(
                    "⚠️ Erro ao liberar acesso.\nTente novamente."
                )

        except requests.exceptions.Timeout:
            await update.message.reply_text(
                "⏳ O servidor demorou para responder.\nTente novamente."
            )

        except Exception as erro:
            print("Erro ao liberar acesso:", erro)
            await update.message.reply_text(
                "🚫 Erro ao conectar com a API."
            )

        return

    await update.message.reply_text(
        "⚠️ Escolha uma opção no menu ou digite /start.",
        reply_markup=menu
    )


def iniciar_bot():
    if not TOKEN:
        print("❌ ERRO: Token não encontrado.")
        print("Crie um arquivo .env com:")
        print("BOT_TOKEN=SEU_TOKEN_AQUI")
        return

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ajuda", ajuda))
    app.add_handler(CommandHandler("cancelar", cancelar))

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            mensagens
        )
    )

    print("🤖 Bot UltraBuscaX iniciado com sucesso!")
    app.run_polling()


if __name__ == "__main__":
    iniciar_bot()
    