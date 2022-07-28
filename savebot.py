from watchdog.observers import Observer
from watchdog.events import *
import tkinter as tk
from tkinter import filedialog
import time
import re
import sys


SAVEPATH = ""
WATCHPATH = ""

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

        img_file = SAVEPATH + str(re.sub(r'.dat$', '.' + file_type, file_name))
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
            if "Image" in src_path and "rst" not in src_path:
                print("检测到图片:" + srcpath)
                time.sleep(1)
                WechatImageDecoder(src_path)
                print("存储"+str(src_path))
        pass


def submit():
    global SAVEPATH
    global WATCHPATH
    SAVEPATH = save_var.get() + "/"
    WATCHPATH = watch_var.get()
    root.destroy()
    pass

def path_choose():
    path = filedialog.askdirectory(title="请选择路径")
    return path

def save_path_choose():
    path = path_choose()
    save_var.set(path)
    print("save path 指定:" + path)

def watch_path_choose():
    path = path_choose()
    watch_var.set(path)
    print("watch path 指定:" + path)

if __name__ == "__main__":
    root = tk.Tk()
    root.title("微信自动保存图片")
    root.geometry("333x200")
    save_var = tk.StringVar()
    watch_var = tk.StringVar()
    with open('config.ini', 'a+') as config:
        config.seek(0, 0)
        con_path = config.readline()
        if con_path:
            save_var.set(con_path.strip())
            watch_var.set(config.readline())

    text1 = tk.Label(root, text='选择保存目录').place(x=10, y=50)
    text2 = tk.Label(root, text='微信监控目录').place(x=10, y=100)
    submit_button = tk.Button(root, text="确定", command = submit).place(x=150, y=160)
    save_path_button = tk.Button(root, text="选择", command=save_path_choose).place(x=250, y=50)
    watch_path_button = tk.Button(root, text="选择", command=watch_path_choose).place(x=250, y=100)
    save_entry = tk.Entry(root, textvariable=save_var)
    save_entry.place(x=100, y=50)
    watch_entry = tk.Entry(root, textvariable=watch_var)
    watch_entry.place(x=100, y=100)
    root.mainloop()
    with open('config.ini', 'w') as config:
        config.write(save_var.get())
        config.write('\n')
        config.write(watch_var.get())
    print("图片保存文件夹： " + SAVEPATH)
    print("微信聊天图片文件夹： " + WATCHPATH)
    path = WATCHPATH
    observer = Observer()
    event_handler = Watcher()
    observer.schedule(event_handler, path, True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()