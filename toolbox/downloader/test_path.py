# -*- coding: utf-8 -*-

if __name__ == '__main__':
    # import os
    # import subprocess
    #
    # from common import BINARY_PATH
    # from threading import thread
    #
    # print BINARY_PATH
    #
    # path = os.environ['PATH']
    # path = ';'.join([BINARY_PATH, path])
    # os.environ['PATH'] = path
    #
    # print os.environ['PATH']
    #
    # subprocess.call(['wget', 'http://mirrors.aliyun.com/ubuntu-releases/16.04.1/ubuntu-16.04-desktop-amd64.iso'])


    from threading import Thread
    import time

    class LogMonitor(Thread):

        def __init__(self, *args, **traits):
            super(LogMonitor, self).__init__(*args, **traits)

            self.speed = 0
            self.progress = 0.0

        def run(self):
            for i in xrange(10):
                self.speed += 1
                self.progress += 0.1
                time.sleep(5)

                print 'in child thread: ', self.speed, self.progress


    thread = LogMonitor()
    thread.start()

    while True:
        time.sleep(5)
        print 'in main thread: ', thread.speed, thread.progress
