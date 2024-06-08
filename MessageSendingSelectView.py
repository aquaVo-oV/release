import typing
import discord

from DiscordUIRedefine import Button, ChannelSelect


class MessageSendingSelectView(discord.ui.View):
    def __init__(
            self,
            guildId_to_msg: dict[int, discord.Message],
            content: str = None,
            embed: discord.Embed = None,
            view: discord.ui.View = None,
            reactions: discord.Reaction = (),
            allowed_mentions: discord.AllowedMentions = None,
            silent: bool = True,
            timeout: float = None,
            ):
        super().__init__(timeout=timeout)

        self.guildId_to_msg = guildId_to_msg

        self.content = content
        self.embed = embed
        self.view = view
        self.reactions = reactions
        self.allowed_mentions = allowed_mentions
        self.silent = silent

        self.select = ChannelSelect(custom_id= "MsgSendSelector")
        self.button = Button(
            callback_process= self.__button_pressed,
            label= "送信",
            custom_id= "MessageSendButton"
            )
        
        self.add_item(self.select)
        self.add_item(self.button)

    async def __button_pressed(self, ctx: discord.Interaction):

        await ctx.response.defer(ephemeral= True, thinking= False)
        
        try :
            await ctx.delete_original_response()
        except (discord.HTTPException, discord.NotFound):
            pass

        msg = await ctx.guild.get_channel(self.select.values[0].id).send(
            content= self.content,
            embed= self.embed,
            view= self.view,
            allowed_mentions= self.allowed_mentions,
            silent= self.silent
        )
        for r in self.reactions:
            await msg.add_reaction(r)
            
        self.guildId_to_msg[msg.guild.id] = msg
        
        
        
        
        