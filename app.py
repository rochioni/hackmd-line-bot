import os
import logging
from chalice import Chalice
from chalice import BadRequestError

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, ImageMessage, TextSendMessage
)

import hackmd_bot.hackmd_bot as hb
from dotenv import load_dotenv

load_dotenv()
app = Chalice(app_name='hackmd-line-bot')
logger = logging.getLogger()
line_bot_api = LineBotApi(os.environ.get('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.environ.get('LINE_CHANNEL_SECRET'))

# Messages on start and restart
line_bot_api.push_message(os.environ.get('LINE_USER_ID'), TextSendMessage(text='Chat BOT Startup'))

@app.route('/')
#@app.route('/<name>')
def index():
    return {'hello': 'world'}

# Listen for all Post Requests from /callback
@app.route("/callback", methods=['POST'])
def callback():
    request = app.current_request
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        raise BadRequestError('Invalid signature. Please check your channel access token/channel secret.')

    return 'OK'


@handler.add(MessageEvent, message=(TextMessage, ImageMessage))
def handle_message(event):
    if event.message.type=='image':
        # message_idから画像のバイナリデータを取得
        image = line_bot_api.get_message_content(event.message.id)
        path = f"static/{event.message.id}.jpg"
        hb.get_user_image(path, image)
        link = hb.upload_img_link(path)
        content = hb.add_temp_note(content = f"![]({link})")
        message = TextSendMessage(text=content)
        line_bot_api.reply_message(event.reply_token, message)

    if event.message.type=='text':
        word =  str(event.message.text)
        if word[:5] == "@todo":
            content = hb.update_todo_note(word[5:])
            message = TextSendMessage(text=content)
            line_bot_api.reply_message(event.reply_token, message)
        else: 
            content = hb.add_temp_note(word)
            message = TextSendMessage(text=content)
            line_bot_api.reply_message(event.reply_token, message)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)