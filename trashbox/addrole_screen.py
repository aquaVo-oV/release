import tkinter
import typing

from trashbox.roleinfoclass import RoleInfo

class AddRoleScreen(tkinter.Frame):
    
    def __init__(
            self,
            parent: tkinter.Misc,
            role_label: str,
            camp_label: str,
            info_label: str,
            wincon_label: str,
            submit_label: str,
            submit_command: typing.Callable[[str, str, str, str], None],
            initial: RoleInfo = RoleInfo(),
            ):
        tkinter.Frame.__init__(
            self,
            parent,
            padx= 20,
            pady= 600,
            )

        self.parent = parent

        self.role_label = tkinter.Label(parent, text= role_label)
        self.role_label.grid(row= 0, column= 0)
        
        self.camp_label = tkinter.Label(parent, text= camp_label)
        self.camp_label.grid(row= 1, column= 0)

        self.info_label = tkinter.Label(parent, text= info_label)
        self.info_label.grid(row= 2, column= 0)

        self.wincon_label = tkinter.Label(parent, text= wincon_label)
        self.wincon_label.grid(row= 3, column= 0)

        self.name_entry = tkinter.Entry(parent)
        self.name_entry.insert(tkinter.END, initial.role_name)
        self.name_entry.grid(row= 0, column= 1)

        self.camp_entry = tkinter.Entry(parent)
        self.camp_entry.insert(tkinter.END, initial.role_camp)
        self.camp_entry.grid(row= 1, column= 1)

        self.info_text = tkinter.Text(parent, height= 5)
        self.info_text.insert(tkinter.END, initial.role_info)
        self.info_text.grid(row= 2, column= 1)

        self.wincon_text = tkinter.Text(parent, height= 5)
        self.wincon_text.insert(tkinter.END, initial.wincon)
        self.wincon_text.grid(row= 3, column= 1)

        self.submit_button = tkinter.Button(parent, text= submit_label, command= self.submit)
        self.submit_button.grid(row= 4, column= 1)

        self.submit_command = submit_command

    def submit(self):
        self.submit_command(
            self.name_entry.get(),
            self.camp_entry.get(),
            self.info_text.get("0.0", "end").rstrip(),
            self.wincon_text.get("0.0", "end").rstrip()
            )
        self.parent.destroy()
        
import ctypes

if __name__ == "__main__":
    
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(True)
    except:
        pass

    def submit_command(role: str, camp: str, info: str, wincon: str):
        print(role)
        print(camp)
        print(info)
        print(wincon)
        print("保存しました")

    root = tkinter.Tk()
    AddRoleScreen(
        root,
        role_label= "役職",
        camp_label= "陣営",
        info_label= "情報",
        wincon_label= "勝利条件",
        submit_label= "保存",
        submit_command= submit_command
        )
    root.mainloop()


