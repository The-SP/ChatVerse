from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
import json

from .models import Chat
from django.contrib.auth.models import User

class ChatRoomConsumer(AsyncWebsocketConsumer):
    # 'connect' method is called when a client connects to the WebSocket
    async def connect(self):
        # extract 'pk' parameter from the URL route, this identifies the chat room being accessed
        self.pk = self.scope["url_route"]["kwargs"]["pk"]
        # create unique name for the chat room
        self.room_group_name = "chat_%s" % self.pk

        # 'group_add' adds the client's channel to the chat room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        # 'self.channel_name' is a unique identifier for the WebSocket channel that the consumer is connected to. Think of it as the phone number for your WebSocket connection - just as you can call someone on their phone number, you can send messages to a WebSocket channel using its channel name.

        # Accept the WebSocket connection (must accept before sending message i.e 'group_send')
        await self.accept()

    # 'disconnect' method is called when the WebSocket connection is closed.
    async def disconnect(self, close_code):
        # `group_discard` remove the client's channel from the chat room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        username = text_data_json['username']
        roomID = text_data_json['roomID']

        # Save the message to DB
        await self.save_message(username, roomID, message)

        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "chatroom_message", "message": message, "username": username},
        )

    # This is the chatroom_message method, which is called when the group_send method is invoked. It receives an event parameter that contains the message being sent to the group. It extracts the message from the event, converts it to JSON, and sends it to the client's channel using the send method.
    async def chatroom_message(self, event):
        message = event["message"]
        username = event["username"]

        await self.send(
            text_data=json.dumps({"message": message, "username": username})
        )

    @sync_to_async
    def save_message(self, username, roomID, message):
        user = User.objects.get(username=username)
        Chat.objects.create(
            user=user,
            room_id=roomID,
            message=message
        )