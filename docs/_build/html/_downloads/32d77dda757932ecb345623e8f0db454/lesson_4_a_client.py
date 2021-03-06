from valkka.core import *

width  =1920//4
height =1080//4

shmem_name    ="lesson_4"      # This identifies posix shared memory - must be unique
shmem_buffers =10              # Size of the shmem ringbuffer

"""<rtf>
The wrapped cpp class is *SharedMemRingBufferRGB* (at the server side, RGBShmemFrameFilter is using SharedMemRingBufferRGB):
<rtf>"""
shmem = SharedMemRingBufferRGB(shmem_name, shmem_buffers, width, height, 1000, False) # shmem id, buffers, w, h, timeout, False=this is a client
  
"""<rtf>
We are using an integer pointers and a metadata object:
<rtf>"""
index_p = new_intp() # shmem index
meta    = RGB24Meta()
  
"""<rtf>
Next, get the shared memory ringbuffer as a list of numpy arrays:
<rtf>"""
shmem_list = shmem.getBufferListPy()
  
"""<rtf>
Finally, start reading frames:
<rtf>"""
while True:
  got = shmem.clientPullFrame(index_p, meta)
  # got = shmem.clientPullFrameThread(index_p, meta) # if you are using multithreading
  if got:
    index = intp_value(index_p)
    data = shmem_list[index][0:meta.size]
    print("data   : ",data[0:min(10,meta.size)])
    print("width  : ", meta.width)
    print("height : ", meta.height)
    print("slot   : ", meta.slot)
    print("time   : ", meta.mstimestamp)
    print("size required : ", meta.width * meta.height * 3)
    print("size copied   : ", meta.size)
    print()
  else:
    print("timeout")
