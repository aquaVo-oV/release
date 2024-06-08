import discord
from discord.utils import MISSING
import typing

from DiscordUIRedefine import Button

class UserSelect(discord.ui.UserSelect):
    def __init__(
            self,
            callback_process: typing.Coroutine,
            *,
            custom_id: str = ...,
            row: int = None
            ) -> None:
        super().__init__(
            custom_id=custom_id,
            placeholder= None,
            min_values= 1,
            max_values= 1,
            disabled= False,
            row= row
            )
        self.callback_process = callback_process

    async def callback(self, ctx: discord.Interaction):
        self.callback_process(ctx, self.values[0])
        return await super().callback(ctx)
    
class DMChannelCreatorView(discord.ui.View):
    def __init__(
            self,
            select_checker: typing.Coroutine,
            create_process: typing.Coroutine,
            *,
            timeout: float = None
            ):
        super().__init__(timeout=timeout)

        self.selector = UserSelect(select_checker)
        self.submit_button = Button(create_process)

        self.add_item(self.selector)
        self.add_item(self.submit_button)