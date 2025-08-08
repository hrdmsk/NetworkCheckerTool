# logger_setup.py
import logging
import sys
import os
from functools import wraps

def setup_logger():
    """アプリケーション全体のロガーを設定します。"""
    
    if getattr(sys, 'frozen', False):
        log_dir = os.path.dirname(sys.executable)
    else:
        log_dir = os.path.dirname(os.path.abspath(__file__))

    log_file = os.path.join(log_dir, 'rentalserverchecker.log')

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout) 
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("resetup_logger")
    return logger

logger = setup_logger()

def log_execution(func):
    """関数の実行をログに記録するデコレータ"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # 'self'を除いた引数をログに出力
        func_args = ', '.join(repr(a) for a in args[1:])
        logger.info(f"{func.__name__}({func_args})")
        
        # 元の関数を実行
        return func(*args, **kwargs)
            
    return wrapper
