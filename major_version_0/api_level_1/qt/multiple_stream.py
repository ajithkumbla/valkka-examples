"""
multiple_stream.py : A demo program streaming from various rtsp cameras and other sources (defined per .sdp files)

Copyright 2017 Sampsa Riikonen

Authors: Sampsa Riikonen

This file is part of the Valkka Python3 examples library

Valkka Python3 examples library is free software: you can redistribute it and/or modify
it under the terms of the MIT License
 
This code is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the MIT License for more details.

@file    multiple_stream.py
@author  Sampsa Riikonen
@date    2017
@version 0.1
@brief   A demo program streaming from various rtsp cameras and other sources (defined per .sdp files)
"""

from PyQt5 import QtWidgets, QtCore, QtGui # Qt5
import sys
from valkka.valkka_core import *


class FilterChain:
  """
    filtergraph:
    --> {FifoFrameFilter:av_in_filter} --> [FrameFifo:av_fifo] -->> (AVThread:avthread) --> {FifoFrameFilter:gl_in_gilter} -->
    """
  
  def __init__(self, gl_in_filter, window_id, address, slot):
    self.gl_in_filter =gl_in_filter
    self.window_id    =window_id
    self.address      =address
    self.slot         =slot
    self.render_ctx   =None
    
    self.av_fifo         =FrameFifo          ("av_fifo",10)                 
    self.avthread        =AVThread           ("avthread",       self.av_fifo, self.gl_in_filter) # [av_fifo] -->> (avthread) --> {gl_in_filter}
    self.av_in_filter    =FifoFrameFilter    ("av_in_filter",   self.av_fifo)
    self.live_out_filter =InfoFrameFilter    ("live_out_filter",self.av_in_filter)
    
    self.ctx=LiveConnectionContext()
    self.ctx.slot=slot
    if (self.address.find("rtsp://")>-1):
      self.ctx.connection_type=LiveConnectionType_rtsp
    else:
      self.ctx.connection_type=LiveConnectionType_sdp
    self.ctx.address=self.address
    self.ctx.framefilter=self.live_out_filter
    
    self.avthread.startCall()
    self.avthread.decodingOnCall()


  def getSlot(self):
    return self.slot

  def getConnectionCtx(self):
    return self.ctx
        
  def getLiveFilter(self):
    return self.live_out_filter
  
  def getWindowId(self):
    return self.window_id
  
  def decodingOn(self):
    self.avthread.decodingOnCall()

  def decodingOff(self):
    self.avthread.decodingOffCall()

  def setRenderCtx(self,n):
    self.render_ctx=n
    
  def getRenderCtx(self):
    return self.render_ctx

  def stop(self):
    self.avthread.stopCall() # TODO: this should be called at garbage collection => c++ destructor


class MyGui(QtWidgets.QMainWindow):

  def __init__(self,parent=None,addresses=[]):
    super(MyGui, self).__init__()
    self.debug=False
    # self.debug=True
    if (len(addresses)<1):
      print("No streams!")
      return
    self.addresses=addresses
    self.n_streams=len(self.addresses)
    self.initVars()
    self.setupUi()
    if (self.debug): return
    self.openValkka()
    self.makeFilterChains()
    self.start_streams()
    

  def initVars(self):
    self.filterchains=[]
    self.videoframes=[]
    

  def setupUi(self):
    self.setGeometry(QtCore.QRect(100,100,500,500))
    
    self.w=QtWidgets.QWidget(self)
    self.setCentralWidget(self.w)
    
    self.lay=QtWidgets.QGridLayout(self.w)
    
    for i, address in enumerate(self.addresses):
      fr=QtWidgets.QFrame(self.w)
      print("setupUi: layout index, address : ",i//4,i%4,address)
      self.lay.addWidget(fr,i//4,i%4)
      self.videoframes.append((fr,address)) # list of (QFrame, address) pairs
    
    
  def openValkka(self):
    """
    filtergraph:
    (LiveThread:livethread) --> FilterChain --> {FifoFrameFilter:gl_in_gilter} --> [OpenGLFrameFifo:gl_fifo] -->> (OpenGLThread:glthread)
    """
    self.glthread        =OpenGLThread ("glthread",
                                        self.n_streams*10,     # n720p
                                        self.n_streams*10,     # n1080p
                                        0,                     # n1440p
                                        0,                     # n4K
                                        self.n_streams*10,     # naudio
                                        100,                   # msbuftime
                                        -1                     # thread affinity
                                        )
    
    self.gl_fifo         =self.glthread.getFifo() # get gl_fifo from glthread
    self.gl_in_filter    =FifoFrameFilter    ("gl_in_filter", self.gl_fifo)
    self.livethread      =LiveThread         ("livethread")
    
    self.glthread.  startCall()
    self.livethread.startCall()
    
  
  def closeValkka(self):
    self.livethread.stopCall()
    self.glthread.  stopCall()
  
  
  def makeFilterChains(self):
    for i, videoframe in enumerate(self.videoframes): # videoframe == (QFrame, address) pairs
      window_id=int(videoframe[0].winId()) # QFrame.windId() returns x-window id
      address  =videoframe[1]
      self.filterchains.append( FilterChain(self.gl_in_filter, window_id, address, i+1) )
    
    
  def start_streams(self):
    print("starting streams")
    for filterchain in self.filterchains:
      ctx=filterchain.getConnectionCtx()
      self.livethread.registerStreamCall(ctx)
      self.livethread.playStreamCall(ctx)
      filterchain.decodingOn()
      
      window_id=filterchain.getWindowId()
      self.glthread.newRenderGroupCall(window_id)
      context_id=self.glthread.newRenderContextCall(filterchain.getSlot(), window_id, 0)
      filterchain.setRenderCtx(context_id) # save context id to filterchain
    
    
  def stop_streams(self):
    print("stopping streams")
    for filterchain in self.filterchains:
      filterchain.stop()
      ctx=filterchain.getConnectionCtx()
      self.livethread.stopStreamCall(ctx)
      self.livethread.deregisterStreamCall(ctx)
      self.glthread.delRenderContextCall(filterchain.getRenderCtx())
      self.glthread.delRenderGroupCall(filterchain.getWindowId())

    
  def closeEvent(self,e):
    print("closeEvent!")
    self.stop_streams()
    self.closeValkka()
    e.accept()


def main():
  if (len(sys.argv)<2):
    print("Give multiple rtsp and sdp stream addresses, i.e. rtsp://passwd1:user1@ip1 sdp_filename1 sdp_filename2 rtsp://passwd2:user2@i2")
    return
  app=QtWidgets.QApplication(["multiple_stream_test"])
  mg=MyGui(addresses=sys.argv[1:])
  mg.show()
  app.exec_()


if (__name__=="__main__"):
  main()
 
