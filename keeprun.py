import pywintypes
import win32con, win32process, win32event, win32job
import json
import os
import atexit
import psutil

#load data
exedata=json.load(open("keeprun.json","r",encoding="utf-8"))

#pre-cleanup
for proc in psutil.process_iter():
  for i in exedata:
    if proc.name() == i['exec']:
      proc.kill()
      break

#job thing
hjob=win32job.CreateJobObject(None,"pyKeepRun")

#...
def killLaunched():
  win32job.TerminateJobObject(hjob,0)

atexit.register(killLaunched)

hprocs=[]
procids=[]

#no window launch
def launchProcess(info):
  sinfo=win32process.STARTUPINFO()
  sinfo.dwFlags=win32con.STARTF_USESHOWWINDOW
  sinfo.wShowWindow=win32con.SW_HIDE
  (hproc,_,procid,_)=win32process.CreateProcess(
    os.path.join(info["path"],info["exec"]),
    info["exec"]+" "+info["args"],
    None,
    None,
    False,
    win32process.DETACHED_PROCESS,
    None,
    info["path"],
    sinfo)
  win32job.AssignProcessToJobObject(hjob,hproc)
  return (hproc,procid)

#...
for i in exedata:
  (hproc,procid)=launchProcess(i)
  hprocs.append(hproc)
  procids.append(procid)

#Wait for kill and restart it
while True:
  sig=win32event.WaitForMultipleObjects(hprocs,False,win32event.INFINITE)
  if sig-win32event.WAIT_OBJECT_0>=0 and sig-win32event.WAIT_OBJECT_0<len(hprocs):
    index=sig-win32event.WAIT_OBJECT_0
    i=exedata[index]
    (hproc,procid)=launchProcess(i)
    hprocs[index]=hproc
    procids[index]=procid

