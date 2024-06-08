import typing, asyncio
import sys, traceback

import discord

default_delete_after = 3

# 処理に対してtryexceptをかけて結果をdiscordにdeferで返答
async def try_except_to_discord_defer(
        ctx: discord.Interaction,
        process: typing.Coroutine,
        normal_finish_msg: str = "正常に終了しました",
        error_msg: str = "エラーが発生しました",
        delete_after: float = default_delete_after,
        ):
    await ctx.response.defer(ephemeral= True)
    try :
        await process()
        whmsg: discord.WebhookMessage  = await ctx.followup.send(
                normal_finish_msg,
                ephemeral= True,
                allowed_mentions= False,
                wait= True
                )
        if delete_after is not None:
            await asyncio.sleep(delete_after)
            await whmsg.delete()

    except :
        exc_info = sys.exc_info()
        print(traceback.format_exception(*exc_info))
        whmsg: discord.WebhookMessage  = await ctx.followup.send(
                error_msg,
                ephemeral= True,
                allowed_mentions= False,
                wait= True
                )
        if delete_after is not None:
            await asyncio.sleep(delete_after)
            await whmsg.delete()

# 処理に対してtryexceptをかけて結果をdiscordにresponse
async def try_except_to_discord(
        ctx: discord.Interaction,
        process: typing.Coroutine,
        normal_finish_msg: str = "正常に終了しました",
        error_msg: str = "エラーが発生しました",
        delete_after: float = default_delete_after
        ):
    
    try :
        await process()
        await ctx.response.send_message(
            normal_finish_msg,
            ephemeral= True,
            allowed_mentions= False,
            silent= True,
            delete_after= delete_after,
            )
    except :
        exc_info = sys.exc_info()
        print(traceback.format_exception(*exc_info))
        await ctx.response.send_message(
            error_msg, 
            ephemeral= True,
            allowed_mentions= False,
            silent= True,
            delete_after= delete_after,
            )

# 処理に対してtryexceptをかけて結果をdiscordにresponse
async def try_except_no_responce(
        process: typing.Coroutine,
        ):
    
    try :
        await process()
    except :
        exc_info = sys.exc_info()
        print(traceback.format_exception(*exc_info))