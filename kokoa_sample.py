import socket
import threading
import sys

class Server:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connections = []
    nickname = {}
    nick_cnt = -1
    def __init__(self):
        self.sock.bind(('0.0.0.0', 4967))
        self.sock.listen(20)

        
    def handler_all_chat(self,c,a):
        while True:
            try:                                        
                data = c.recv(1024)
            except ConnectionResetError:            #클라이언트 종료
                self.connections.remove(c)
                print(str(a[0]) + ':' + str(a[1]), "disconnected")
                self.nick_cnt -= 1
                c.close()
                break
            
            data = str(data,'utf-8')                #클라이언트가 보낸 내용 변환
            data = data.split('@')
            
            if len(data) > 2:                       #클라이언트의 닉네임 설정 및 변환 +  설정하면 클라이언트한테 누구누구가 채팅방에 입장했다고 보내주기
                nick_order = int(data[1])
                nick = data[2]
                self.nickname[nick_order] = nick
            else:
                try:                                #클라이언트의 대화
                    nick_order = int(data[0])
                    msg = data[1]
                    for connection in self.connections:
                        inst = self.nickname[nick_order] + ": " + msg
                        connection.send(bytes(inst,'utf-8'))
                except:                             #클라이언트가 잘못된 프로토콜로 전송
                    print(str(nick_order) , "번 클라이언트가 서식을 잘못 입력하였습니다.")
                    inst = "서식을 제대로 입력하세요"
                    self.connections[nick_order].send(bytes(inst,'utf-8'))
                    

    def run(self):
        while True:
            c, a = self.sock.accept()
            cThread = threading.Thread(target = self.handler_all_chat, args=(c,a))
            cThread.daemon = True
            cThread.start()
            self.connections.append(c)
            print(self.connections)
            print(str(a[0]) + ':' + str(a[1]), "connected")
            print(c.getpeername()[1])
            self.nick_cnt += 1
            self.send_nickorder()
            
    def send_nickorder(self):
        inst1 = "부여된 번호는 " + "\"" + str(self.nick_cnt) + "\"" + " 입니다."
        inst2 = "대화양식 :  \"번호@대화내용\"  입니다."
        inst3 = "닉네임을 먼저 지정해주셔야 합니다."
        inst4 = "닉네임은 \"@번호@닉네임\" 방식으로 지정해주세요."
        inst5 = str(self.nick_cnt)
        self.connections[self.nick_cnt].send(bytes(inst1,'utf-8'))
        self.connections[self.nick_cnt].send(bytes(inst2,'utf-8'))
        self.connections[self.nick_cnt].send(bytes(inst3,'utf-8'))
        self.connections[self.nick_cnt].send(bytes(inst4,'utf-8'))        
        self.connections[self.nick_cnt].send(bytes(inst4,'utf-8'))




class Client:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    nickname_created = False
    nick_order = 0
    
    def __init__(self,address):
        self.sock.connect((address,4967))

        iThread = threading.Thread(target=self.sendMsg)
        iThread.daemon = True
        iThread.start()

        while True:
            data = self.sock.recv(1024)
            if not data:
                break
            elif self.nickname_created == False:
                self.create_nickname()
            else:
                print(str(data,'utf-8'))

            
    def sendMsg(self):
        while True:
            if self.nickname_created == True:
                self.sock.send(bytes(input(""),'utf-8'))


    def create_nickname(self):
        nick = input("닉네임 : ")
        
        

if (len(sys.argv) > 1):
    client = Client(sys.argv[1])
else:
    server = Server()
    server.run()
            
