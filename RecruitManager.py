import discord
import utils
import typing

from MessageSendingSelectView import MessageSendingSelectView
from RecruitView import RecruitView, YNView
from StartView import StartView, RoleNumberModal



class RecruitManager():

    def __init__(
            self,
            client: discord.Client,
            tree: discord.app_commands.CommandTree,
            start_process: typing.Coroutine
            ) -> None:
        
        self.client = client
        self.tree = tree

        self.start_process = start_process
        
        self.__guildId_to_atendees: dict[int, set[int]] = {}
        self.__guildId_to_roleNumTable: dict[int, dict[str, int]] = {}
        self.__guildId_to_recruitMsg: dict[int, discord.Message] = {}
        self.__guildId_to_gmMsg: dict[int, discord.Message] = {}
    
        self.__interacting_guildId: set[int] = set()

        tree.command(description= "人狼ゲームの参加者の募集")(self.recruit)

    async def __with_interacting_check(self, ctx: discord.Interaction, process: typing.Coroutine):
        if ctx.guild_id not in self.__interacting_guildId:
            await process(ctx)
        else :
            await ctx.response.defer(ephemeral= True, thinking= False)

    async def __all_delete(self, guild_id: int):
        async def process():
            await self.__guildId_to_recruitMsg[guild_id].delete()
            await self.__guildId_to_gmMsg[guild_id].delete()
            self.__guildId_to_recruitMsg.pop(guild_id)
            self.__guildId_to_atendees.pop(guild_id)
            self.__guildId_to_gmMsg.pop(guild_id)
        await utils.try_except_no_responce(process)

    async def __attend_button_pressed(self, ctx: discord.Interaction):
        if not ctx.user.id in self.__guildId_to_atendees[ctx.guild_id]:
            # 参加者テーブルに追加
            self.__guildId_to_atendees[ctx.guild_id].add(ctx.user.id)
            # 応答はdefer
            await ctx.response.defer(ephemeral= True, thinking= False)
            # Embedを編集して送る
            embed = ctx.message.embeds[0]
            embed.add_field(name= ctx.user.display_name, value= ctx.user.mention)
            await ctx.message.edit(embed= embed)
        else :
            await ctx.response.send_message(
                content= "すでに参加しています",
                ephemeral= True,
                allowed_mentions= False,
                silent= True,
                delete_after= 3
                )
    
    async def __recruit_cancel_button_pressed(self, ctx: discord.Interaction):
        if ctx.user.id in self.__guildId_to_atendees[ctx.guild_id]:
            # 参加者テーブルから削除
            self.__guildId_to_atendees[ctx.guild_id].remove(ctx.user.id)
            # 応答はdefer
            await ctx.response.defer(ephemeral= True, thinking= False)
            # Embedを編集して送る
            embed = ctx.message.embeds[0]
            embed.clear_fields()
            for mid in self.__guildId_to_atendees[ctx.guild_id]:(
                embed.add_field(
                    name= ctx.guild.get_member(mid).display_name,
                    value= ctx.guild.get_member(mid).mention
                )
            )
            await ctx.message.edit(embed= embed)
        else :
            await ctx.response.send_message(
                content= "まだ参加していません",
                ephemeral= True,
                allowed_mentions= False,
                silent= True,
                delete_after= 3
                )

    async def __start_button_pressed(self, ctx: discord.Interaction):
        async def process():
            async def process_core():
                atendeeTable = self.__guildId_to_atendees[ctx.guild_id]
                await self.__all_delete(ctx.guild_id)
                await self.start_process(ctx, atendeeTable)
            await utils.try_except_to_discord_defer(ctx, process_core)

        # 仮想modalが出ているときは無視する
        await self.__with_interacting_check(ctx, process)
        
    async def __add_button_pressed(self, ctx: discord.Interaction):
        # submitした時の処理
        async def submit_process(ctx_: discord.Interaction, role_name: str, role_number: str):
            # 1以上ならテーブルに追加そうでないならテーブルから削除
            if int(role_number) > 0:
                self.__guildId_to_roleNumTable[ctx.guild_id][role_name] = int(role_number)
            else :
                if role_name in self.__guildId_to_roleNumTable[ctx.guild_id]:
                    self.__guildId_to_roleNumTable[ctx.guild_id].pop(role_name)
            # 応答はdefer
            await ctx_.response.defer(ephemeral= True, thinking= False)
            # Embedを編集して送る
            resp = await ctx.original_response()
            embed = resp.embeds[0]
            embed.clear_fields()
            for (rn, num) in self.__guildId_to_roleNumTable[ctx.guild_id].items():(
                embed.add_field(name= rn, value= num, inline= True)
            )
            await ctx.edit_original_response(embed= embed)

        async def process(ctx_: discord.Interaction):
            # モーダルをレスポンス
            modal = RoleNumberModal(submit_process)
            await ctx_.response.send_modal(modal)

        # 無視機能付きで実行
        await self.__with_interacting_check(ctx, process)

    async def __start_cancel_button_pressed(self, ctx: discord.Interaction):
        
        # キャンセルプロセス
        async def yes_process(ctx_: discord.Interaction):
            async def process_core():
                await ctx.delete_original_response()
                await self.__all_delete(ctx.guild_id)

            await utils.try_except_to_discord(
                ctx_,
                process_core,
                normal_finish_msg= "キャンセルされました"
                )
            self.__interacting_guildId.remove(ctx.guild_id)
        
        # いいえ選択時
        async def no_process(ctx_: discord.Interaction):
            async def process():
                await ctx_.response.defer(ephemeral= True, thinking= False)
                await ctx_.delete_original_response()
            await utils.try_except_no_responce(process)
            self.__interacting_guildId.remove(ctx.guild_id)
        
        # この関数の本体
        async def process(ctx_: discord.Interaction):
            # 元messageの入力を無視する
            self.__interacting_guildId.add(ctx_.guild_id)
            # 実行するかの質問view
            ynview = YNView(yes_process, no_process)
            await ctx.response.send_message(
                content= "本当にキャンセルしますか？",
                view= ynview,
                ephemeral= True,
                silent= True
            )
        
        # 無視機能付きで実行
        await self.__with_interacting_check(ctx, process)


    @discord.app_commands.guilds(366876869590515712)
    async def recruit(self, ctx: discord.Interaction):

        self.__guildId_to_atendees[ctx.guild_id] = set()
        self.__guildId_to_roleNumTable[ctx.guild_id] = {}
        
        recruit_embed = discord.Embed(title= "参加者一覧")
        recruit_view = RecruitView(
            self.__attend_button_pressed,
            self.__recruit_cancel_button_pressed
        )

        start_embed = discord.Embed(title= "配役")
        start_view = StartView(
                self.__start_button_pressed,
                self.__add_button_pressed,
                self.__start_cancel_button_pressed
            )

        select_view = MessageSendingSelectView(
                guildId_to_msg= self.__guildId_to_recruitMsg,
                embed= recruit_embed,
                view= recruit_view,
                allowed_mentions= False,
                silent= True
            )
        
        # 参加プレイヤーの募集メッセージの送信
        async def process():
            await ctx.response.send_message(
                embed= start_embed,
                view= start_view,
                ephemeral= True,
                silent= True
            )
            gm_msg = await ctx.original_response()
            self.__guildId_to_gmMsg[ctx.guild_id] = gm_msg

            await ctx.followup.send(
                content= "参加者募集メッセージの送信先を選択してください",
                view = select_view,
                ephemeral= True,
                silent= True
                )
            
        await utils.try_except_no_responce(process= process)

        