from telethon import TelegramClient
from telethon.tl.types import DocumentAttributeFilename
from telethon.tl.types import DocumentAttributeVideo


class Agent:
    def __init__(self):
        self.entity = 'Yt_dwnld'  # имя сессии - все равно какое
        self.api_id = 11372475
        self.api_hash = '48849e6cd0b959a6b18423f433488660'
        self.phone = '+79168017371'
        self.client = TelegramClient(self.entity, self.api_id, self.api_hash)

    async def start(self):
        await self.client.connect()
        if not await self.client.is_user_authorized():
            # при первом запуске - раскомментить, после авторизации для избежания FloodWait советую закомментить
            # await self.client.send_code_request(self.phone)
            await self.client.sign_in(self.phone, input('Enter code: '))
        self.client.start()

    async def forward_to_bot(self, *args):
        """bot_name, file_path, chat_id, duration, file_name, width, height"""
        msg = await self.client.send_file(
            args[0]['bot_name'],
            open(f'{args[0]["file_path"]}', "rb").read(),
            caption=f"{args[0]['chat_id']}:{args[0]['duration']}",
            file_name=args[0]['file_name'],
            use_cache=False,
            part_size_kb=1048576,
            attributes=[
                DocumentAttributeVideo(
                    args[0]['duration'],
                    args[0]['width'],
                    args[0]['height'],
                    supports_streaming=True),
                DocumentAttributeFilename(f"{args[0]['file_name']}.mp4")
            ]
        )
        print(msg)
        await self.client.disconnect()

