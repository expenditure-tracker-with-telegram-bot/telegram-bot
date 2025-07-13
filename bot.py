import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv
load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
API_GATEWAY_URL = os.getenv("API_GATEWAY_URL")

user_tokens = {}

def get_auth_headers(user_id):
    if user_id in user_tokens:
        return {"Authorization": f"Bearer {user_tokens[user_id]}"}
    return None

def format_json_for_telegram(data):
    import json
    return f"<pre>{json.dumps(data, indent=2)}</pre>"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a welcome message with a list of all commands."""
    help_text = (
        "Welcome to the Expenditure Tracker Bot!\n\n"
        "--- User Commands ---\n"
        "/signup `<username>` `<password>` - Create a new account\n"
        "/login `<username>` `<password>` - Log in to get a token\n"
        "/logout - Log out and invalidate your token\n\n"
        "--- Category Commands ---\n"
        "/addcategory `<name>` `<type>` - (e.g., Food expense)\n"
        "/listcategories - View your categories\n\n"
        "--- Transaction Commands ---\n"
        "/addtransaction `<amount>` `<type>` `<desc>`\n"
        "/listtransactions - View your transactions\n"
        "/updatetransaction `<id>` `<new_amount>` `<new_desc>`\n"
        "/deletetransaction `<id>` - Delete a transaction\n"
        "/summary - Get your income/expense summary\n\n"
        "--- Admin Commands ---\n"
        "/listusers - List all users\n"
        "/listallcategories - List all categories (admin)\n"
        "/stats - Get system-wide statistics (admin)"
    )
    await update.message.reply_text(help_text)

async def signup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        username, password = context.args
        # This now correctly constructs the URL
        response = requests.post(f"http://{API_GATEWAY_URL}/auth/signup", json={"username": username, "password": password})
        await update.message.reply_html(format_json_for_telegram(response.json()))
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /signup <username> <password>")
    except Exception as e:
        await update.message.reply_text(f"An error occurred: {e}")

async def login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    try:
        username, password = context.args
        response = requests.post(f"http://{API_GATEWAY_URL}/auth/login", json={"username": username, "password": password})
        if response.status_code == 200:
            token = response.json().get("token")
            user_tokens[user_id] = token
            await update.message.reply_text("Login successful! Token saved.")
        else:
            await update.message.reply_html(format_json_for_telegram(response.json()))
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /login <username> <password>")
    except Exception as e:
        await update.message.reply_text(f"An error occurred: {e}")

async def logout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    headers = get_auth_headers(user_id)
    if not headers:
        await update.message.reply_text("You are not logged in.")
        return

    response = requests.post(f"http://{API_GATEWAY_URL}/auth/logout", headers=headers)
    if response.status_code == 200:
        if user_id in user_tokens:
            del user_tokens[user_id]
        await update.message.reply_text("Logout successful.")
    else:
        await update.message.reply_html(format_json_for_telegram(response.json()))

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    headers = get_auth_headers(user_id)
    if not headers:
        await update.message.reply_text("You must be logged in as an admin.")
        return

    response = requests.get(f"http://{API_GATEWAY_URL}/auth/admin/users", headers=headers)
    await update.message.reply_html(format_json_for_telegram(response.json()))

async def add_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    headers = get_auth_headers(user_id)
    if not headers:
        await update.message.reply_text("You must be logged in.")
        return

    try:
        name, cat_type = context.args
        payload = {"name": name, "type": cat_type}
        response = requests.post(f"http://{API_GATEWAY_URL}/category/create", json=payload, headers=headers)
        await update.message.reply_html(format_json_for_telegram(response.json()))
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /addcategory <name> <type>")

async def list_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    headers = get_auth_headers(user_id)
    if not headers:
        await update.message.reply_text("You must be logged in.")
        return

    response = requests.get(f"http://{API_GATEWAY_URL}/category/list", headers=headers)
    await update.message.reply_html(format_json_for_telegram(response.json()))

async def list_all_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    headers = get_auth_headers(user_id)
    if not headers:
        await update.message.reply_text("You must be logged in as an admin.")
        return

    response = requests.get(f"http://{API_GATEWAY_URL}/category/admin/all", headers=headers)
    await update.message.reply_html(format_json_for_telegram(response.json()))

async def add_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    headers = get_auth_headers(user_id)
    if not headers:
        await update.message.reply_text("You must be logged in.")
        return

    try:
        amount, tx_type, *desc_parts = context.args
        desc = " ".join(desc_parts)
        payload = {"amount": float(amount), "type": tx_type, "desc": desc}
        response = requests.post(f"http://{API_GATEWAY_URL}/transaction/add", json=payload, headers=headers)
        await update.message.reply_html(format_json_for_telegram(response.json()))
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /addtransaction <amount> <type> <description>")

async def list_transactions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    headers = get_auth_headers(user_id)
    if not headers:
        await update.message.reply_text("You must be logged in.")
        return

    response = requests.get(f"http://{API_GATEWAY_URL}/transaction/list", headers=headers)
    await update.message.reply_html(format_json_for_telegram(response.json()))

async def update_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    headers = get_auth_headers(user_id)
    if not headers:
        await update.message.reply_text("You must be logged in.")
        return

    try:
        tx_id, amount, *desc_parts = context.args
        desc = " ".join(desc_parts)
        payload = {"amount": float(amount), "desc": desc}
        response = requests.put(f"http://{API_GATEWAY_URL}/transaction/update/{tx_id}", json=payload, headers=headers)
        await update.message.reply_html(format_json_for_telegram(response.json()))
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /updatetransaction <id> <new_amount> <new_description>")

async def delete_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    headers = get_auth_headers(user_id)
    if not headers:
        await update.message.reply_text("You must be logged in.")
        return

    try:
        tx_id = context.args[0]
        response = requests.delete(f"http://{API_GATEWAY_URL}/transaction/delete/{tx_id}", headers=headers)
        await update.message.reply_html(format_json_for_telegram(response.json()))
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /deletetransaction <id>")

async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    headers = get_auth_headers(user_id)
    if not headers:
        await update.message.reply_text("You must be logged in.")
        return

    response = requests.get(f"http://{API_GATEWAY_URL}/transaction/summary", headers=headers)
    await update.message.reply_html(format_json_for_telegram(response.json()))

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    headers = get_auth_headers(user_id)
    if not headers:
        await update.message.reply_text("You must be logged in as an admin.")
        return

    response = requests.get(f"http://{API_GATEWAY_URL}/transaction/admin/stats", headers=headers)
    await update.message.reply_html(format_json_for_telegram(response.json()))

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("signup", signup))
    app.add_handler(CommandHandler("login", login))
    app.add_handler(CommandHandler("logout", logout))
    app.add_handler(CommandHandler("listusers", list_users))
    app.add_handler(CommandHandler("addcategory", add_category))
    app.add_handler(CommandHandler("listcategories", list_categories))
    app.add_handler(CommandHandler("listallcategories", list_all_categories))
    app.add_handler(CommandHandler("addtransaction", add_transaction))
    app.add_handler(CommandHandler("listtransactions", list_transactions))
    app.add_handler(CommandHandler("updatetransaction", update_transaction))
    app.add_handler(CommandHandler("deletetransaction", delete_transaction))
    app.add_handler(CommandHandler("summary", summary))
    app.add_handler(CommandHandler("stats", stats))

    app.run_polling()

if __name__ == "__main__":
    main()
