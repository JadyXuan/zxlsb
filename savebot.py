from watchdog.observers import Observer
from watchdog.events import *
import tkinter as tk
from tkinter import filedialog
import time
import threading
import re
import sys, os


SAVEPATH = ""
WATCHPATH = ""
SAVEDIC = ""


def save_dic_choose():
    global SAVEDIC
    while True:
        dic_name = time.strftime("%y-%m-%d")
        SAVEDIC = dic_name + "/"
        if not os.path.exists(SAVEPATH + SAVEDIC):
            os.makedirs(SAVEPATH + SAVEDIC)
        time.sleep(600)


class WechatImageDecoder:
    def __init__(self, dat_file):
        dat_file = dat_file.lower()

        decoder = self._match_decoder(dat_file)
        decoder(dat_file)

    def _match_decoder(self, dat_file):
        decoders = {
            r'.+\.dat$': self._decode_pc_dat,
            r'cache\.data\.\d+$': self._decode_android_dat,
            None: self._decode_unknown_dat,
        }

        for k, v in decoders.items():
            if k is not None and re.match(k, dat_file):
                return v
        return decoders[None]

    def _decode_pc_dat(self, dat_file):

        def do_magic(header_code, buf):
            return header_code ^ list(buf)[0] if buf else 0x00

        def decode(magic, buf):
            return bytearray([b ^ magic for b in list(buf)])

        def guess_encoding(buf):
            headers = {
                'jpg': (0xff, 0xd8),
                'png': (0x89, 0x50),
                'gif': (0x47, 0x49),
            }
            for encoding in headers:
                header_code, check_code = headers[encoding]
                magic = do_magic(header_code, buf)
                _, code = decode(magic, buf[:2])
                if check_code == code:
                    return (encoding, magic)
            print('Decode failed')
            sys.exit(1)

        file_name = dat_file.split("/")[-1]
        with open(dat_file, 'rb') as f:
            buf = bytearray(f.read())
        file_type, magic = guess_encoding(buf)

        img_file = SAVEPATH + SAVEDIC + str(re.sub(r'.dat$', '.' + file_type, file_name))
        print(img_file)

        with open(img_file, 'wb') as f:
            new_buf = decode(magic, buf)
            f.write(new_buf)

    def _decode_android_dat(self, dat_file):
        with open(dat_file, 'rb') as f:
            buf = f.read()

        last_index = 0
        for i, m in enumerate(re.finditer(b'\xff\xd8\xff\xe0\x00\x10\x4a\x46', buf)):
            if m.start() == 0:
                continue


            imgfile = '%s_%d.jpg' % (dat_file, i)
            with open(imgfile, 'wb') as f:
                f.write(buf[last_index: m.start()])
            last_index = m.start()

    def _decode_unknown_dat(self, dat_file):
        raise Exception('Unknown file type')

class Watcher(FileSystemEventHandler):
    def __init__(self):
        FileSystemEventHandler.__init__(self)

    def on_created(self, event):
        if event.is_directory:
            print("create directory:" + str(event.src_path))
        else:
            srcpath = str(event.src_path)
            srcpath = srcpath.replace("\\", "/")
            temp_path = srcpath.split(".dat")[0]
            src_path = temp_path + ".dat"
            if "Image" in src_path and "rst" not in src_path:  # ??????????????????rst????????????????????????????????????????????????
                print("???????????????:" + srcpath)
                time.sleep(1)
                WechatImageDecoder(src_path)
                print("??????"+str(src_path))
        pass


class SaveUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("????????????????????????")
        self.root.geometry("333x200")
        self.save_var = tk.StringVar()
        self.watch_var = tk.StringVar()
        with open('config.ini', 'a+') as config:
            config.seek(0, 0)
            con_path = config.readline()
            if con_path:
                self.save_var.set(con_path.strip())
                self.watch_var.set(config.readline())
        text1 = tk.Label(self.root, text='??????????????????').place(x=10, y=50)
        text2 = tk.Label(self.root, text='??????????????????').place(x=10, y=100)
        submit_button = tk.Button(self.root, text="??????", command=self.submit).place(x=150, y=160)
        save_path_button = tk.Button(self.root, text="??????", command=self.save_path_choose).place(x=250, y=50)
        watch_path_button = tk.Button(self.root, text="??????", command=self.watch_path_choose).place(x=250, y=100)
        save_entry = tk.Entry(self.root, textvariable=self.save_var)
        save_entry.place(x=100, y=50)
        watch_entry = tk.Entry(self.root, textvariable=self.watch_var)
        watch_entry.place(x=100, y=100)

    def loop(self):
        self.root.mainloop()

    def submit(self):
        global SAVEPATH
        global WATCHPATH
        SAVEPATH = self.save_var.get() + "/"
        WATCHPATH = self.watch_var.get()
        with open('config.ini', 'w') as config:
            config.write(self.save_var.get())
            config.write('\n')
            config.write(self.watch_var.get())
        self.root.destroy()
        pass

    def path_choose(self):
        path = filedialog.askdirectory(title="???????????????")
        return path

    def save_path_choose(self):
        path = self.path_choose()
        self.save_var.set(path)
        print("save path ??????:" + path)


    def watch_path_choose(self):
        path = self.path_choose()
        self.watch_var.set(path)
        print("watch path ??????:" + path)


if __name__ == "__main__":
    daytime_thread = threading.Thread(target=save_dic_choose)
    ui = SaveUI()
    ui.loop()
    print("???????????????????????? " + SAVEPATH)
    print("?????????????????????????????? " + WATCHPATH)
    path = WATCHPATH
    observer = Observer()
    event_handler = Watcher()
    observer.schedule(event_handler, path, True)

    daytime_thread.start()
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()