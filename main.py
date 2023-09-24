import os
from dotenv import load_dotenv

from fastapi import FastAPI, Header, Request, HTTPException

from linebot.v3 import (
    WebhookHandler
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
    PostbackAction,
    ButtonsTemplate,
    TemplateMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent
)

import openai

load_dotenv()

configuration = Configuration(access_token=os.environ['CHANNEL_ACCESS_TOKEN'])
handler = WebhookHandler(os.environ['CHANNEL_SECRET'])

app = FastAPI()

@app.get("/")
def index():
  return 'OK'

@app.post("/callback")
async def callback(request: Request, x_line_signature=Header(None)):
    body = await request.body()
    try:
        handler.handle(body.decode('utf-8'), x_line_signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="InvalidSignatureError")
    return 'OK'

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    if event.message.text == "QA":
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            buttons_template_message = TemplateMessage(
                alt_text='QA',
                template=ButtonsTemplate(
                    title='QA',
                    text='質問したい内容を入力してください',
                    actions=[
                        PostbackAction(
                            data='test',
                            label='メッセージを送信',
                            input_option='openKeyboard'
                        )
                    ]
                )
            )    
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[buttons_template_message]
                )
            )
    else:
        with ApiClient(configuration) as api_client:
            openai.api_key = os.environ['OPENAI_API_KEY']
            completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": event.message.text}])
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=completion.choices[0].message.content)]
                )
            )
