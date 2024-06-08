import discord

class GameManager():
    def __init__(
            self,
            client: discord.Client,
            tree: discord.app_commands.CommandTree
            ) -> None:
        
        self.client = client
        self.tree = tree

        self.__guildId_to_atendeeIds: dict[int, set[int]] = {}
        self.__guildId_to_atendeeRole: dict[int, discord.Role] = {}
        self.__guildId_to_talkChannel: dict[int, discord.TextChannel] = {}

        self.__atendeeId_to_sysChannelId: dict[int, int] = {}

    async def start(self, ctx: discord.Interaction, atendeeIds: set[int]):
        self.__guildId_to_atendeeIds[ctx.guild_id] = atendeeIds
        await self.__create_discord_roles(ctx.guild)
        await self.__add_discord_roles(ctx.guild)
        await self.__create_talk_channel(ctx.guild)
        await self.__create_system_channel(ctx.guild)
        
    async def __create_discord_roles(self, guild: discord.Guild):
        # 参加者ロールのパーミッション設定
        participant_perm = discord.Permissions.none()
        
        # 参加者ロールを作成
        role = await guild.create_role(name= "参加者", permissions= participant_perm, color= 0x1f1e33)
        self.__guildId_to_atendeeRole[guild.id] = role

    async def __add_discord_roles(self, guild: discord.Guild):
        role = self.__guildId_to_atendeeRole[guild.id]
        # 参加者にロールを付与
        for atendee in self.__guildId_to_atendeeIds[guild.id]:
            await guild.get_member(atendee).add_roles(role)

    async def __create_talk_channel(self, guild: discord.Guild):

        atendeeIds = self.__guildId_to_atendeeIds[guild.id]
        atendee_role = self.__guildId_to_atendeeRole[guild.id]

        # TalkChannelでは参加者はスレッドでのみ話せる
        view_and_thread_only = discord.PermissionOverwrite()
        view_and_thread_only.read_messages = True
        view_and_thread_only.send_messages_in_threads = True
        
        talk_channel_overwrite = { 
            atendee_role: view_and_thread_only
            }
        
        # TalkChannelの作成
        talk_channel = await guild.create_text_channel(
            name = "TalkChannel",
            overwrites= talk_channel_overwrite
            )
        self.__guildId_to_talkChannel[guild.id] = talk_channel
        thread = await talk_channel.create_thread(
            name= "Public",
            type= discord.ChannelType.public_thread
        )
        for pid in atendeeIds:
            await thread.add_user(guild.get_member(pid))

    async def __create_system_channel(self, guild: discord.Guild):

        # 権限設定
        view_and_send = discord.PermissionOverwrite()
        view_and_send.read_messages = True
        view_and_send.read_message_history = True
        view_and_send.send_messages = True

        # system_channelの作成
        for pid in self.__guildId_to_atendeeIds[guild.id]:
            participant = guild.get_member(pid)
            dm_request_overwrite = {
                participant: view_and_send
            }
            system_channel = await guild.create_text_channel(
                name= "DMRequest",
                overwrites= dm_request_overwrite
                )
            self.__atendeeId_to_sysChannelId[pid] = system_channel.id
