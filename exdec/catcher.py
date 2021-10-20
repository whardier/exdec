import asyncio
import functools
from typing import Any, Callable, Optional

from .data_classes import DecData, FuncInfo


def handle_wrapper(handle_exception_method):
    @functools.wraps(handle_exception_method)
    def handle_exception(self, dec_data: DecData):

        self.try_reraise(dec_data)

        dec_data.handler = self.select_handler(dec_data)

        func_self = self.get_func_self(dec_data)
        if func_self is not None:
            dec_data.func_info.self = func_self
            dec_data.func_info.args = dec_data.func_info.args[1:]

        if asyncio.iscoroutinefunction(handle_exception_method):
            async def async_func():
                return await handle_exception_method(self, dec_data)
            return async_func()
        else:
            return handle_exception_method(self, dec_data)

    return handle_exception


class Catcher:

    def default_handler(self, func_info: FuncInfo):
        print("--- tmp:", type(func_info.exception), func_info.exception)

    @staticmethod
    def try_reraise(dec_data: DecData):

        func_exception = dec_data.func_info.exception
        exception_classes = dec_data.exceptions

        if dec_data.exclude:
            if isinstance(func_exception, exception_classes):
                raise
        else:
            if not isinstance(func_exception, exception_classes):
                raise

    @staticmethod
    def get_func_self(dec_data: DecData) -> Optional[object]:

        func = dec_data.func_info.func
        func_args = dec_data.func_info.args

        # TODO: add parse class method
        if func_args and hasattr(func_args[0], func.__name__):
            class_name = func_args[0].__class__.__name__
            if func.__qualname__ == f"{class_name}.{func.__name__}":
                return func_args[0]

    def select_handler(self, dec_data: DecData) -> Callable:

        return self.default_handler if dec_data.handler is None \
               else dec_data.handler

    @handle_wrapper
    def handle_exception(self, dec_data: DecData) -> Any:

        return dec_data.handler(dec_data.func_info)

    @handle_wrapper
    async def aio_handle_exception(self, dec_data: DecData) -> Any:

        if asyncio.iscoroutinefunction(dec_data.handler):
            return await dec_data.handler(dec_data.func_info)
        else:
            return dec_data.handler(dec_data.func_info)
