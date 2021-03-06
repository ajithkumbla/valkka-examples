import time
from valkka.core import *
"""
(LiveThread:livethread) --> {InfoFrameFilter:live_out_filter}
"""
live_out_filter =InfoFrameFilter("live_out_filter")
livethread =LiveThread("livethread")
ctx =LiveConnectionContext(LiveConnectionType_rtsp, "rtsp://admin:nordic12345@192.168.1.41", 1, live_out_filter)

livethread.startCall()
livethread.registerStreamCall(ctx)
livethread.playStreamCall(ctx)
time.sleep(5)
livethread.stopCall()

print("bye")
