import logger
import myqq
from bilibili import bili
from vedio_pusher import videoPusher

if __name__ == '__main__':
    logger.init()
    bili.login()
    myqq.start_listen()
    videoPusher.start()
