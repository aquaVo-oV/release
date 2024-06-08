import tkinter
import pathlib
import os

from trashbox.roleinfoclass import RoleInfo
from trashbox.addrole_screen import AddRoleScreen

class RoleList(tkinter.Frame):
    def __init__(
            self,
            parent : tkinter.Misc,
            directory: pathlib.Path
            ):
        tkinter.Frame.__init__(
            self,
            parent,
            )

        if not directory.is_dir():
            os.makedirs(directory, exist_ok= True)

        self.fn_name = "name.txt"
        self.fn_camp = "camp.txt"
        self.fn_info = "info.txt"
        self.fn_wincon = "wincon.txt"
        self.button_attr_fmt = "role_button{}"
        self.role_dn_fmt = "role{}"
        self.x_max_pos = 10


        self.parent = parent
        self.directory = directory
        self.info_list = self._load_files()
        for (i, info) in enumerate(self.info_list):
            self._addButton(text= info.role_name, pos= i)
        
        self.rolebox_add_button = tkinter.Button(
            parent,
            text= "追加",
            command= self._add_role_button_cmd,
            )
        self.rolebox_add_button.grid(row= 0, column= 0, pady= 20)
        
    def _add_role_button_cmd(self):
        self.info_list.append(RoleInfo(name="new_role"))
        self._addButton(self.info_list[-1].role_name, len(self.info_list) - 1)

    def _addButton(self, text: str, pos: int):
        setattr(
            self,
            self.button_attr_fmt.format(pos),
            tkinter.Button(
                self.parent,
                text= text,
                command= self.__get_open_command(pos),
                height= 1,
                width= 10,
                )
            )
        button: tkinter.Button = getattr(self, self.button_attr_fmt.format(pos))
        p_row = pos // self.x_max_pos 
        p_col = pos % self.x_max_pos
        button.grid(row= p_row + 1, column= p_col)
        
    def _load_files(self) -> list[RoleInfo]:
        info_list = []
        for path in pathlib.Path(self.directory).iterdir():
            if path.is_dir():
                info = RoleInfo()
                with open(path / self.fn_name) as f:
                    info.role_name = f.read()
                with open(path / self.fn_camp) as f:
                    info.role_camp = f.read()
                with open(path / self.fn_info) as f:
                    info.role_info = f.read()
                with open(path / self.fn_wincon) as f:
                    info.wincon = f.read()
                info_list.append(info)

        return info_list
    
    def save_files(self, pos: int, name: str, camp: str, info: str, wincon: str):

        dir_path = pathlib.Path(self.directory) / self.role_dn_fmt.format(pos)
        os.makedirs(dir_path, exist_ok= True)

        with open(dir_path / self.fn_name, mode= "w") as f:
            f.writelines(name)
        with open(dir_path / self.fn_camp, mode= "w") as f:
            f.writelines(camp)
        with open(dir_path / self.fn_info, mode= "w") as f:
            f.writelines(info)
        with open(dir_path / self.fn_wincon, mode= "w") as f:
            f.writelines(wincon)

    def __get_submit_command(self, pos: int):
        
        def submit_command(name: str, camp: str, info: str, wincon: str) -> None:

            ri = RoleInfo(name, camp, info, wincon)
            self.save_files(pos, name, camp, info, wincon)
            change_button : tkinter.Button = getattr(self, self.button_attr_fmt.format(pos))
            change_button["text"] = name
            self.info_list[pos] = ri
            self.parent.grab_release()
            
        return submit_command
    
    def __get_open_command(self, pos: int):
        
        def open_add_screen() -> None:
            #新規ウィンドウを表示
            window = tkinter.Toplevel()
            #親ウィンドウを操作不可にする
            self.parent.grab_set()
            AddRoleScreen(
                window,
                role_label= "役職",
                camp_label= "陣営",
                info_label= "情報",
                wincon_label= "勝利条件",
                submit_label= "保存",
                initial= self.info_list[pos],
                submit_command= self.__get_submit_command(pos)
            )

        return open_add_screen
            

import ctypes

if __name__ == "__main__":
    
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(True)
    except:
        pass

    root = tkinter.Tk()
    RoleList(root, pathlib.Path("./") / "role_text")
    root.mainloop()
