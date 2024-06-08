import discord

import typing

from DiscordUIRedefine import Button

async def delete_original_response(ctx : discord.Interaction):
    await ctx.response.defer(ephemeral= True, thinking= False)
    await ctx.delete_original_response()

class YNView(discord.ui.View):
    def __init__(
            self,
            __yes_pressed: typing.Coroutine,
            __no_pressed: typing.Coroutine = delete_original_response,
            yes_label: str = "はい",
            no_label: str = "いいえ",
            *,
            timeout: float = None,
            ):
        super().__init__(timeout= timeout)

        self.attend_button = Button(
            callback_process= __yes_pressed,
            style= discord.ButtonStyle.success,
            label= yes_label
        )
        self.cancel_button = Button(
            callback_process= __no_pressed,
            style= discord.ButtonStyle.secondary,
            label= no_label
        )

        self.add_item(self.attend_button)
        self.add_item(self.cancel_button)

class RecruitView(YNView):
    def __init__(
            self,
            __attend_button_pressed: typing.Coroutine,
            __cancel_button_pressed: typing.Coroutine,
            *,
            timeout: float = None
            ):
        super().__init__(
            __attend_button_pressed,
            __cancel_button_pressed,
            yes_label= "参加",
            no_label= "キャンセル",
            timeout=timeout
            )
    


