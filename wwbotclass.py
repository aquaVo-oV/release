import discord
import asyncio
import sys, traceback

from RecruitManager import RecruitManager
from rolemanager import roleManager
import utils

class wwbot():
    def __init__(
            self,
            client: discord.Client,
            tree: discord.app_commands.CommandTree,
            error_msg: str = "error_msg",
            normal_finish_msg: str = "normal_finish_msg"
            ) -> None:
        self.client = client
        self.tree = tree

        self.recruit_mng = RecruitManager(client, tree, start_process= lambda : None)
        self.role_mng = roleManager(client= client, tree= tree)
        
        self.__error_msg = error_msg
        self.__normal_finish_msg = normal_finish_msg

        self._dict_guildId_to_particiantsRoleId: dict[int, int] = {}
        self._dict_guildId_to_talkChannelId: dict[int, int] = {}
        self._dict_guildId_to_drcIds: dict[int, tuple[int, ...]] = {} 
        self._dict_guildId_to_dmCreatedPairs: dict[int, list[set[int]]] = {} 
        self._dict_drcId_to_pid: dict[int, int] = {} # dmRequestChannelId_to_participantId

        tree.command(description= "人狼ゲームの開始")(self.start)
        client.event(self.on_message)

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
