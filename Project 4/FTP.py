from ftplib import FTP, all_errors


class FTPClient:
    def __init__(self):
        self.PASV_flag = 0
        self.ftp = FTP()

    def CONT(self, host, port):
        try:
            resp = self.ftp.connect(host, port)
        except all_errors as e:
            resp = str(e)
        # print(resp)
        return resp

    def USER(self, name="anonymous"):
        try:
            resp = self.ftp.sendcmd("USER " + name)
        except all_errors as e:
            resp = str(e)
        # print(resp)
        return resp

    def PASS(self, passwd=""):
        try:
            resp = self.ftp.sendcmd("PASS " + passwd)
        except all_errors as e:
            resp = str(e)
        # print(resp)
        return resp

    def PWD(self):
        try:
            resp = self.ftp.sendcmd("PWD")
        except all_errors as e:
            resp = str(e)
        # print(resp)
        return resp

    def CWD(self, dir):
        try:
            resp = self.ftp.cwd(dir)
        except all_errors as e:
            resp = str(e)
        # print(resp)
        return resp

    def PASV(self):
        try:
            resp = self.ftp.sendcmd("PASV")
        except all_errors as e:
            resp = str(e)
        return resp

    def LIST(self, path):
        out = []

        try:
            resp = self.ftp.retrlines("LIST" + path, lambda x: out.append(x))
            out.append(resp)
            resp = "\n".join(out)
        except all_errors as e:
            resp = str(e)
        # print(resp)
        return resp

    # Download file
    def RETR(self, remotepath, localpath=""):
        bufsize = 1024

        if localpath != "":
            pass
        else:
            localpath += remotepath

        fp = open(localpath, 'wb')
        try:
            resp = self.ftp.retrbinary('RETR ' + remotepath, fp.write, bufsize)
        except all_errors as e:
            resp = str(e)
        # print(resp)
        fp.close()
        return resp

    # Upload file
    # def uploadFile(self, remotepath, localpath):
    #     bufsize = 1024
    #     fp = open(localpath, 'rb')
    #     self.ftp.storbinary('STOR ' + remotepath, fp, bufsize)
    #     # self.ftp.set_debuglevel(0)
    #     fp.close()

    def QUIT(self):
        try:
            resp = self.ftp.quit()
        except all_errors as e:
            resp = str(e)
        # print(resp)
        return resp
