import socket
import threading
import sys
import time

class Server:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connections = []                            #전체 채팅을 위해 접속한 클라이언트의 정보를 저장할 리스트
    clientNickList = {}                         #클라이언트의 포트번호를 키로, 닉네임을 밸류로 갖는 현재 접속자 수를 출력하기 위한 딕셔너리
    clientSocketList = {}                       #위 딕셔너리의 키와 밸류가 뒤바뀐 딕셔너리로, 귓속말 기능을 위한 딕셔너리
    checkMark = '@'
    
    def __init__(self):
        self.sock.bind(('0.0.0.0', 4967))
        self.sock.listen(20)

    def run(self):                              #메인 쓰레드
        self.serverReport(1)
        while True:
            c, a = self.sock.accept()
            clientIP = str(a[0])
            clientPortNum = str(a[1])
            cThread = threading.Thread(target = self.chatHandler, args=(c,a,clientIP,clientPortNum))
            cThread.daemon = True
            cThread.start()
            self.connections.append(c)
            self.clientNickList[int(clientPortNum)] = None
            self.serverReport(2,clientIP,clientPortNum)
        
    def chatHandler(self,c,a,clientIP,clientPortNum):       #클라이언트당 구동되는 쓰레드
        
        while True:
            try:                                        
                requestMsg = c.recv(1024)
            except ConnectionResetError:                    #클라이언트 종료
                self.connections.remove(c)
                try:                                        #클라이언트가 닉네임 설정 후 종료하였을 경우
                    del self.clientNickList[int(clientPortNum)]
                    self.serverReport(3,clientIP,clientPortNum,nick)
                except:                                     #클라이언트가 닉네임 설정하지 않고 종료하였을 경우
                    self.serverReport(4,clientIP,clientPortNum)
                self.sendClientNotice(2,self.connections,nick)
                c.close()
                break
            
            requestMsg = str(requestMsg,'utf-8')                        #리퀘스트 메시지 변환 및 해석
            requestMsg = requestMsg.split(self.checkMark)
            requestHeader = requestMsg[0]
            
            if requestHeader == 'nickset':                            #닉네임 설정
                nick = requestMsg[1]
                self.clientNickList[int(clientPortNum)] = nick
                self.clientSocketList[nick] = clientPortNum
                self.serverReport(5,clientIP,clientPortNum,nick)
                self.sendClientNotice(1,self.connections,nick)
                
                
            elif requestHeader == 'msgToAll':                         #전체 채팅
                msg = requestMsg[1]
                self.sendMsgAll(self.connections,nick,msg)

            elif requestHeader == 'whisper':                          #귓속말
                sender = nick
                target = requestMsg[1]
                msg = requestMsg[2]
                self.whisper(sender,target,msg,c)
                
            



    def sendMsgAll(self,connections,nick,msg):                  #전체 채팅 메소드
        responseHeader = "msgToAll"
        responseMsg = responseHeader + self.checkMark + nick + self.checkMark + msg
        for connection in connections:
                    connection.send(bytes(responseMsg,'utf-8'))

                    

    def whisper(self,sender,target,msg,c):                      #귓속말 메소드
        try:
            targetSocketNum = self.clientSocketList[target]
        except:                                                 #귓속말 상대를 잘못 입력하였을 경우
            self.sendClientNotice(3,self.connections,None,c)
            return
        
        for target in self.connections:                         #귓속말 상대의 소켓 객체 검색
            tmpTarget = str(target).split(', ')[7][:5]
            if tmpTarget == targetSocketNum:
                break
        responseHeader = "whisper"
        responseMsg = responseHeader + self.checkMark + sender + self.checkMark + msg
        target.send(bytes(responseMsg,'utf-8'))
        self.sendClientNotice(4,self.connections,None,c)
            

    def sendClientNotice(self,Type,connections,nick = None,c = None):       #클라이언트에게 알림 전송 메소드
        if Type == 1:                                                       #채팅방 입장 알림
            responseHeader = "noticeJoin"
            justJoined = nick
            responseMsg = responseHeader + self.checkMark + justJoined
            for connection in connections:
                    connection.send(bytes(responseMsg,'utf-8'))
        elif Type == 2:
            responseHeader = "noticeExit"                                   #채팅방 퇴장 알림
            justExit = nick
            responseMsg = responseHeader + self.checkMark + justExit
            for connection in connections:
                    connection.send(bytes(responseMsg,'utf-8'))
        elif Type == 3:                                                     #귓속말 상대 없음 알림
            responseHeader = "noticeWhisperError"
            responseMsg = responseHeader + self.checkMark
            c.send(bytes(responseMsg,'utf-8'))
        elif Type == 4:                                                     #귓속말 전달 완료 알림
            responseHeader = "noticeWhisperSuccess"
            responseMsg = responseHeader + self.checkMark
            c.send(bytes(responseMsg,'utf-8'))
            

            
    def serverReport(self,Type,clientIP = None,clientPortNum = None,nick = None):     #관리자 알림 기능
        print("----------Server report---------")
        if Type == 1:
            print("##코코아톡 서버가 구동중입니다##")
            
        elif Type == 2:
            print("접속 IP : " + clientIP + "  ###  포트번호 :" + clientPortNum, " 가 접속하였습니다.")
            
        elif Type == 3:
            print("접속 IP : " + clientIP + "  ###  포트번호 :" + clientPortNum + "  ###  닉네임 : " + nick + " 가 연결을 종료하였습니다.")
            
        elif Type == 4:
            print("접속 IP : " + clientIP + "  ###  포트번호 :" + clientPortNum, " 가 연결을 종료하였습니다.")

        elif Type == 5:
            print("접속 IP : " + clientIP + "  ###  포트번호 :" + clientPortNum, " 가 닉네임을 " + nick + "으로 설정하였습니다.")

        print("현재 접속자 수 : " + str(len(self.clientNickList)))
        print("현재 접속자 리스트 : ",end="")
        print(self.clientNickList)
        print()

            
            
            
            

            


class Client:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    isNickSet = False
    checkMark = '@'
    
    def __init__(self,address):
        self.sock.connect((address,4967))

    def run(self):                          #메인 쓰레드

        iThread = threading.Thread(target=self.chat)
        iThread.daemon = True
        iThread.start()
        msgBlank = "\t\t\t\t"
        noticeBlank = "\t\t\t\t\t\t\t\t  "

        while True:
            if self.isNickSet == False:       #클라이언트가 처음 접속하였을 때 서버에게 닉네임 전송
                self.setNick()
                self.setChatWindow()
            try:
                responseMsg = self.sock.recv(1024)
            except:
                break
            responseMsg = str(responseMsg,'utf-8')
            responseMsg = responseMsg.split(self.checkMark)
            responseHeader = responseMsg[0]

            if responseHeader == 'msgToAll':
                sender = responseMsg[1]
                msg = responseMsg[2]
                print(msgBlank + sender + ": " + msg + "\n")
                
            elif responseHeader == 'whisper':
                sender = responseMsg[1]
                msg = responseMsg[2]
                print(msgBlank + sender + "님으로부터의 귓속말 : " + msg)

            elif responseHeader == 'noticeWhisperError':
                print(noticeBlank + "입력하신 상대가 채팅방에 없습니다.")

            elif responseHeader == 'noticeWhisperSuccess':
                print(noticeBlank + "귓속말을 전달하였습니다.")
                
            elif responseHeader == 'noticeJoin':
                justJoined = responseMsg[1]
                print(noticeBlank + justJoined + "님이 채팅방에 입장했습니다.")
                
            elif responseHeader == 'noticeExit':
                justExit = responseMsg[1]
                print(noticeBlank + justExit + "님이 채팅방에서 퇴장했습니다.")
                

            
    def chat(self):                         #클라이언트로부터 입력받는 쓰레드
        while True:
            if self.isNickSet == True:        #클라이언트 기능-1. 닉네임 설정
                time.sleep(0.2)
                keyboard = input("")
                if keyboard == '/w':            # 클라이언트 기능-2. 귓속말
                    self.whisper()
                else:                           # 클라이언트 기능-3. 전체 채팅
                    self.msgToAll(keyboard)

                
    def whisper(self):                          #귓속말 메소드
        requestHeader = 'whisper'
        target = input("상대를 입력하세요 : ")
        msg = input("내용을 입력하세요 : ")
        requestMsg = requestHeader + self.checkMark + target + self.checkMark + msg
        self.sock.send(bytes(requestMsg,'utf-8'))

    def msgToAll(self,keyboard):                #전체 채팅 메소드
        requestHeader = 'msgToAll'
        msg = keyboard
        requestMsg = requestHeader + self.checkMark + msg
        self.sock.send(bytes(requestMsg,'utf-8'))
        


    def setNick(self):                         #닉네임 설정 메소드
        nick = input("닉네임을 입력하세요 : ")
        requestHeader = 'nickset'
        requestMsg = requestHeader + self.checkMark + nick
        self.sock.send(bytes(requestMsg,'utf-8'))
        self.isNickSet = True


    def setChatWindow(self):            #채팅창 세팅 메소드
        print("keyboard------------------------message---------------------------Notice---------------------------")







if (len(sys.argv) > 1):                         #접속할 서버ip를 매개변수로 전달하면 클라이언트
    client = Client(sys.argv[1])
    client.run()
else:                                           #전달하지 않으면 서버
    server = Server()
    server.run()
            
