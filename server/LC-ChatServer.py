#!/usr/bin/python
# -*- coding: utf-8 -*-

#作者：龙昌
#作者博客：http://www.xefan.com
#ICQ:wosuopu@gmail.com
#QQ:346202141
#email:admin@xefan.com

import socket,time,xml.etree.ElementTree,struct,thread
import os
import urllib2,re

try:
    import pygtk
    pygtk.require("2.0")
except:
    pass
try:
    import gtk,gobject
except Exception,e:
    os._exit(1)
#检查glade文件是否存在
if not os.path.exists('server.glade'):
    #新建窗口
    window = gtk.Window(gtk.WINDOW_TOPLEVEL)
    window.set_title("错误!")
    window.set_resizable(False)
    window.set_position(gtk.WIN_POS_CENTER)
    window.connect("destroy", lambda wid: gtk.main_quit())
    window.connect("delete_event", lambda a1,a2:gtk.main_quit())
    #
    box1 = gtk.VBox(False, 0)
    label = gtk.Label("配置文件丢失，程序无法启动！")
    label2 = gtk.Label("确定")
    button = gtk.Button()
    button.add(label2)
    button.connect("clicked", lambda wid: gtk.main_quit())
    box1.pack_start(label, False, False, 3)
    box1.pack_start(button, False, False, 3)
    
    window.add(box1)
    window.show_all()
    gtk.main()
    os._exit(1)

gobject.threads_init()

class ChatServer:
    def delete_event(self,widget,event,data=None):
        return gtk.FALSE
    def on_MainWindow_delete_event(self,widget,data=None):
        widget.show()
        return True    #不激活destroy信号 
    #点击启动按钮
    def on_Start_button_clicked(self,widget):
        try:
            self.PORT = int(self.Port_entry.get_text())
            self.MAXTHREAD = int(self.MAX_entry.get_text())
            
            self.ADDR = (self.HOST,self.PORT)
            self.tcpServSocket.bind(self.ADDR)
            self.tcpServSocket.listen(15)
            self.startTCPThread()
        except Exception,e:
            print e
            self.Error_dialog.show()
            return
        gtk.gdk.threads_enter()
        widget.set_label(u"已启动")
        gtk.gdk.threads_leave()
        widget.set_sensitive(False)
        thread.start_new_thread(self.getOnlineNum,())
            
    #点击退出按钮
    def on_Quit_button_clicked(self,widget):
        widget.show()
    #取消退出
    def on_Cancle_Quit_button_clicked(self,widget):
        widget.hide()
    #确定退出
    def on_OK_Quit_button_clicked(self,widget):
        widget.hide()
        gtk.main_quit()
        os._exit(0)
    def mainloop(self):
        #显示窗口
        gtk.gdk.threads_enter()
        self.window.show()
        gtk.main()
        gtk.gdk.threads_leave()
    def __init__(self):
        #配置信息
        self.HOST = ''
        self.PORT = 21567
        self.BUFSIZE = 1024
        self.MAXTHREAD = 4
        self.ProNum = self.MAXTHREAD
        self.TCPList = {}
        self.ConFlag = 0
        #建立连接
        self.tcpServSocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        #self.locks = []
        
        #初始化 gtkbuilder
        builder = gtk.Builder()
        #设置 glade文件
        builder.add_from_file("server.glade")
        #连接 glade文件中的signals
        builder.connect_signals(self)
        #获取主窗口
        self.window = builder.get_object("MainWindow")
        self.Error_dialog = builder.get_object("Error_dialog")
        self.Port_entry = builder.get_object("Port_entry")
        self.MAX_entry = builder.get_object("MAX_entry")
        self.OnlineNum_label = builder.get_object("OnlineNum_label")
        
        #本机ip地址
        self.HostName_entry = builder.get_object("HostName_entry")
        self.PrivateIP_entry = builder.get_object("PrivateIP_entry")
        self.PublicIP_entry = builder.get_object("PublicIP_entry")
        s1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s1.connect(('www.123cha.com', 0))
            my_ip1 = s1.getsockname()[0]
        except Exception,e:
            my_ip1 = u"获取失败"
        my_host_name = socket.gethostname()
        #my_ip1 = socket.gethostbyname(my_host_name)
        try:
            my_ip2 = re.search('\d+\.\d+\.\d+\.\d+',urllib2.urlopen("http://www.123cha.com/").read()).group(0)
        except Exception,e:
            my_ip2 = u"获取失败"
        self.HostName_entry.set_text(my_host_name)
        self.PrivateIP_entry.set_text(my_ip1)
        self.PublicIP_entry.set_text(my_ip2)

    def WaitCon(self):        
        while True:
            #print "self.ProNum:"+str(self.ProNum)
            print('waiting for connection...')
            tcpClientSocket,addr = self.tcpServSocket.accept()
            thread.start_new_thread(self.WaitCon2, (tcpClientSocket, addr,))
    def WaitCon2(self, tcpClientSocket, addr):
            #print tcpClientSocket, addr
            self.ProNum -= 1
                
            #检查登陆
            fmt = tcpClientSocket.recv(self.BUFSIZE)
            #print "fmt:",fmt
            data = tcpClientSocket.recv(self.BUFSIZE)
            #print "data:",data
                
            if self.ProNum == 0:
                tcpClientSocket.send('0')
                tcpClientSocket.close()
                self.ProNum += 1
                #continue
                thread.exit()
                
            Userdata = struct.unpack(fmt,data)
            #data = CheckLogin(userdata[0],userdata[1])
            #检查密码
            root = xml.etree.ElementTree.parse('data.xml')
            userdata = root.getiterator('userdata')
            sendData = 'F'
            for node in userdata:
                if node.find('username').text != Userdata[0]:
                    continue
                else:
                    if node.find('password').text == Userdata[1]:
                        sendData = 'T'
                    else:
                        sendData = 'F'
                    break
                    
            tcpClientSocket.send(sendData)
            if sendData == 'F':        #密码错误
                tcpClientSocket.close()
                self.ProNum += 1
                #break
                thread.exit()
            #print('connected from:',addr,'\n')
        
            self.TCPList[Userdata[0]]=tcpClientSocket
            #print self.TCPList
            self.ConFlag = 1
            repeatData='?'
            for user,tcp in self.TCPList.items():
                repeatData+=user+';'
            #tcpClientSocket.send(repeatData)
            for user,tcp in self.TCPList.items():
                tcp.send(repeatData)
            while True:
                try:
                    data = tcpClientSocket.recv(self.BUFSIZE)
                except Exception,e:
                    break
                if not data:
                    break
                
                if data == '?list':    #用户列表
                    repeatData='?'
                    for user,tcp in self.TCPList.items():
                        repeatData+=user+';'
                    tcpClientSocket.send(repeatData)
                
                if data[0] == ':':    #私聊
                    if data[1:-1] not in self.TCPList:    #譔用户不在线
                        #tcpClientSocket.send('0')
                        tcpClientSocket.send(u':\n譔用户目前不在线\n')
                        tcpClientSocket.recv(self.BUFSIZE)
                        continue
                    #tcpClientSocket.send('1')
                    UserTo = data[1:-1]
                    private = data[-1]
                    data = tcpClientSocket.recv(self.BUFSIZE)
                    ProcessTime = time.ctime()
                    if private == "1":
                        repeatData = ':[%s] from:[%s] to you\n%s\n' %(ProcessTime,Userdata[0],data)
                        self.TCPList[UserTo].send(repeatData)
                        repeatData = ':[%s] from:you to [%s]\n%s\n' %(ProcessTime,UserTo,data)
                        self.TCPList[Userdata[0]].send(repeatData)
                    elif private == "0":
                        repeatData = ':[%s] from:[%s] to [%s]\n%s\n' %(ProcessTime,Userdata[0],UserTo,data)
                        for user,tcp in self.TCPList.items():
                            tcp.send(repeatData)
                
                if data == '?all':    #群聊
                    #tcpClientSocket.send('[%s] %s' %(time.ctime(),data))
                    data = tcpClientSocket.recv(self.BUFSIZE)
                    repeatData = ':[%s] from:[%s]\n%s\n' %(time.ctime(),Userdata[0],data)
                    for user,tcp in self.TCPList.items():
                        tcp.send(repeatData)
            del self.TCPList[Userdata[0]]
            repeatData='?'
            for user,tcp in self.TCPList.items():
                repeatData+=user+';'
            #tcpClientSocket.send(repeatData)
            for user,tcp in self.TCPList.items():
                tcp.send(repeatData)
            tcpClientSocket.close()
            self.ConFlag = 1
            self.ProNum += 1
    def getOnlineNum(self):
        while True:
            if self.ConFlag:
                OnlineNum = len(self.TCPList)
                gtk.gdk.threads_enter()
                self.OnlineNum_label.set_markup(u"当前在线人数：<b>"+str(OnlineNum)+u"</b>")
                gtk.gdk.threads_leave()
                self.ConFlag = 0
    def startTCPThread(self):
        self.lock = thread.allocate_lock()
        self.lock.acquire()
        
        #i = 0
        #while i < self.MAXTHREAD:
        thread.start_new_thread(self.WaitCon,())
        #    i += 1

if __name__ == "__main__":
    window=ChatServer()
    window.mainloop()

