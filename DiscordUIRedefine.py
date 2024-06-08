import discord

import typing

from discord.utils import MISSING

class Button(discord.ui.Button):
    def __init__(
            self, 
            callback_process: typing.Coroutine,
            *, 
            style: discord.ButtonStyle = discord.ButtonStyle.primary,
            disabled= False,
            label: str = None,
            row: int = None,
            custom_id: str = None,
            ):
        
        super().__init__(
            style= style,
            disabled= disabled,
            label=label,
            custom_id=custom_id,
            row= row
            )
        
        self.callback_process = callback_process

    async def callback(self, ctx: discord.Interaction):
        await self.callback_process(ctx)
        return await super().callback(ctx)

class ChannelSelect(discord.ui.ChannelSelect):
    async def callback(self, ctx: discord.Interaction):
        await ctx.response.defer(ephemeral= True, thinking= False)
        return await super().callback(ctx)
