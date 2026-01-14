from pyrogram import Client, raw
from pyrogram.raw.functions.contacts import ResolvePhone, ResolveUsername
from pyrogram import enums
from pyrogram.raw import types
from typing import Optional, Annotated
from fastapi import FastAPI, Query, HTTPException
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import uvicorn
import re
import os

load_dotenv()

api_id = int(os.getenv("TELEGRAM_API_ID"))
api_hash = os.getenv("TELEGRAM_API_HASH")
session_name = os.getenv("TELEGRAM_SESSION_NAME")
app = FastAPI()


def parse_text(text: str) -> str:
    text = text.replace('\\n', '\n')
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    text = text.strip()
    return text


def parse_html(html: str):
    soup = BeautifulSoup(html, "html.parser")
    text, entities = "", []

    def walk(node):
        nonlocal text
        if isinstance(node, str):
            text += node
            return
        if node.name == "a" and node.get("href"):
            start = len(text)
            t = node.get_text()
            text += t
            entities.append(types.MessageEntityTextUrl(offset=start, length=len(t), url=node["href"]))
        else:
            for c in node.children:
                walk(c)

    for c in (soup.body or soup).children:
        walk(c)

    return text, entities


def contains_only_digits(contact: str):
    contact = contact.replace('-', '').replace('+', '').replace('@', '').replace('_', '').replace(' ', '')
    return contact.isdigit()


async def resolve_username(username: str):
    pyro = Client(
        api_id=api_id,
        api_hash=api_hash,
        name=session_name)

    user_id = None
    async with pyro:
        r = await pyro.invoke(ResolveUsername(username=username))
        if r.users:
            user_id = r.users[0].id
    del pyro
    return user_id


async def resolve_phone(phone: str):
    pyro = Client(
        api_id=api_id,
        api_hash=api_hash,
        name=session_name)

    user_id = None
    async with pyro:
        r = await pyro.invoke(ResolvePhone(phone=phone))
        if r.users:
            user_id = r.users[0].id
    del pyro
    return user_id


async def resolve_contact(contact: str):
    contact = contact.replace('@', '')
    user_id = None
    try:
        if contains_only_digits(contact):
            user_id = await resolve_phone(contact)

        if user_id is None:
            user_id = await resolve_username(contact)

        return {'user_id': user_id}

    except:
        return {'user_id': None}


@app.post('/send_message')
async def send_message(
    date: str,
    contact: str,                       # может быть id, @username, телефон
    client_name: Optional[str] = None
):
    pyro = Client(api_id=api_id, api_hash=api_hash, name=session_name)

    msg = (
        f'{client_name+", добрый день 🙂" if client_name else "Добрый день 🙂"}\n\n'
        f'Напоминаю, что у вас назначена сессия на {date}.\n\n'
        'Подтвердите, пожалуйста,  сессию в  чат-боте @HraniLiveBot. '
        'Для этого нажмите кнопку “Спасибо, я приду” ✅\n\n'
        'Если подтверждение не придёт, то сессия отменится автоматически.\n'
        'Если у вас поменялись планы и нужно перенести сессию, напишите мне. '
        'Подберу для вас новое время 🙏🏻'
    )

    async with pyro:
        try:
            chat_id = int(contact)
        except ValueError:
            user = await resolve_contact(contact)
            if not user or "user_id" not in user:
                raise HTTPException(status_code=404, detail=f"User not found for contact: '{contact}'")
            chat_id = user["user_id"]

        await pyro.send_message(chat_id, msg)

    del pyro
    return {'ok': 'ok'}


@app.post('/send_custom_message')
async def send_custom_message(
    contact: Annotated[str, Query()],   # может быть id, @username, телефон
    message: Annotated[str, Query()]
):
    pyro = Client(api_id=api_id, api_hash=api_hash, name=session_name)

    async with pyro:
        try:
            user_id = int(contact)
            chat_id = user_id
        except ValueError:
            user = await resolve_contact(contact)
            if not user or "user_id" not in user:
                raise HTTPException(status_code=404, detail=f"User not found for contact: '{contact}'")
            chat_id = user["user_id"]

        await pyro.send_message(chat_id, message)

    del pyro
    return {'ok': 'ok'}


@app.post('/send_to_group')
async def send_to_group(
    group_id: Annotated[str, Query()],
    text: Annotated[str, Query()],
    thread_id: Annotated[Optional[int], Query()] = None
):
    def norm_id(g): return int(g) if g.lstrip('-').isdigit() else g

    async def send_with_variants(fn, cid):
        last = None
        for v in (cid, str(cid), int(cid) if isinstance(cid, str) and cid.lstrip('-').isdigit() else None):
            if v is None:
                continue
            try:
                await fn(v)
                return
            except Exception as e:
                last = e
        raise Exception(last or "send failed")

    chat_id = norm_id(group_id)
    processed = parse_text(text)
    pyro = Client(api_id=api_id, api_hash=api_hash, name=session_name)

    try:
        async with pyro:
            try:
                try:
                    await pyro.get_chat(chat_id)
                except:
                    async for d in pyro.get_dialogs():
                        if str(d.chat.id) == str(chat_id) or d.chat.id == chat_id:
                            break
            except:
                pass

            if thread_id is not None:
                msg_text, entities = parse_html(processed)

                async def send_thread(cid):
                    p = await pyro.resolve_peer(cid)
                    await pyro.invoke(
                        raw.functions.messages.SendMessage(
                            peer=p,
                            message=msg_text,
                            entities=entities or None,
                            random_id=pyro.rnd_id(),
                            reply_to_msg_id=thread_id,
                            top_msg_id=thread_id,
                        )
                    )

                await send_with_variants(send_thread, chat_id)
            else:
                async def send_plain(cid):
                    await pyro.send_message(cid, processed, parse_mode=enums.ParseMode.HTML)

                await send_with_variants(send_plain, chat_id)

        del pyro
        return {"ok": "ok"}

    except HTTPException:
        raise
    except Exception as e:
        del pyro
        msg = str(e)
        if any(x in msg for x in ("Peer id invalid", "PEER_ID_INVALID", "CHAT_NOT_FOUND")):
            raise HTTPException(
                status_code=404,
                detail=f"Group not found or access denied. Group ID: '{group_id}'. Error: {msg}. "
                       f"Make sure the client is added to the group and has permission to send messages.",
            )
        raise HTTPException(status_code=500, detail=f"Failed to send message: {msg}")


uvicorn.run(app, host='0.0.0.0', port=8080)