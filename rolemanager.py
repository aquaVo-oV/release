import os, sys, traceback
import discord
import typing
import random

# 処理に対してtryexceptをかけて結果をdiscordに
async def try_except_to_discord(
        ctx: discord.Interaction,
        process: typing.Coroutine,
        normal_finish_msg: str = "normal_finish_msg",
        error_msg: str = "error_msg"
        ):
    
    try :
        await process()
        await ctx.response.send_message(
            normal_finish_msg,
            ephemeral= True,
            allowed_mentions= False,
            silent= True,
            delete_after= 3,
            )
    except :
        exc_info = sys.exc_info()
        print(traceback.format_exception(*exc_info))
        await ctx.response.send_message(
            error_msg, 
            ephemeral= True,
            allowed_mentions= False,
            silent= True,
            delete_after= 3,
            )

class roleManager():
    def __init__(
            self,
            client: discord.Client,
            tree: discord.app_commands.CommandTree,
            normal_finish_msg: str = "normal_finish_msg",
            error_msg: str = "error_msg",
            cast_title: str = "",
            ) -> None:
        
        self.client = client
        self.tree = tree

        self.__normal_finish_msg = normal_finish_msg
        self.__error_msg = error_msg
        self.cast_title = cast_title

        self._casting_msg_fmt = "あなたは{}です。"

        self.cast_return_fmt = "{} : {}"

        self._dict_guildId_to_castNums: dict[int, dict[str, int]] = {}
        self._dict_guildId_to_castingDict: dict[int, dict[int, str]] = {}
        self._dict_guildId_to_roleChannelIds: dict[int, tuple[int, ...]] = {}
        self._dict_rcid_to_pid: dict[int, int] = {} #roleChannelId_to_participantId

        self._dict_guildId_to_castingMsg_CidMid : dict[int, tuple[int, int]] = {}
        
        tree.command(description= "役職の人数の設定")(self.set_cast_num)
        tree.command(description= "配役の人数の表示")(self.get_cast_msg)

    def __construct_casting_emb(self, guild_id: int) -> discord.Embed:
        msg = os.linesep.join(
                self.cast_return_fmt.format(role_name, number)
                for (role_name, number) in self._dict_guildId_to_castNums[guild_id].items()
                )
        return discord.Embed(
            title= self.cast_title,
            description= msg
            )
        
    @discord.app_commands.guilds(366876869590515712)
    async def set_cast_num(self, ctx: discord.Interaction, rolename: str, number: int):
        async def process():
            # ギルドに配役が設定されてないなら空のものを設定する
            if ctx.guild_id not in self._dict_guildId_to_castNums:
                self._dict_guildId_to_castNums[ctx.guild_id] = {}
            # 数が0以上ならnumberを設定、0なら配役を消去、負の場合はエラー
            if number > 0:
                self._dict_guildId_to_castNums[ctx.guild_id][rolename] = number
            elif number == 0:
                self._dict_guildId_to_castNums[ctx.guild_id].pop(rolename, 0)
            else:
                raise Exception('The argument "number" must not be negative.')
            
            if ctx.guild_id in self._dict_guildId_to_castingMsg_CidMid:
                cid, mid= self._dict_guildId_to_castingMsg_CidMid[ctx.guild_id]
                emb = self.__construct_casting_emb(ctx.guild_id)
                self.client.get_guild(ctx.guild_id).get_channel(cid).get_partial_message(mid).edit(embed= emb)

        await try_except_to_discord(
            ctx= ctx,
            process= process,
            normal_finish_msg= self.__normal_finish_msg
            )
        
    @discord.app_commands.guilds(366876869590515712)
    async def get_cast_msg(self, ctx: discord.Interaction, channel_id: str = None):

        # 送信関数のコア
        async def send_cast_msg(channel_id: int):
            # ギルドに配役が設定されてないなら空のものを設定する
            if ctx.guild_id not in self._dict_guildId_to_castNums:
                self._dict_guildId_to_castNums[ctx.guild_id] = {}
            # メッセージを構築して送信
            embed = self.__construct_casting_emb(guild_id= ctx.guild_id)
            casting_msg = await self.client.get_channel(channel_id).send(embed= embed)
            self._dict_guildId_to_castingMsg_CidMid = (channel_id, casting_msg.id)

        # 送信プロセス    
        async def process():
            if channel_id is None:
                await send_cast_msg(ctx.channel.id)
            else :
                await send_cast_msg(int(channel_id))

        # 例外処理込みでprocを実行
        await try_except_to_discord(
            ctx= ctx,
            process= process,
            normal_finish_msg= self.__normal_finish_msg,
            error_msg= self.__error_msg
            )
        
    def check_number(self, guild_id: int, part_num: int) -> bool:
        # 役職の数がpart_numと等しいか判定
        all_cast_number = sum(cn for cn in self._dict_guildId_to_castNums[guild_id].values())
        return all_cast_number == part_num
    
    def casting(self, guild_id: int, participantIds: typing.Sequence[int]):
        # 参加者の人数と役職の数が等しいなら、それぞれの参加者に対し、役職を割り振る
        all_cast_number = sum(cn for cn in self._dict_guildId_to_castNums[guild_id].values())
        if all_cast_number == len(participantIds):
            # 役職一覧を展開してシャッフル
            rolenames = random.sample(
                tuple(
                    name
                    for (name, num) in self._dict_guildId_to_castNums[guild_id].items()
                    for _ in range(num)
                    ),
                k= all_cast_number
                )
            # participantId_to_rolenameの形でcastingを決定
            self._dict_guildId_to_castingDict[guild_id] = { 
                pid: rn 
                for (rn, pid) in zip(rolenames, participantIds)
            }
        else :
            raise Exception("Unknown Error")
        
    async def create_role_channel(self, guild_id: int):
        guild = self.client.get_guild(guild_id)
        # 権限設定
        view_and_send = discord.PermissionOverwrite()
        view_and_send.read_messages = True
        view_and_send.read_message_history = True
        view_and_send.send_messages = True
        # personal_role_channelの作成(プレイヤーが役職の効果を使うとき用のチャンネル)
        # キャスティングからイテレータを回す
        personal_role_channels = ()
        for (pid , role_name) in self._dict_guildId_to_castingDict[guild_id].items():
            participant = guild.get_member(pid)
            overwrite = {
                participant: view_and_send
            }
            personal_role_channel = await guild.create_text_channel(
                name= role_name,
                overwrites= overwrite
                )
            personal_role_channels += (personal_role_channel.id,)
            self._dict_rcid_to_pid[personal_role_channel.id] = pid
        self._dict_guildId_to_roleChannelIds[guild_id] = personal_role_channels

    async def send_casting_role_massage(self, guild_id: str):
        # 割り振った役職についてのメッセージを送る
        rcids = self._dict_guildId_to_roleChannelIds[guild_id]
        for rcid in rcids:
            await self.client.get_guild(guild_id).get_channel(rcid).send(
                self._casting_msg_fmt.format(
                    self._dict_guildId_to_castingDict[guild_id][self._dict_rcid_to_pid[rcid]]
                )
            )