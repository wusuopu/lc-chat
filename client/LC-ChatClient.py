#!/usr/bin/python
# -*- coding: utf-8 -*-

#作者：龙昌
#作者博客：http://www.xefan.com
#ICQ:wosuopu@gmail.com
#QQ:346202141
#email:admin@xefan.com

import sys,time,re,os
import socket,hashlib,struct,thread

try:
    import pygtk
    pygtk.require("2.0")
except:
    pass
try:
    import gtk,gobject
except:
    os._exit(1)
#检查glade文件是否存在
if not os.path.exists('client.glade'):
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

class ChatClient:
    #连接失败
    def OffLine(self):
        self.messagedialog.show()
    #接收信息
    def recieveMsg(self):
        #self.tcpCliSock.send("?list")           #获取用户列表
        while True:
            try:
                data = self.tcpCliSock.recv(self.BUFSIZ)
            except Exception,e:
                print e
                self.Warning_label.set_text(u"与服务器失去连接！")
                self.OffLine()
                return
            if data == "":
                data = " "
            if data[0] == "?":      #用户列表
                #print data
                Online_user_list = re.split(";",data[1:])
                #gtk.gdk.threads_enter()
                self.Online_liststore.clear()
                for username in Online_user_list:
                    if username != "":
                        self.Online_liststore.append([username])
                self.Online_count_label.set_markup("<b>"+str(len(Online_user_list)-1)+"</b>")
                #gtk.gdk.threads_leave()
            elif data[0] == ":":    #聊天内容
                #gtk.gdk.threads_enter()
                #print time.ctime() ,data[1:]
                self.textbuffer1.insert(self.textbuffer1.get_end_iter(),data[1:]+"\n")
                #gtk.gdk.threads_leave()
    #设置是否私聊
    def on_Private_checkbutton_toggled(self,widget):
        self.privateMessage = not self.privateMessage
        if self.SayTo[0] == ":":
            self.SayTo = self.SayTo[0:-1] + str(int(self.privateMessage))
            #print self.SayTo
    #设置聊天对象
    def on_chooseComBoBox_changed(self,widget):
        model = self.chooseComBoBox.get_model()
        iter = self.chooseComBoBox.get_active_iter()
        try:
            sayto = model.get_value(iter, 0)
        except Exception,e:
            sayto = "all"
        if sayto == "all":
            self.SayTo = "?all"
        else:
            self.SayTo = ":" + sayto + str(int(self.privateMessage))
        #print self.SayTo
    
    def delete_event(self,widget,event,data=None):
        return gtk.FALSE
    def on_MainWindow_destroy(self,widget):
        self.tcpCliSock.close()
        gtk.main_quit()
        os._exit(0)
    #
    def on_clear_textview_button_clicked(self,widget):
        widget.set_text("")
        return
    #发送
    def on_tr_button_clicked(self,widget):
        self.textbuffer2 = self.input_textview.get_buffer()
        insert_text = self.textbuffer2.get_text(self.textbuffer2.get_start_iter(),self.textbuffer2.get_end_iter())
        if insert_text == "":
            return
        if self.SayTo[0] == ":" and self.SayTo[1:-1] == self.username:
            self.textbuffer1.insert(self.textbuffer1.get_end_iter(),u'\n不能向自己发信息！\n')
            return
        try:
            self.tcpCliSock.send(self.SayTo)        #聊天对象
            self.tcpCliSock.send(insert_text[0:99])
        except Exception,e:
            print e
            self.Warning_label.set_text(u"与服务器连接失败！")
            self.OffLine()
            return
        #self.textbuffer1.insert(self.textbuffer1.get_end_iter(),insert_text+'\n')
        self.textbuffer2.set_text("")               #清空输入框
        #self.input_textview.set_buffer(self.textbuffer2)
    #设置用户列表的值
    def online_cell_data_funcs(self, column, cell, model, iter):
        cell.set_property('text', model.get_value(iter, 0))
        return
    #选择对象
    def on_online_treeview_cursor_changed(self,treeview):
        s = treeview.get_selection()
        (treestore, iter) = s.get_selected()
        if iter is None:
            return
        else:
            username = treestore.get_value(iter, 0)
            try:
                u_iter = self.liststore1.get_iter_from_string("1")
                self.liststore1.remove(u_iter)
            except Exception,e:
                    #print e
                    pass
            self.liststore1.append([username])
            self.chooseComBoBox.set_active(0)
            #print username

    #对话框我确认
    def on_dialog_button_clicked(self,widget):
        widget.hide()
    #关闭对话框
    def on_dialog_delete_event(self,widget,data=None):
        widget.hide()
        return True
    #登陆
    def on_Login_button_clicked(self,widget):
        username = self.UserName_entry.get_text()
        password = self.PassWord_entry.get_text()
        self.username = username
        self.PORT = self.Port_entry.get_text()
        self.HOST = self.HOST_entry.get_text()
        if username == "" or password == "" or self.PORT == "" or self.HOST == "":
            self.Warning_label.set_text(u"用户名、密码、主机名、端口号不能为空")
            self.messagedialog.show()
            return
        for cPort in self.PORT:
            if cPort not in "0123456789":
                self.Warning_label.set_text(u"端口号只能为数字")
                self.messagedialog.show()
                return
        self.ADDR = (self.HOST,int(self.PORT))
        try:
            self.tcpCliSock.connect(self.ADDR)
        except Exception,e:
            print e
            self.Warning_label.set_text(u"与服务器连接失败！")
            self.OffLine()
            return
        user_len = len(username)
        password = hashlib.md5(password).hexdigest()
        passwd_len = len(password)
        #压缩格式
        fmt = str(user_len) + 's' + str(passwd_len) + 's'
        try:
            self.tcpCliSock.send(fmt)
        except Exception,e:
                print e
                self.Warning_label.set_text(u"与服务器连接失败！")
                self.OffLine()
                #self.tcpCliSock.close()
                return
        sendData = struct.pack(fmt,username,password)
        #print sendData
        try:
            self.tcpCliSock.send(sendData)        #登陆
            Confirm = self.tcpCliSock.recv(1)     #判断登陆
        except Exception,e:
                print e
                self.Warning_label.set_text(u"与服务器连接失败！")
                self.OffLine()
                self.tcpCliSock.close()
                return
        if Confirm == '0':
            #print(u'服务器负荷过重，请稍后再登陆')
            self.Warning_label.set_text(u'服务器负荷过重，请稍后再登陆')
            self.messagedialog.show()
            self.tcpCliSock.close()
            return
        elif Confirm == 'T':
            #print(u'登陆成功!')
            #print(u'>>>>>>>>>>使用“?”命令查看帮助<<<<<<<<<<\n')
            self.lock = thread.allocate_lock()
            self.lock.acquire()
            thread.start_new_thread(self.recieveMsg,())
            time.sleep(1)
            
            #全局快捷键Ctrl + Enter发送信息
            accel_group = gtk.AccelGroup()
            self.window.add_accel_group(accel_group)
            self.tr_button.add_accelerator("clicked", accel_group, 65293,gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
        else:
            #print(u'登陆失败!')
            self.Warning_label.set_text(u'登陆失败!')
            self.messagedialog.show()
            self.tcpCliSock.close()
            return
        self.logwindow.hide()
        self.window.show()
    def mainloop(self):
        #显示窗口
        gtk.gdk.threads_enter()
        #显示窗口
        self.logwindow.show()
        #self.window.show()
        gtk.main()
        gtk.gdk.threads_leave()
    def __init__(self):
        #配置连接信息
        self.HOST = 'localhost'
        self.PORT = 21567
        self.BUFSIZ = 1024
        self.tcpCliSock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.privateMessage = 1 #是否私聊
        #初始化 gtkbuilder
        builder = gtk.Builder()
        #设置 glade文件
        builder.add_from_file("client.glade")
        #连接 glade文件中的signals
        builder.connect_signals(self)

        #获取主窗口
        self.window = builder.get_object("MainWindow")
        self.logwindow = builder.get_object("LoginWindow")
        #获取部件
        self.show_textview = builder.get_object("show_textview")
        self.input_textview = builder.get_object("input_textview")
        self.tr_button = builder.get_object("tr_button")
        self.textbuffer1 = builder.get_object("textbuffer1")
        self.textbuffer2 = builder.get_object("textbuffer2")
        #下拉组合框
        self.liststore1 = builder.get_object("liststore1")
        self.chooseComBoBox = builder.get_object("chooseComBoBox")
        self.cell_ComBoBox = gtk.CellRendererText()
        self.chooseComBoBox.pack_start(self.cell_ComBoBox, True)
        self.chooseComBoBox.add_attribute(self.cell_ComBoBox, 'text',0)
        self.chooseComBoBox.set_active(0)
        #在线用户列表
        self.Online_count_label = builder.get_object("online_count_label")
        self.Online_treeview = builder.get_object("online_treeview")
        #self.Online_liststore = builder.get_object("Online_liststore")
        
        #获取在线用户
        self.Online_liststore = gtk.ListStore(str)
        
        self.Online_cell = gtk.CellRendererText()
        self.Online_column = gtk.TreeViewColumn(u"在线用户")
        self.Online_column.pack_start(self.Online_cell, False)
        #self.Online_cell.set_property('xalign', 1.0)
        self.Online_column.set_cell_data_func(self.Online_cell, self.online_cell_data_funcs)
        self.Online_treeview.append_column(self.Online_column)
        self.Online_treeview.set_model(self.Online_liststore)
        
        #登陆输入
        self.UserName_entry = builder.get_object("UserName_entry")
        self.PassWord_entry = builder.get_object("PassWord_entry")
        self.HOST_entry = builder.get_object("HOST_entry")
        self.Port_entry = builder.get_object("Port_entry")
        #对话框
        self.Warning_label = builder.get_object("Warning_label")
        self.messagedialog = builder.get_object("dialog")
        #
        #self.show_textview.set_buffer(self.textbuffer1)
        
if __name__ == "__main__":
    window=ChatClient()
    window.mainloop()


