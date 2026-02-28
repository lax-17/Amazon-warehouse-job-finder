#!/usr/bin/env python3
"""Get your Telegram Chat ID."""

import requests

TOKEN = '8551550614:AAFchjPtAUjGScNnwaTx2JLIXhRLKEcfkAQ'
url = f'https://api.telegram.org/bot{TOKEN}/getUpdates'

print("="*60)
print("TELEGRAM CHAT ID FINDER")
print("="*60)
print("\nStep 1: Open Telegram on your phone")
print("Step 2: Search for your bot (the one you created)")
print("Step 3: Send any message to your bot (like 'Hi')")
print("Step 4: Run this script again\n")
print("="*60)

try:
    response = requests.get(url).json()
    
    if response.get('ok') and response.get('result'):
        print("\n✅ Found your Chat ID:\n")
        for update in response['result']:
            if 'message' in update:
                chat = update['message']['chat']
                print(f"CHAT_ID: {chat['id']}")
                print(f"Name: {chat.get('first_name', '')} {chat.get('last_name', '')}")
                print(f"Username: @{chat.get('username', 'N/A')}")
                print("\n" + "="*60)
                print(f"\n👉 Add this to config.env:")
                print(f"TELEGRAM_CHAT_ID={chat['id']}")
                print("="*60)
                break
    else:
        print("\n⚠️  No messages found.")
        print("   You need to send a message to your bot first!")
        
except Exception as e:
    print(f"Error: {e}")
