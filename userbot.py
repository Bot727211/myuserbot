from telethon import TelegramClient, events
import os
import asyncio

api_id = 37730713
api_hash = "0101aec7619efb628f0f869c5ccd323a"

client1 = TelegramClient("userbot1", api_id, api_hash)
client2 = TelegramClient("userbot2", api_id, api_hash)
client3 = TelegramClient("userbot3", api_id, api_hash)
clients = [client1, client2, client3]

user_status = {}

async def delete_qr_after_delay(client, chat_id, msg_id, user_id):
    await asyncio.sleep(600) # 10 Minutes
    try:
        current_data = user_status.get(user_id, {})
        if current_data.get('qr_msg_id') == msg_id and current_data.get('status') == 1:
            await client.delete_messages(chat_id, [msg_id])
            user_status[user_id]['status'] = 0
            user_status[user_id]['qr_msg_id'] = None
            await client.send_message(chat_id, "⏰ **QR code expired! Please contact the Admin to get a new QR code.**")
    except: pass

def get_qr_path(plan):
    paths = [f'/sdcard/Download/qr{plan}.jpg', f'/sdcard/Download/QR{plan}.jpg', f'qr{plan}.jpg']
    for p in paths:
        if os.path.exists(p): return p
    return None

async def handle_message(event, client):
    chat_id = event.chat_id
    my_id = (await client.get_me()).id
    
    PLAN_MENU_TEXT = (
        "💰 **Hamare Plans:**\n\n"
        "1️⃣ **₹49 Plan:** 250+ Groups\n"
        "2️⃣ **₹99 Plan:** 350+ Groups + CP Files + Videos + Extra Material\n\n"
        "👉 Buy karne ke liye chat me sirf **49** ya **99** likhein!"
    )
    
    # --- ADMIN COMMANDS (Outgoing Messages) ---
    if event.out or event.sender_id == my_id:
        text = event.raw_text.strip().lower()
        
        if text == "clear":
            await event.reply("🧹 Chat clearing & Bot Reset...")
            async for msg in client.iter_messages(chat_id):
                await client.delete_messages(chat_id, msg.id)
            user_status[chat_id] = {'status': 0, 'qr_msg_id': None, 'menu_msg_id': None, 'stopped': False, 'menu_sent': False}
            return
        
        if text in ["price", "buy"]:
            await event.delete()
            current_data = user_status.get(chat_id, {'status': 0, 'qr_msg_id': None, 'menu_msg_id': None, 'menu_sent': False})
            if current_data.get('menu_msg_id'):
                try: await client.delete_messages(chat_id, [current_data['menu_msg_id']])
                except: pass
                
            msg = await client.send_message(chat_id, PLAN_MENU_TEXT)
            user_status[chat_id] = {'status': 0, 'qr_msg_id': None, 'menu_msg_id': msg.id, 'stopped': False, 'menu_sent': True}
            return

        if text in ["qr 49", "qr 99"]:
            plan = text.split()[1]
            await event.delete()
            
            current_data = user_status.get(chat_id, {'status': 0, 'qr_msg_id': None, 'menu_msg_id': None})
            if current_data.get('qr_msg_id'):
                try: await client.delete_messages(chat_id, [current_data['qr_msg_id']])
                except: pass
                
            qr = get_qr_path(plan)
            if qr:
                custom_caption = (
                    f"✅ **₹{plan} Plan Selected!**\n\n"
                    " 💳 **Pay and send a screenshot.**\n\n"
                    "⚠️ **Limited stock! Please complete the payment within 10 minutes, or the QR code will expire.**"
                )
                msg = await client.send_file(chat_id, qr, caption=custom_caption)
                user_status[chat_id] = {'status': 1, 'qr_msg_id': msg.id, 'menu_msg_id': current_data.get('menu_msg_id'), 'stopped': False, 'menu_sent': True}
                asyncio.create_task(delete_qr_after_delay(client, chat_id, msg.id, chat_id))
            return
            
        bot_phrases = ["hamare plans:", "✅", "price", "limited stock", "welcome!", "chat clearing", "pay and send", "screenshot received!", "qr code expired!"]
        if not any(phrase in text for phrase in bot_phrases) and not text.startswith("qr"):
            if chat_id not in user_status:
                user_status[chat_id] = {'status': 3, 'qr_msg_id': None, 'menu_msg_id': None, 'stopped': True, 'menu_sent': False}
            else:
                user_status[chat_id]['stopped'] = True
                user_status[chat_id]['status'] = 3
        return

    # --- CUSTOMER MESSAGES (Incoming Only) ---
    if event.is_private:
        user_id = event.sender_id
        if not user_id: return
        
        current = user_status.get(user_id, {'status': 0, 'qr_msg_id': None, 'menu_msg_id': None, 'stopped': False, 'menu_sent': False})
        
        if current.get('stopped', False) and current['status'] == 3:
            return

        if event.photo and current['status'] == 1:
            await event.reply("✅ **Screenshot received! Please wait while the admin verifies your payment.**")
            if current['qr_msg_id']:
                try: await client.delete_messages(chat_id, [current['qr_msg_id']])
                except: pass
            user_status[user_id] = {'status': 2, 'qr_msg_id': None, 'menu_msg_id': current.get('menu_msg_id'), 'stopped': False, 'menu_sent': True}
            return

        text = event.raw_text.strip().lower() if event.raw_text else ""
        
        if current['status'] == 2:
            return

        bot_phrases = ["hamare plans:", "✅", "price", "limited stock", "welcome!", "pay and send", "screenshot received!", "qr code expired!"]
        if any(phrase in text for phrase in bot_phrases): return

        if current['status'] == 0:
            if text in ["49", "99"]:
                if current.get('qr_msg_id'):
                    try: await client.delete_messages(chat_id, [current['qr_msg_id']])
                    except: pass
                
                custom_caption = (
                    f"✅ **₹{text} Plan Selected!**\n\n"
                    " 💳 **Pay and send a screenshot.**\n\n"
                    "⚠️ **Limited stock! Please complete the payment within 10 minutes, or the QR code will expire.**"
                )
                qr = get_qr_path(text)
                if qr:
                    msg = await client.send_file(chat_id, qr, caption=custom_caption)
                    user_status[user_id] = {'status': 1, 'qr_msg_id': msg.id, 'menu_msg_id': current.get('menu_msg_id'), 'stopped': False, 'menu_sent': True}
                    asyncio.create_task(delete_qr_after_delay(client, chat_id, msg.id, user_id))
                return

            if (text or event.sticker) and not current.get('menu_sent', False):
                if current.get('menu_msg_id'):
                    try: await client.delete_messages(chat_id, [current['menu_msg_id']])
                    except: pass
                msg = await client.send_message(chat_id, PLAN_MENU_TEXT)
                user_status[user_id] = {'status': 0, 'qr_msg_id': None, 'menu_msg_id': msg.id, 'stopped': False, 'menu_sent': True}
                return

for cli in clients:
    @cli.on(events.NewMessage())
    async def wrapper(event, current_cli=cli):
        await handle_message(event, current_cli)

async def main():
    await asyncio.gather(client1.start(), client2.start(), client3.start())
    print("✅ Original Stable Bot Started!")
    await asyncio.gather(client1.run_until_disconnected(), client2.run_until_disconnected(), client3.run_until_disconnected())

asyncio.run(main())
          
