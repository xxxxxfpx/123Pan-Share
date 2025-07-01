import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
import threading
from PIL import Image, ImageTk
import io
import pyperclip

# 添加当前目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import Pan123
from Share.sign import panToSign, signToPan

class ProgressFrame(ttk.Frame):
    """进度条框架组件"""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        # 创建进度条
        self.progress = ttk.Progressbar(self, orient=tk.HORIZONTAL, length=300, mode='determinate')
        self.progress.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        # 创建文件计数标签
        self.file_count_label = ttk.Label(self, text="处理文件: 0/0")
        self.file_count_label.pack(side=tk.TOP, padx=5)
        
        # 默认隐藏
        self.pack_forget()
    
    def show(self):
        """显示进度条"""
        self.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
    
    def hide(self):
        """隐藏进度条"""
        self.pack_forget()
    
    def reset(self):
        """重置进度条"""
        self.progress['value'] = 0
        self.file_count_label.config(text="处理文件: 0/0")
    
    def update_progress(self, value, max_value=100):
        """更新进度条值"""
        if max_value > 0:
            percentage = (value / max_value) * 100
            self.progress['value'] = percentage
    
    def update_file_count(self, handled_files, total_files):
        """更新文件计数"""
        self.file_count_label.config(text=f"处理文件: {handled_files}/{total_files}")

class Pan123ShareApp(tk.Tk):
    def __init__(self):
        super().__init__()
        
        # 设置窗口标题和大小
        self.title("123云盘分享工具")
        self.geometry("800x600")
        self.minsize(800, 600)
        
        # 绑定关闭事件
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 创建状态栏
        self.status_bar = ttk.Label(self, text="就绪", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 创建标签页控件
        self.tab_control = ttk.Notebook(self)
        
        # 创建各个标签页
        self.login_tab = ttk.Frame(self.tab_control)
        self.share_tab = ttk.Frame(self.tab_control)
        self.receive_tab = ttk.Frame(self.tab_control)
        self.history_tab = ttk.Frame(self.tab_control)
        
        # 添加标签页到控件
        self.tab_control.add(self.login_tab, text="登录")
        self.tab_control.add(self.share_tab, text="创建分享", state="disabled")
        self.tab_control.add(self.receive_tab, text="接收分享", state="disabled")

        
        # 显示标签页控件
        self.tab_control.pack(expand=1, fill="both")
        
        # 初始化各个标签页的内容
        self.init_login_tab()
        self.init_share_tab()
        self.init_receive_tab()

        
        # 初始化Pan123实例
        self.pan = None
        
        # 尝试自动加载账号信息
        self.try_load_account()
    
    def try_load_account(self):
        """尝试从配置文件加载账号信息"""
        try:
            config_path = os.path.join(os.path.expanduser("~"), ".123pan", "account.txt")
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    if len(lines) >= 2:
                        username = lines[0].strip()
                        password = lines[1].strip()
                        
                        # 填充到登录表单
                        if username and password:
                            self.username_entry.delete(0, tk.END)
                            self.username_entry.insert(0, username)
                            self.password_entry.delete(0, tk.END)
                            self.password_entry.insert(0, password)
                            self.remember_var.set(True)
                            
                            # 自动登录
                            self.after(500, self.login)
        except Exception as e:
            print(f"加载账号信息失败: {e}")
    
    def init_login_tab(self):
        """初始化登录标签页"""
        # 创建登录框架
        login_frame = ttk.Frame(self.login_tab, padding=(50, 50))
        login_frame.pack(fill=tk.NONE, expand=True, anchor=tk.CENTER)
        
        # 创建标题标签
        title_label = ttk.Label(login_frame, text="123云盘登录", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # 创建用户名标签和输入框
        username_label = ttk.Label(login_frame, text="用户名:", font=('Arial', 10))
        username_label.grid(row=1, column=0, sticky=tk.W, pady=5)
        
        self.username_entry = ttk.Entry(login_frame, width=30, font=('Arial', 10))
        self.username_entry.grid(row=1, column=1, pady=5)
        
        # 创建密码标签和输入框
        password_label = ttk.Label(login_frame, text="密码:", font=('Arial', 10))
        password_label.grid(row=2, column=0, sticky=tk.W, pady=5)
        
        self.password_entry = ttk.Entry(login_frame, width=30, show="*", font=('Arial', 10))
        self.password_entry.grid(row=2, column=1, pady=5)
        
        # 创建记住账号复选框
        self.remember_var = tk.BooleanVar(value=False)
        remember_check = ttk.Checkbutton(login_frame, text="记住账号", variable=self.remember_var)
        remember_check.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # 创建按钮框架
        button_frame = ttk.Frame(login_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=15)
        
        # 创建登录按钮
        self.login_button = ttk.Button(button_frame, text="登录", command=self.login, width=15)
        self.login_button.pack(side=tk.LEFT, padx=10)
        # 创建退出登录按钮
        self.logout_button = tk.Button(button_frame, text="退出登录", command=self.logout, bg='red', fg='white', font=('Arial', 12, 'bold'), width=12, height=1, bd=2, relief=tk.RAISED, borderwidth=1, highlightthickness=1, highlightbackground='yellow')
        self.logout_button.pack(side=tk.LEFT, padx=10)
        self.logout_button.pack_forget()  # 初始隐藏退出按钮
        

    def init_share_tab(self):
        """初始化创建分享标签页"""
        # 创建分享框架
        share_frame = ttk.Frame(self.share_tab, padding="20")
        share_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建分享内容输入框
        content_frame = ttk.Frame(share_frame)
        content_frame.pack(fill=tk.X, pady=10)
        
        content_label = ttk.Label(content_frame, text="分享内容:")
        content_label.pack(side=tk.LEFT, padx=5)
        
        self.share_content_entry = ttk.Entry(content_frame)
        placeholder = "示例：/分享目录/影视资源(目录路径) 或 241234(目录ID)"
        self.share_content_entry.insert(0, placeholder)
        self.share_content_entry.bind("<FocusIn>", lambda e: self.on_entry_focus_in(e, self.share_content_entry, placeholder))
        self.share_content_entry.bind("<FocusOut>", lambda e: self.on_entry_focus_out(e, self.share_content_entry, placeholder))
        self.share_content_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        load_button = ttk.Button(share_frame, text="预加载分享内容", command=self.load_share_name, style="Secondary.TButton")
        load_button.pack(anchor=tk.E, pady=5)
        
        # 创建分享名称输入框
        name_frame = ttk.Frame(share_frame)
        name_frame.pack(fill=tk.X, pady=10)
        
        name_label = ttk.Label(name_frame, text="分享名称:")
        name_label.pack(side=tk.LEFT, padx=5)
        
        self.share_name_entry = ttk.Entry(name_frame)
        self.share_name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # 创建分享按钮
        self.create_share_button = ttk.Button(share_frame, text="创建分享", command=self.create_share)
        self.create_share_button.pack(pady=10)
        
        # 创建进度条框架
        self.share_progress_frame = ProgressFrame(share_frame)
        
        # 创建分享结果框架
        result_frame = ttk.LabelFrame(share_frame, text="分享结果")
        result_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 创建分享链接显示框
        self.share_result = tk.Text(result_frame, height=5, state=tk.DISABLED)
        self.share_result.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建滚动条
        result_scrollbar = ttk.Scrollbar(result_frame, command=self.share_result.yview)
        result_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        self.share_result.config(yscrollcommand=result_scrollbar.set)
        
        # 创建按钮框架
        button_frame = ttk.Frame(share_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        # 创建复制按钮
        copy_button = ttk.Button(button_frame, text="复制链接", command=self.copy_share_link)
        copy_button.pack(side=tk.LEFT, padx=5)
        
        # 创建清除按钮
        clear_button = ttk.Button(button_frame, text="清除结果", command=self.clear_share_result)
        clear_button.pack(side=tk.LEFT, padx=5)
    
    def init_receive_tab(self):
        """初始化接收分享标签页"""
        # 创建接收框架
        receive_frame = ttk.Frame(self.receive_tab, padding="20")
        receive_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建分享链接输入框架
        link_frame = ttk.Frame(receive_frame)
        link_frame.pack(fill=tk.X, pady=10)
        
        link_label = ttk.Label(link_frame, text="分享链接:")
        link_label.pack(side=tk.LEFT, padx=5)
        
        self.share_link_entry = ttk.Entry(link_frame)
        self.share_link_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        paste_button = ttk.Button(link_frame, text="粘贴", command=self.paste_from_clipboard, width=8)
        paste_button.pack(side=tk.LEFT, padx=5)
        
        # 创建保存位置选择框架
        save_frame = ttk.Frame(receive_frame)
        save_frame.pack(fill=tk.X, pady=10)
        
        save_label = ttk.Label(save_frame, text="保存位置:")
        save_label.pack(side=tk.LEFT, padx=5)
        
        self.save_type = tk.StringVar(value="root")
        self.save_type.trace_add("write", self.on_save_type_change)
        
        root_radio = ttk.Radiobutton(save_frame, text="根目录", variable=self.save_type, value="root")
        root_radio.pack(side=tk.LEFT, padx=10)
        
        custom_radio = ttk.Radiobutton(save_frame, text="自定义", variable=self.save_type, value="custom")
        custom_radio.pack(side=tk.LEFT, padx=10)
        
        # 创建自定义路径输入框
        path_frame = ttk.Frame(receive_frame)
        path_frame.pack(fill=tk.X, pady=5)
        
        path_label = ttk.Label(path_frame, text="自定义路径:")
        path_label.pack(side=tk.LEFT, padx=5)
        
        self.custom_path_entry = ttk.Entry(path_frame, state=tk.DISABLED)
        placeholder = "示例： /自定义路径/影视资源/(目录路径) 或 123123(目录ID)"
        self.custom_path_entry.insert(0, placeholder)
        self.custom_path_entry.bind("<FocusIn>", lambda e: self.on_entry_focus_in(e, self.custom_path_entry, placeholder))
        self.custom_path_entry.bind("<FocusOut>", lambda e: self.on_entry_focus_out(e, self.custom_path_entry, placeholder))
        self.custom_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # 创建接收按钮
        self.receive_button = ttk.Button(receive_frame, text="接收分享", command=self.receive_share)
        self.receive_button.pack(pady=10)
        
        # 创建进度条框架
        self.receive_progress_frame = ProgressFrame(receive_frame)
        
        # 创建接收结果框架
        result_frame = ttk.LabelFrame(receive_frame, text="接收结果")
        result_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 创建接收结果显示框
        self.receive_result = tk.Text(result_frame, height=10, state=tk.DISABLED)
        self.receive_result.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建滚动条
        result_scrollbar = ttk.Scrollbar(result_frame, command=self.receive_result.yview)
        result_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        self.receive_result.config(yscrollcommand=result_scrollbar.set)
        
        # 创建清除按钮
        clear_button = ttk.Button(receive_frame, text="清除结果", command=self.clear_receive_result)
        clear_button.pack(anchor=tk.E, pady=5)
    
    
    
    def on_entry_focus_in(self, event, entry, placeholder):
        if entry.get() == placeholder:
            entry.delete(0, tk.END)

    def on_entry_focus_out(self, event, entry, placeholder):
        if not entry.get():
            entry.insert(0, placeholder)
    
    def logout(self):
        """退出登录"""
        # 确认退出
        if messagebox.askyesno("确认退出", "确定要退出登录吗?"):
            # 清除Pan实例
            self.pan = None
            
            # 禁用其他标签页
            self.tab_control.tab(self.share_tab, state="disabled")
            self.tab_control.tab(self.receive_tab, state="disabled")
            
            # 切换到登录标签页
            self.tab_control.select(self.login_tab)
            
            # 隐藏退出登录按钮（使用pack_forget()匹配pack()显示方式）
            self.login_button.pack()
            self.logout_button.pack_forget()
            
            
            # 清除登录表单
            self.username_entry.delete(0, tk.END)
            self.password_entry.delete(0, tk.END)
            self.remember_var.set(False)
            
            # 清除分享标签页内容
            self.share_content_entry.delete(0, tk.END)
            self.share_name_entry.delete(0, tk.END)
            self.share_result.config(state=tk.NORMAL)
            self.share_result.delete(1.0, tk.END)
            self.share_result.config(state=tk.DISABLED)
            
            # 清除接收标签页内容
            self.share_link_entry.delete(0, tk.END)
            self.custom_path_entry.delete(0, tk.END)
            self.receive_result.config(state=tk.NORMAL)
            self.receive_result.delete(1.0, tk.END)
            self.receive_result.config(state=tk.DISABLED)
            
            # 更新状态栏
            self.status_bar.config(text="已退出登录")

    def create_share(self):
        """创建分享"""
        # 获取分享类型和内容

        content = self.share_content_entry.get().strip()
        share_name = self.share_name_entry.get().strip()
        
        # 验证输入
        if not content:
            messagebox.showerror("错误", "请输入分享内容")
            return
        
        if not share_name:
            messagebox.showerror("错误", "请输入分享名称")
            return
        
        # 禁用创建按钮
        self.create_share_button.config(state=tk.DISABLED)
        
        # 重置并显示进度条
        self.share_progress_frame.reset()
        self.share_progress_frame.show()
        
        # 更新状态
        self.update_status("正在创建分享...")
        
        # 在新线程中执行分享操作
        threading.Thread(target=self._create_share_thread, args=(content, share_name)).start()
    
    def _create_share_thread(self, content, share_name):
        """在线程中执行创建分享操作"""
        try:
            # 定义进度回调函数
            def progress_callback(now_info, handle_file=None, allfile=None):
                # 在主线程中更新进度
                self.after(10, self._update_share_progress, now_info, handle_file, allfile)
            
            # 创建分享
            # 检查是否已通过加载按钮获取迭代器
            if not hasattr(self, 'sign_iter') or self.sign_iter is None:
                messagebox.showerror("错误", "请先点击'加载'按钮获取默认名称")
                return
            
            # 发送用户自定义名称并获取分享链接
            share_link = self.sign_iter.send(share_name)
            
            # 重置迭代器
            self.sign_iter = None
            
            # 在主线程中更新UI
            self.after(10, lambda: self._share_success(share_link))
            
        except Exception as e:
            # 分享失败，在主线程中显示错误
            self.after(10, lambda e=e: self._share_failed(str(e)))
        finally:
            # 在主线程中恢复按钮状态
            self.after(10, lambda: self.create_share_button.config(state=tk.NORMAL))
    
    def _update_share_progress(self, now_info, handle_file=None, all_file=None):
        """更新分享进度"""
        # 更新状态栏
        self.update_status(f"创建分享中: {now_info}")
        
        # 更新进度条（如果有文件计数）
        if handle_file is not None and all_file is not None:
            self.share_progress_frame.update_file_count(handle_file, all_file)
            self.share_progress_frame.update_progress(handle_file, all_file)
    
    def _share_success(self, share_link):
        """分享成功处理"""
        # 更新状态栏
        self.update_status("分享创建成功")
        
        # 隐藏进度条
        self.share_progress_frame.hide()
        
        # 显示分享链接
        self.share_result.config(state=tk.NORMAL)
        self.share_result.delete(1.0, tk.END)
        self.share_result.insert(tk.END, share_link)
        self.share_result.config(state=tk.DISABLED)
        
        # 显示成功消息
        messagebox.showinfo("成功", "分享创建成功")
        

    
    def _share_failed(self, error_msg):
        """分享失败处理"""
        # 更新状态栏
        self.update_status(f"分享创建失败: {error_msg}")
        
        # 隐藏进度条
        self.share_progress_frame.hide()
        
        # 显示错误消息
        messagebox.showerror("错误", f"创建分享失败: {error_msg}")
    
    def receive_share(self):
        """接收分享"""
        # 获取分享链接
        share_link = self.share_link_entry.get().strip()
        if not share_link:
            messagebox.showerror("错误", "请输入分享链接")
            return
        
        # 获取保存位置
        save_type = self.save_type.get()
        save_location = 0  # 默认为根目录
        
        if save_type == "custom":
            custom_path = self.custom_path_entry.get().strip()
            if not custom_path:
                messagebox.showerror("错误", "请输入自定义保存位置")
                return
            
            # 尝试将自定义位置解析为ID或路径
            try:
                # 检查是否为数字ID
                save_location = int(custom_path)
            except ValueError:
                # 不是数字，视为路径
                save_location = custom_path
        
        # 禁用接收按钮
        self.receive_button.config(state=tk.DISABLED)
        
        # 重置并显示进度条
        self.receive_progress_frame.reset()
        self.receive_progress_frame.show()
        
        # 更新状态
        self.update_status("正在接收分享...")
        
        # 在新线程中执行接收操作
        threading.Thread(target=self._receive_share_thread, args=(share_link, save_location)).start()

    def _receive_share_thread(self, share_link, save_location):
        """在线程中执行接收分享操作"""
        try:
            # 定义进度回调函数
            def progress_callback(now_info, handle_file=None, all_file=None):
                # 在主线程中更新进度
                self.after(10, lambda: self._update_receive_progress(now_info, handle_file, all_file))
            
            # 接收分享
            result = signToPan(self.pan, share_link, save_location, progress_callback)
            
            # 在主线程中更新UI
            self.after(10, lambda: self._receive_success(result))
            
        except Exception as e:
            # 接收失败，在主线程中显示错误
            self.after(10, lambda e=e: self._receive_failed(str(e)))
        finally:
            # 在主线程中恢复按钮状态
            self.after(10, lambda: self.receive_button.config(state=tk.NORMAL))

    def _update_receive_progress(self, now_info, handle_file, all_file):
        """更新接收进度"""
        # 更新状态栏
        self.update_status(f"接收分享中: {now_info}")
        
        # 更新文件计数（如果有）
        if handle_file is not None and all_file is not None:
            self.receive_progress_frame.update_file_count(handle_file, all_file)
            self.receive_progress_frame.update_progress(handle_file, all_file)
        
        # 更新接收结果文本框
        self.receive_result.config(state=tk.NORMAL)
        self.receive_result.insert(tk.END, f"{now_info}\n")
        self.receive_result.see(tk.END)  # 滚动到底部
        self.receive_result.config(state=tk.DISABLED)

    def _receive_success(self, result):
        """接收成功处理"""
        # 更新状态栏
        self.update_status("分享接收成功")
        
        # 隐藏进度条
        self.receive_progress_frame.hide()
        
        # 显示成功消息
        messagebox.showinfo("成功", "分享文件接收成功")
        


    def _receive_failed(self, error_msg):
        """接收失败处理"""
        # 更新状态栏
        self.update_status(f"分享接收失败: {error_msg}")
        
        # 隐藏进度条
        self.receive_progress_frame.hide()
        
        # 显示错误消息
        messagebox.showerror("错误", f"接收分享失败: {error_msg}")

    def on_closing(self):
        if messagebox.askokcancel("退出", "确定要退出程序吗？"):
            self.destroy()

    def update_status(self, message):
        """更新状态栏消息"""
        self.status_bar.config(text=message)

    def clear_share_result(self):
        """清除分享结果"""
        self.share_result.config(state=tk.NORMAL)
        self.share_result.delete(1.0, tk.END)
        self.share_result.config(state=tk.DISABLED)

    def copy_share_link(self):
        """复制分享链接到剪贴板"""
        share_link = self.share_result.get(1.0, tk.END).strip()
        if share_link:
            pyperclip.copy(share_link)
            messagebox.showinfo("复制成功", "分享链接已复制到剪贴板")
        else:
            messagebox.showwarning("警告", "没有可复制的分享链接")

    def paste_from_clipboard(self):
        """从剪贴板粘贴内容到分享链接输入框"""
        try:
            clipboard_content = pyperclip.paste()
            if clipboard_content:
                self.share_link_entry.delete(0, tk.END)
                self.share_link_entry.insert(0, clipboard_content)
            else:
                messagebox.showwarning("警告", "剪贴板为空")
        except Exception as e:
            messagebox.showerror("错误", f"粘贴失败: {str(e)}")

    def save_account(self, username, password):
        """保存账号信息到配置文件"""
        try:
            import os
            import json
            config_path = os.path.join(os.path.expanduser("~"), ".123pan_config.json")
            with open(config_path, "w") as f:
                json.dump({"username": username, "password": password}, f)
            print(f"账号信息已保存到: {config_path}")
        except Exception as e:
            print(f"保存账号信息失败: {e}")

    def load_share_name(self):
        """通过迭代器加载默认分享名称"""
        content = self.share_content_entry.get().strip()
        if not content:
            messagebox.showerror("错误", "请输入分享内容")
            return
        try:    # 尝试将内容解析为数字ID 
            content = int(content)
        except ValueError:  # 如果不是数字ID，则使用原始内容
            pass
        try:
            # 创建分享迭代器并获取默认名称
            self.sign_iter = panToSign(self.pan, content, call=self._update_share_progress)
            default_name = next(self.sign_iter)

            # 填充默认名称到输入框
            self.share_name_entry.delete(0, tk.END)
            self.share_name_entry.insert(0, default_name)
        except Exception as e:
            messagebox.showerror("错误", f"加载失败: {str(e)}")

    def on_save_type_change(self, *args):
        """保存类型变更时的处理"""
        if self.save_type.get() == "custom":
            self.custom_path_entry.config(state=tk.NORMAL)
        else:
            self.custom_path_entry.delete(0, tk.END)
            self.custom_path_entry.config(state=tk.DISABLED)
            
    def clear_receive_result(self):
        """清除接收结果"""
        self.receive_result.config(state=tk.NORMAL)
        self.receive_result.delete(1.0, tk.END)
        self.receive_result.config(state=tk.DISABLED)

    def login(self):
        """登录账号"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        if not username or not password:
            messagebox.showerror("错误", "用户名和密码不能为空")
            return
        # 保存账号信息
        if self.remember_var.get():
            self.save_account(username, password)
        # 禁用登录按钮
        self.login_button.config(state=tk.DISABLED)
        # 更新状态
        self.update_status("正在登录...")
        # 在新线程中执行登录操作
        threading.Thread(target=self._login_thread, args=(username, password)).start()

    def _login_thread(self, username, password):
        """在线程中执行登录操作"""
        try:
            # 初始化Pan123实例并登录
            self.pan = Pan123.Pan123(username, password)
            self.pan.login()  # 登录失败会报错
            self.after(10, lambda: self.tab_control.tab(1, state="normal"))
            self.after(10, lambda: self.tab_control.tab(2, state="normal"))
            self.after(10, lambda: self.update_status(f"已登录: {username}"))
            self.login_button.pack_forget()
            self.logout_button.pack(side=tk.LEFT, padx=10)
        except Exception as e:
            # 登录失败，在主线程中显示错误
            self.after(10, lambda e=e: messagebox.showerror("错误", f"登录失败: {str(e)}"))
            self.after(10, lambda: self.update_status("登录失败"))
        finally:
            # 在主线程中恢复登录按钮状态
            self.login_button.config(state=tk.NORMAL)

# 添加主函数入口
if __name__ == "__main__":
    app = Pan123ShareApp()
    app.mainloop()