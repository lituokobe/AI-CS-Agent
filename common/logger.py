#!/usr/bin/python
# coding:utf-8

import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path


class TimedRotatingFileHandlerWithCategory(logging.handlers.TimedRotatingFileHandler):
    def __init__(self, base_filename, when='midnight', interval=1, backupCount=0, encoding=None, delay=False, utc=False,
                 category=None):
        # 添加category参数以支持分类命名
        self.category = category
        # 获取当前日期并构建文件夹路径
        today = datetime.today().strftime('%Y-%m-%d')
        if category is None:
            category = 'message'
        # dirname = os.path.join(os.path.dirname(base_filename), category)
        # dirname = os.path.join(os.path.dirname(base_filename), category, today)
        dirname = os.path.join(os.path.dirname(base_filename), str(category))
        # 如果文件夹不存在，则创建它
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        # 构建带有分类的日志文件名
        if category:
            base_filename = os.path.join(dirname, f"{os.path.basename(base_filename)}.log")
        # 调用父类的构造函数
        super().__init__(base_filename, when, interval, backupCount, encoding, delay, utc)


# 配置日志记录器
def setup_logger(name, level=logging.DEBUG, category=None, console_output=True):
    # 构建日志文件的路径（不包含分类，因为将在处理器中处理）
    log_dir = str(Path().cwd()) + '/static/logs/'  # 替换为你的日志目录路径
    base_filename = os.path.join(log_dir, str(name))

    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 创建自定义的处理器（文件输出）
    file_handler = TimedRotatingFileHandlerWithCategory(base_filename, when='midnight', interval=1, backupCount=7,
                                                        category=category, encoding='utf-8')

    # 创建格式器
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)

    # 添加文件处理器
    add_handler_safely(file_handler, logger)

    # 添加控制台处理器（如果启用）
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        add_handler_safely(console_handler, logger)

    return logger


def add_handler_safely(handler, logger):
    for h in logger.handlers:
        if type(h) is type(handler):  # 检查类型是否重复
            logger.debug('重复')
            return
    logger.addHandler(handler)
    logger.debug('添加新的日志处理器')


def cleanup_logging(handler_types=None):
    """清理指定类型的处理器，默认清理所有处理器"""
    root = logging.getLogger()
    for logger in [root] + list(logging.Logger.manager.loggerDict.values()):
        if not isinstance(logger, logging.Logger):
            continue
        for handler in logger.handlers[:]:
            print(handler)
            if (handler_types and isinstance(handler, tuple(handler_types))) or not handler_types:
                # 关闭并移除处理器
                handler.close()
                logger.removeHandler(handler)

# 使用配置好的日志记录器
# logger1 = setup_logger('douyin', category='category1')
# logger2 = setup_logger('module2', category='category2')
#
# # 记录日志
# logger1.debug('这是module1在category1下的调试信息')
# logger1.info('这是module1在category1下的信息')
#
# logger2.warning('这是module2在category2下的警告信息')
# logger2.error('这是module2在category2下的错误信息')
