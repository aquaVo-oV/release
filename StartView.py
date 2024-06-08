import typing
import discord
from discord.utils import MISSING

from DiscordUIRedefine import Button

class RoleNumberModal(discord.ui.Modal):
    def __init__(self, submit_process: typing.Coroutine) -> None:
        super().__init__(title= "配役を変更", timeout= None, custom_id= "role_number_modal")

        self.submit_process = submit_process
        
        self.role_name = discord.ui.TextInput(
            label= "役職",
            style= discord.TextStyle.short,
            placeholder= "役職名を入力"
        )
        self.role_number = discord.ui.TextInput(
            label= "人数",
            style= discord.TextStyle.short,
            placeholder= "人数を入力"
        )
        self.add_item(self.role_name)
        self.add_item(self.role_number)
        
    async def on_submit(self, ctx: discord.Interaction) -> typing.Coroutine:
        if self.role_number.value.isdecimal():
            await self.submit_process(ctx, self.role_name.value, self.role_number.value)
        else :
            # 数値以外がrolenumberにあるとき、再送信する
            await ctx.response.send_message(
                '人数には数字を入力してください',
                ephemeral= True,
                allowed_mentions= False,
                silent= True
                )
        return await super().on_submit(ctx)

class StartView(discord.ui.View):
    def __init__(
            self,
            __start_button_pressed: typing.Coroutine,
            __add_button_pressed: typing.Coroutine,
            __cancel_button_pressed: typing.Coroutine,
            *,
            timeout: float = None,
            ):
        super().__init__(timeout= timeout)

        
        self.start_button = Button(
            callback_process= __start_button_pressed,
            style= discord.ButtonStyle.success,
            label= "スタート"
        )
        self.add_button = Button(
            callback_process= __add_button_pressed,
            style= discord.ButtonStyle.primary,
            label= "配役を変更"
        )
        self.cancel_button = Button(
            callback_process= __cancel_button_pressed,
            style= discord.ButtonStyle.secondary,
            label= "キャンセル"
        )

        self.add_item(self.start_button)
        self.add_item(self.add_button)
        self.add_item(self.cancel_button)