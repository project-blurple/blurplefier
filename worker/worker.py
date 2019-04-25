# -*- coding: utf-8 -*-

import asyncio
import json
import logging
import signal

import aiohttp
import aioredis
import discord.http

from .magic import convert_image


log = logging.getLogger(__name__)


class Worker:
    def __init__(self, config):
        self.config = config

        self.redis = None
        self.loop = asyncio.get_event_loop()

        self.http = None


    @classmethod
    def with_config(cls, path='config.json'):
        """Create a bot instance with a Config."""

        with open(path) as f:
            data = json.load(f)

        return cls(data)

    def run(self):
        loop = self.loop

        loop.create_task(self.run_jobs())

        try:
            loop.add_signal_handler(signal.SIGINT, lambda x: loop.close)
            loop.add_signal_handler(signal.SIGTERM, lambda x: loop.close)
        except RuntimeError:  # Windows
            pass

        try:
            loop.run_forever()
        except KeyboardInterrupt:
            loop.close()

    async def run_jobs(self):
        self.redis = await aioredis.create_redis(self.config['redis'])

        # We're using discord.py's HTTP class for rate limit handling
        # This is not intended to be used so there's no pretty way of creating it
        self.http = http = discord.http.HTTPClient()
        http._token(self.config['token'])
        http._HTTPClient__session = aiohttp.ClientSession()

        while self.loop.is_running():
            _, data = await self.redis.blpop('blurple:queue')

            job = json.loads(data)
            log.info(f'Running job {job}.')

            try:
                await self.run_job(job)
            except Exception:
                log.exception(f'Failed to run job: {job}.')

    async def run_job(self, data):
        user_id = data['requester']
        channel_id = data['channel']
        message_id = data['message']

        try:
            image = await self.http.get_from_cdn(data['url'])
        except discord.HTTPException:
            await self._send_error(f'I failed to download your image, please try again <@!{user_id}>!', channel_id)
            return

        if len(image) >= 8388608:
            await self._send_error(
                f'Your image is above 8MiB large, please use smaller images <@!{user_id}>!', channel_id
            )
            return

        try:
            result = convert_image(image, data['modifier'])
        except Exception:
            await self._send_error(f'I failed to convert your image <@!{user_id}>.', channel_id)
            return

        try:
            msg = f'Here is your image <@!{user_id}>!'
            await self.http.send_files(channel_id, content=msg, files=(result,))
            await self.http.remove_own_reaction(message_id, channel_id, '\N{FLOPPY DISK}')
        except discord.HTTPException:
            await self._send_error(
                f'I couldn\'t upload your image to Discord, it may be too big <@!{user_id}>!', channel_id
            )

    async def _send_error(self, message, channel_id):
        try:
            await self.http.send_message(channel_id, message)
        except discord.HTTPException:
            pass
