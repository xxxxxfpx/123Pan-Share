import os
import sys
import tkinter as tk
from tkinter import messagebox

# 添加当前目录到系统路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    try:
        # 尝试导入必要的模块
        import Pan123
        from Share.sign import panToSign, signToPan
        from UI.main import Pan123ShareApp
        
        # 启动应用
        app = Pan123ShareApp()
        app.mainloop()
    except ImportError as e:
        # 如果缺少必要模块，显示错误信息
        root = tk.Tk()
        root.withdraw()  # 隐藏主窗口
        messagebox.showerror("错误", f"无法启动应用：{str(e)}\n\n请确保已安装所有必要的依赖项。")
        root.destroy()
    except Exception as e:
        # 其他错误
        root = tk.Tk()
        root.withdraw()  # 隐藏主窗口
        messagebox.showerror("错误", f"应用启动失败：{str(e)}")
        root.destroy()

if __name__ == "__main__":
    main()