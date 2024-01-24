# -*- coding: utf-8 -*-
import asyncio
import signal
import subprocess

from hagworm.extend.asyncio.base import install_uvloop, Utils
from hagworm.extend.asyncio.future import SubProcess

from base.agent_public.agent_log import logger

from setting import BaseConfig


class MainProcess:

    def __init__(self):

        self._sub_process: set[SubProcess] = set()

        signal.signal(signal.SIGINT, self._kill_process)
        signal.signal(signal.SIGTERM, self._kill_process)

    def _kill_process(self, *_):

        for process in self._sub_process:

            if process.is_running():
                process.kill()

    async def _stop_process(self):

        for process in self._sub_process:

            if process.is_running():
                await process.stop()

    async def _fill_process(self):

        for serviceFile in BaseConfig.serviceFiles:

            command_params = [serviceFile]
            process = SubProcess('python', *command_params, stderr=subprocess.PIPE)
            await process.start()

            process.create_stdout_task()
            self._sub_process.add(process)

    async def _check_process(self):

        tasks = []
        for process in self._sub_process.copy():
            tasks.append(process.wait())

        try:
            await asyncio.gather(*tasks)
        except Exception as err:
            logger.error(f'process exit {str(err)}')

    async def _run(self):

        await self._fill_process()

        await self._check_process()

        await self._stop_process()

    def run(self):

        Utils.print_slogan()
        install_uvloop()
        Utils.run_until_complete(self._run())


if __name__ == '__main__':
    MainProcess().run()
