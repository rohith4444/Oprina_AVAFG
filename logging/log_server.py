import logging
import logging.handlers
import socketserver
import struct
import pickle
import threading
import time
import os
from pathlib import Path
import sys
from queue import Queue
import socket

class LogQueueHandler(logging.handlers.QueueHandler):
    """Queue handler for buffering log records"""
    def enqueue(self, record):
        try:
            self.queue.put_nowait(record)
        except Exception:
            pass

class ResilientLogRecordStreamHandler(socketserver.StreamRequestHandler):
    """Handler with connection recovery"""
    
    def setup(self):
        super().setup()
        self.connection_alive = True
        self.log_queue = Queue()
        self.setup_logger()

    def setup_logger(self):
        self.logger = logging.getLogger("LogServer")
        self.logger.setLevel(logging.INFO)
        
        # Console handler
        console = logging.StreamHandler()
        console.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        self.logger.addHandler(console)

    def handle(self):
        while self.connection_alive:
            try:
                chunk = self.connection.recv(4)
                if len(chunk) < 4:
                    break
                    
                slen = struct.unpack('>L', chunk)[0]
                chunk = self.connection.recv(slen)
                
                while len(chunk) < slen and self.connection_alive:
                    chunk = chunk + self.connection.recv(slen - len(chunk))
                    
                record = logging.makeLogRecord(pickle.loads(chunk))
                self.handle_log_record(record)
                
            except (ConnectionError, socket.error) as e:
                self.logger.warning(f"Connection issue: {e}")
                self.attempt_reconnection()
            except Exception as e:
                self.logger.error(f"Error handling log record: {e}")
                self.connection_alive = False

    def attempt_reconnection(self):
        """Attempt to restore connection"""
        max_attempts = 3
        attempt = 0
        
        while attempt < max_attempts and not self.connection_alive:
            try:
                self.logger.info(f"Attempting reconnection {attempt + 1}/{max_attempts}")
                self.connection = self.request
                self.connection_alive = True
                self.logger.info("Connection restored")
                break
            except Exception as e:
                attempt += 1
                self.logger.error(f"Reconnection attempt {attempt} failed: {e}")
                time.sleep(1)

    def handle_log_record(self, record):
        if not hasattr(self, 'log_handlers'):
            self.log_handlers = {}
            
        logger_name = record.name
        if logger_name not in self.log_handlers:
            # Create logger
            logger = logging.getLogger(logger_name)
            logger.handlers = []  # Remove existing handlers
            logger.propagate = False
            
            # File handler
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            file_handler = logging.FileHandler(
                log_dir / f"{logger_name.replace('.', '_')}.log"
            )
            file_handler.setFormatter(
                logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            )
            logger.addHandler(file_handler)
            
            # Console handler with colors
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(ColoredFormatter())
            logger.addHandler(console_handler)
            
            self.log_handlers[logger_name] = logger
            
        logger = self.log_handlers[logger_name]
        logger.handle(record)

class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output"""
    def __init__(self):
        super().__init__()
        self.colors = {
            'DEBUG': '\033[36m',    # Cyan
            'INFO': '\033[32m',     # Green
            'WARNING': '\033[33m',   # Yellow
            'ERROR': '\033[31m',     # Red
            'CRITICAL': '\033[37;41m',  # White on Red
            'RESET': '\033[0m'
        }
        self.fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    def format(self, record):
        color = self.colors.get(record.levelname, self.colors['RESET'])
        formatted_msg = logging.Formatter(self.fmt).format(record)
        return f"{color}{formatted_msg}{self.colors['RESET']}"

class ResilientLogServer(socketserver.ThreadingTCPServer):
    """TCP Server with connection recovery"""
    allow_reuse_address = True
    daemon_threads = True

def serve_logging(host='localhost', port=9020):
    """Start the logging server with connection recovery"""
    while True:
        try:
            server = ResilientLogServer((host, port), ResilientLogRecordStreamHandler)
            print('\033[32m' + f"Log server started on {host}:{port}" + '\033[0m')
            server.serve_forever()
        except Exception as e:
            print('\033[31m' + f"Server error: {e}, restarting..." + '\033[0m')
            time.sleep(1)

if __name__ == '__main__':
    serve_logging()