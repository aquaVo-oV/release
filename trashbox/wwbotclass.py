import discord
import asyncio
import sys, traceback

from rolemanager import roleManager


class wwbot():
    def __init__(
            self,
            client: discord.Client,
            tree: discord.app_commands.CommandTree,
            recruit_msg: str = "recruit_msg",
            error_msg: str = "error_msg",
            normal_finish_msg: str = "normal_finish_msg"
            ) -> None:
        self.client = client
        self.tree = tree

        self.role_mng = roleManager(client= client, tree= tree)
        
        self.__recruit_msg = recruit_msg
        self.__error_msg = error_msg
        self.__normal_finish_msg = normal_finish_msg
        self.__participant_reaction = "\N{neutral face}"

        self._dict_guildId_to_msgId_channelId: dict[int, tuple[int, int]] = {}
        self._dict_guildId_to_participantsIds: dict[int, tuple[int, ...]] = {}
        self._dict_guildId_to_particiantsRoleId: dict[int, int] = {}
        self._dict_guildId_to_talkChannelId: dict[int, int] = {}
        self._dict_guildId_to_drcIds: dict[int, tuple[int, ...]] = {} 
        self._dict_guildId_to_dmCreatedPairs: dict[int, list[set[int]]] = {} 
        self._dict_drcId_to_pid: dict[int, int] = {} # dmRequestChannelId_to_participantId

        tree.command(description= "人狼ゲームの参加者の募集")(self.recruit)
        tree.command(description= "人狼ゲームの開始")(self.start)
        client.event(self.on_message)

    async def __get_participants(self, guild_id: int):
        (msg_id, channel_id) = self._dict_guildId_to_msgId_channelId.pop(guild_id)
        fetch_msg = await self.client.get_channel(channel_id).fetch_message(msg_id)

        # 参加者のidを取得
        usertpl = ()
        for reaction in fetch_msg.reactions:
            if str(reaction) == self.__participant_reaction:
                async for user in reaction.users():
                    if user.id != self.client.user.id:
                        usertpl += (user.id,)
        self._dict_guildId_to_participantsIds[guild_id] = usertpl
        if not self.role_mng.check_number(guild_id, len(usertpl)):
            raise Exception("cast number is no match")
        
        # msgの削除
        await fetch_msg.delete()

    async def __add_discord_roles(self, guild_id: int):

        # 参加者ロールのパーミッション設定
        guild = self.client.get_guild(guild_id)
        participant_perm = discord.Permissions.none()
        
        # 参加者ロールを作成
        role = await guild.create_role(name= "参加者", permissions= participant_perm, color= 0x1f1e33)
        self._dict_guildId_to_particiantsRoleId[guild_id] = role.id

        # 参加者にロールを付与
        for participantsId in self._dict_guildId_to_participantsIds[guild_id]:
            await guild.get_member(participantsId).add_roles(role)

    async def __delete_roles(self):
        for (gid, rid) in self._dict_guildId_to_particiantsRoleId.items():
            await self.client.get_guild(gid).get_role(rid).delete()
        
    async def __create_discord_channel(self, guild_id: int):
        guild = self.client.get_guild(guild_id)
        part_role = guild.get_role(self._dict_guildId_to_particiantsRoleId[guild_id])

        # TalkChannelでは参加者はスレッドでのみ話せる
        view_and_thread_only = discord.PermissionOverwrite()
        view_and_thread_only.read_messages = True
        view_and_thread_only.send_messages_in_threads = True
        
        talk_channel_overwrite = { 
            part_role: view_and_thread_only
            }

        # TalkChannelの作成
        talk_channel = await guild.create_text_channel(
            name = "TalkChannel",
            overwrites= talk_channel_overwrite
            )
        self._dict_guildId_to_talkChannelId[guild_id] = talk_channel.id
        thread = await talk_channel.create_thread(name= "Public", type= discord.ChannelType.public_thread)
        for pid in self._dict_guildId_to_participantsIds[guild_id]:
            thread.add_user(guild.get_member(pid))
        # 権限設定
        view_and_send = discord.PermissionOverwrite()
        view_and_send.read_messages = True
        view_and_send.read_message_history = True
        view_and_send.send_messages = True
        
        # dm_request_channelの作成
        dm_request_channels = ()
        for pid in self._dict_guildId_to_participantsIds[guild_id]:
            participant = guild.get_member(pid)
            dm_request_overwrite = {
                participant: view_and_send
            }
            dm_request_channel = await guild.create_text_channel(name= "DMRequest", overwrites= dm_request_overwrite)
            dm_request_channels += (dm_request_channel.id, )
            self._dict_drcId_to_pid[dm_request_channel.id] = pid

        self._dict_guildId_to_drcIds[guild_id] = dm_request_channels

    # dmchannelの作成
    async def __create_dmChannel(self, guild_id: int, pid1: int, pid2: int):

        # 二人のペアが作られてないなら作成する
        if {pid1, pid2} not in self._dict_guildId_to_dmCreatedPairs[guild_id]:
            # dmChannelの作成
            guild = self.client.get_guild(guild_id)
            talk_channel: discord.TextChannel = guild.get_channel(self._dict_guildId_to_talkChannelId[guild_id])
            p1 = guild.get_member(pid1).nick
            p2 = guild.get_member(pid2).nick
            thread = await talk_channel.create_thread(
                name= "{} to {}".format(p1, p2),
                type= discord.ChannelType.private_thread,
                invitable= False
            )
            await thread.add_user(p1)
            await thread.add_user(p2)
            self._dict_guildId_to_dmCreatedPairs[guild_id].append({pid1, pid2})

    @discord.app_commands.guilds(366876869590515712)
    async def recruit(self, interaction: discord.Interaction, channel_id: str = None):
        
        # 参加プレイヤーの募集メッセージの送信
        async def recruit_core(channel_id: int):
            msg = await self.client.get_channel(channel_id).send(self.__recruit_msg)
            await msg.add_reaction(self.__participant_reaction)
            self._dict_guildId_to_msgId_channelId[msg.channel.guild.id] = (msg.id, msg.channel.id)

        try :
            if channel_id == None:
                await recruit_core(interaction.channel.id)
            else :
                await recruit_core(int(channel_id))
            await interaction.response.send_message(
                self.__normal_finish_msg,
                ephemeral= True,
                allowed_mentions= False,
                silent= True,
                delete_after= 3,
                )
        except :
            await interaction.response.send_message(
                self.__error_msg, 
                ephemeral= True,
                allowed_mentions= False,
                silent= True,
                delete_after= 3,
                )
    
    @discord.app_commands.guilds(366876869590515712)
    async def start(self, interaction: discord.Interaction, guild_id_: str = None):

        # 人狼ゲームをスタートする関数
        async def start_core(guild_id: int):
            if guild_id in self._dict_guildId_to_msgId_channelId:
                # 参加者を取得
                await self.__get_participants(guild_id)
                # 人狼ロールのキャスティング
                self.role_mng.casting(guild_id, self._dict_guildId_to_participantsIds[guild_id])
                # ロール設定
                await self.__add_discord_roles(guild_id)
                # チャンネル設定
                await self.__create_discord_channel(guild_id)
                await self.role_mng.create_role_channel(guild_id)
                # 初期メッセージ送信
                await self.role_mng.send_casting_role_massage(guild_id)
            else:
                raise Exception("No Recruit Message Error")

        await interaction.response.defer(ephemeral= True)
        try :
            if guild_id_ == None:
                await start_core(interaction.guild.id)
            else :
                await start_core(int(guild_id_))
            whmsg: discord.WebhookMessage  = await interaction.followup.send(
                self.__normal_finish_msg,
                ephemeral= True,
                allowed_mentions= False,
                wait= True
                )
            await asyncio.sleep(3)
            await whmsg.delete()
        except :
            exc_info = sys.exc_info()
            print(traceback.format_exception(*exc_info))
            await interaction.followup.send(
                self.__error_msg,
                ephemeral= True,
                allowed_mentions= False,
                )

    # dm_Request_channel_manager
    async def on_message(self, msg: discord.Message):

        # ボットやDMメッセージは無視
        if msg.author.bot or msg.guild is None:
            return
        
        # drcが作られてないなら無視
        if self._dict_guildId_to_drcIds[msg.guild.id] is None:
            return
        
        # drcに送られてきたなら、dmchannelを作る
        # 相手が一人の時以外は無視
        if msg.channel.id in self._dict_guildId_to_drcIds[msg.guild.id]:
            if (
                len(msg.mentions) == 1 and 
                msg.mentions[0].id in self._dict_guildId_to_participantsIds[msg.guild.id]
                ): 
                await self.__create_dmChannel(
                    guild_id= msg.guild.id,
                    pid1= msg.author.id,
                    pid2= msg.mentions[0].id
                )

    
                

    
"""
    async def on_message(self, msg: discord.Message):

        # ボットには応答なし
        if msg.author.bot:
            return
        
        # /recruit [channel_id] の形式を読み取る
        # [channel_id]なしなら送られてきたメッセージのチャンネルで募集
        # argumentが多いならエラーを返す
        if msg.content.startswith("/recruit"):
            args = msg.content.split()
            if len(args) > 2:
                await msg.channel.send(self._too_many_arg_msg)
                return
            elif len(args) == 2:
                try :
                    await self.player_recruit(int(args[1]))
                except :
                    await msg.channel.send(self._error_msg)
            else :
                await self.player_recruit(msg.channel.id)

            return 

        if msg.content.startswith("/get_channel_id"):
            args = msg.content.split()
            if len(args) > 1:
                await msg.channel.send(self._too_many_arg_msg)
                return
            else :
                await msg.channel.send(str(msg.id))
                return
"""
