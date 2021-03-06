import time
from valkka.api2.threads import LiveThread, OpenGLThread
from valkka.api2.chains import BasicFilterchain

livethread=LiveThread( # starts live stream services (using live555)
  name   ="live_thread",
  verbose=False,
  affinity=-1
)

openglthread=OpenGLThread(
  name    ="glthread",
  n720p   =20,   # reserve stacks of YUV video frames for various resolutions
  n1080p  =20,
  n1440p  =0,
  n4K     =0,
  verbose =False,
  msbuftime=100,
  affinity=-1
)

chain=BasicFilterchain( # decoding and branching the stream happens here
  livethread  =livethread, 
  openglthread=openglthread,
  address     =address,
  slot        =1,
  affinity    =-1,
  verbose     =False,
  msreconnect =10000
)

print("bye")
