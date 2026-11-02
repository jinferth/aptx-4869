import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext
from PIL import Image, ImageDraw, ImageFont, ImageTk
import os
import threading
import platform
import subprocess # 用于打开文件夹

class ImageProcessorPro:
    def __init__(self, root):
        self.root = root
        self.root.title("APTX-4869 图像情报分析终端 (Intelligence Analysis Terminal)")
        self.root.geometry("950x700")
        
        # === 柯南风格配色 ===
        self.colors = {
            "bg": "#2C3E50",          
            "panel_bg": "#34495E",    
            "card_bg": "#ECF0F1",     
            "text_main": "#2C3E50",   
            "accent_red": "#E74C3C",  
            "accent_blue": "#3498DB", 
            "list_bg": "#000000",     
            "list_fg": "#00FF00",     
            "log_bg": "#212121",      
            "log_fg": "#ECF0F1"       
        }
        
        # 字体配置
        system = platform.system()
        base_font = "Impact" if system == "Windows" else "Arial Black"
        body_font = "Segoe UI" if system == "Windows" else "Helvetica Neue"
        self.fonts = {
            "h1": (base_font, 20),
            "h2": (base_font, 12),
            "body": (body_font, 10),
            "mono": ("Consolas", 9)
        }

        self.root.configure(bg=self.colors["bg"])
        
        # === 变量 ===
        self.source_files = []
        self.target_format = tk.StringVar(value="JPG")
        self.enable_resize = tk.BooleanVar(value=False)
        self.resize_width = tk.IntVar(value=1080)
        self.enable_watermark = tk.BooleanVar(value=False)
        self.watermark_text = tk.StringVar(value="TOP SECRET")
        self.last_open_dir = "/" # 记忆上次打开的路径
        
        self.char_photo = None 

        self._setup_styles()
        self._setup_ui()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure("TFrame", background=self.colors["bg"])
        style.configure("Card.TFrame", background=self.colors["card_bg"], relief="flat")
        
        style.configure("TButton", 
                        font=self.fonts["body"], 
                        background=self.colors["accent_blue"], 
                        foreground="white",
                        borderwidth=0)
        style.map("TButton", background=[('active', "#2980B9")])

        style.configure("Red.TButton", background=self.colors["accent_red"])
        style.map("Red.TButton", background=[('active', "#C0392B")])
        
        style.configure("Horizontal.TProgressbar", background=self.colors["accent_red"], troughcolor="#BDC3C7", thickness=10)

    def _setup_ui(self):
        # 主布局
        main_paned = tk.PanedWindow(self.root, orient="horizontal", bg=self.colors["bg"], sashwidth=4)
        main_paned.pack(fill="both", expand=True, padx=10, pady=10)

        # === 左侧：角色与信息区 ===
        left_panel = tk.Frame(main_paned, bg=self.colors["panel_bg"], width=280)
        main_paned.add(left_panel, minsize=280)
        
        self.canvas_char = tk.Canvas(left_panel, bg=self.colors["panel_bg"], height=380, highlightthickness=0)
        self.canvas_char.pack(fill="x", pady=(20, 10))
        self._draw_default_logo()
        
        ttk.Button(left_panel, text="更换调查员图片...", command=self.load_character_image).pack(pady=5)
        
        tk.Label(left_panel, text="SYSTEM STATUS:", bg=self.colors["panel_bg"], fg="#BDC3C7", font=("Arial", 8, "bold")).pack(anchor="w", padx=15, pady=(30, 5))
        self.lbl_status = tk.Label(left_panel, text="WAITING FOR INPUT...", bg=self.colors["panel_bg"], fg=self.colors["accent_red"], font=("Consolas", 11, "bold"))
        self.lbl_status.pack(anchor="w", padx=15)
        
        self.btn_open_folder = ttk.Button(left_panel, text="📂 打开案件目录", command=self.open_output_folder, state="disabled")
        self.btn_open_folder.pack(pady=20, padx=15, fill="x", side="bottom")

        # === 右侧：操作控制台 ===
        right_panel = tk.Frame(main_paned, bg=self.colors["card_bg"])
        main_paned.add(right_panel, minsize=500)
        
        content = tk.Frame(right_panel, bg=self.colors["card_bg"])
        content.pack(fill="both", expand=True, padx=25, pady=25)

        # 1. 标题
        header = tk.Frame(content, bg=self.colors["card_bg"])
        header.pack(fill="x", pady=(0, 15))
        tk.Label(header, text="CASE FILE: IMAGE PROCESSOR", font=self.fonts["h1"], bg=self.colors["card_bg"], fg=self.colors["text_main"]).pack(side="left")
        tk.Label(header, text="v5.2", bg=self.colors["accent_blue"], fg="white", padx=5, font=("Arial", 8, "bold")).pack(side="left", padx=10)

        # 2. 文件选择与列表 (核心升级区)
        self._create_section_label(content, "01. EVIDENCE LIST (证据清单)")
        
        btn_frame = tk.Frame(content, bg=self.colors["card_bg"])
        btn_frame.pack(fill="x", pady=5)
        
        # 升级按钮文案，突出"预览"功能
        self.btn_add = ttk.Button(btn_frame, text="👁️ 浏览并挑选图片 (推荐)", command=self.select_files)
        self.btn_add.pack(side="left", padx=(0, 5), ipadx=10)
        
        # 保留全选功能，但做区分
        self.btn_folder = ttk.Button(btn_frame, text="📚 导入整个目录 (盲选)", command=self.select_folder)
        self.btn_folder.pack(side="left", padx=(0, 5))
        
        # 增加移除选中功能
        ttk.Button(btn_frame, text="❌ 移除选中项", command=self.remove_selected).pack(side="right")

        # 列表框 + 滚动条 + 右键菜单
        list_frame = tk.Frame(content, bg=self.colors["list_bg"])
        list_frame.pack(fill="x", pady=(0, 15))
        
        self.listbox_files = tk.Listbox(list_frame, height=6, bg=self.colors["list_bg"], fg=self.colors["list_fg"], 
                                        font=self.fonts["mono"], relief="flat", selectbackground="#333333", selectmode="extended")
        self.listbox_files.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox_files.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox_files.config(yscrollcommand=scrollbar.set)

        # 绑定删除键和右键菜单
        self.listbox_files.bind("<Delete>", lambda e: self.remove_selected())
        self.listbox_files.bind("<BackSpace>", lambda e: self.remove_selected())
        self._create_context_menu()

        # 3. 处理选项
        self._create_section_label(content, "02. ANALYSIS CONFIG (分析配置)")
        
        opts_frame = tk.Frame(content, bg=self.colors["card_bg"])
        opts_frame.pack(fill="x", pady=5)
        
        tk.Label(opts_frame, text="Format:", bg=self.colors["card_bg"]).grid(row=0, column=0, sticky="w")
        formats = ["JPG", "PNG", "BMP", "WEBP", "ICO"]
        ttk.Combobox(opts_frame, values=formats, textvariable=self.target_format, width=6, state="readonly").grid(row=0, column=1, padx=5, sticky="w")
        
        tk.Checkbutton(opts_frame, text="Resize (Max px)", variable=self.enable_resize, bg=self.colors["card_bg"]).grid(row=0, column=2, padx=15, sticky="w")
        ttk.Entry(opts_frame, textvariable=self.resize_width, width=6).grid(row=0, column=3, sticky="w")

        tk.Checkbutton(opts_frame, text="Watermark (Semi-Transparent)", variable=self.enable_watermark, bg=self.colors["card_bg"]).grid(row=1, column=2, padx=15, sticky="w", pady=5)
        ttk.Entry(opts_frame, textvariable=self.watermark_text, width=15).grid(row=1, column=3, sticky="w", pady=5)

        # 4. 执行
        tk.Frame(content, height=2, bg="#BDC3C7").pack(fill="x", pady=15)
        self.btn_run = ttk.Button(content, text="INITIATE PROCESSING (开始推理)", style="Red.TButton", command=self.start_thread)
        self.btn_run.pack(fill="x", ipady=5)
        self.progress = ttk.Progressbar(content, style="Horizontal.TProgressbar", mode="determinate")
        self.progress.pack(fill="x", pady=10)

        # 5. 日志
        self.log_area = scrolledtext.ScrolledText(content, height=6, bg=self.colors["log_bg"], fg=self.colors["log_fg"], font=self.fonts["mono"], relief="flat")
        self.log_area.pack(fill="both", expand=True)
        self.log("TERMINAL READY. WAITING FOR EVIDENCE...")

    def _create_section_label(self, parent, text):
        tk.Label(parent, text=text, font=("Arial", 9, "bold"), fg=self.colors["accent_blue"], bg=self.colors["card_bg"]).pack(anchor="w")

    def _create_context_menu(self):
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="❌ 移除此线索 (Remove)", command=self.remove_selected)
        self.context_menu.add_command(label="🗑️ 清空列表 (Clear All)", command=self.clear_list)
        
        def do_popup(event):
            try:
                # 自动选中鼠标所在的项
                self.listbox_files.selection_clear(0, tk.END)
                self.listbox_files.selection_set(self.listbox_files.nearest(event.y))
                self.context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.context_menu.grab_release()
        
        self.listbox_files.bind("<Button-3>", do_popup)

    def _draw_default_logo(self):
        self.canvas_char.delete("all")
        w, h = 280, 380
        cx, cy = w/2, h/2 - 20
        self.canvas_char.create_oval(cx-70, cy-25, cx-10, cy+25, outline="white", width=3)
        self.canvas_char.create_oval(cx+10, cy-25, cx+70, cy+25, outline="white", width=3)
        self.canvas_char.create_line(cx-10, cy, cx+10, cy, fill="white", width=3)
        self.canvas_char.create_arc(cx-60, cy-15, cx-20, cy+25, start=0, extent=90, style="arc", outline=self.colors["accent_blue"], width=2)
        bow_y = cy + 60
        points = [cx, bow_y, cx-40, bow_y-20, cx-40, bow_y+20, cx, bow_y+5, cx+40, bow_y+20, cx+40, bow_y-20]
        self.canvas_char.create_polygon(points, fill=self.colors["accent_red"], outline="white", width=2)
        self.canvas_char.create_text(cx, h-50, text="EDOGAWA CONAN", fill="#7F8C8D", font=("Arial", 10, "bold"))
        self.canvas_char.create_text(cx, h-30, text="INTELLIGENCE TERMINAL", fill="#7F8C8D", font=("Arial", 8))

    def load_character_image(self):
        file_path = filedialog.askopenfilename(title="选择调查员图片", filetypes=[("Images", "*.png;*.jpg;*.jpeg")])
        if not file_path: return
        try:
            pil_img = Image.open(file_path)
            cw, ch = 280, 380
            ratio = min(cw/pil_img.width, ch/pil_img.height)
            new_size = (int(pil_img.width * ratio), int(pil_img.height * ratio))
            pil_img = pil_img.resize(new_size, Image.Resampling.LANCZOS)
            self.char_photo = ImageTk.PhotoImage(pil_img)
            self.canvas_char.delete("all")
            self.canvas_char.create_image(cw/2, ch/2, image=self.char_photo, anchor="center")
            self.log(f"INVESTIGATOR UPDATED: {os.path.basename(file_path)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed: {e}")

    # === 核心逻辑升级 ===
    def select_files(self):
        # 使用 askopenfilenames，这允许用户在对话框中看到图片图标并多选
        files = filedialog.askopenfilenames(
            title="浏览并挑选图片 (按住Ctrl多选)",
            initialdir=self.last_open_dir,
            filetypes=[("Images", "*.jpg;*.png;*.bmp;*.webp;*.ico"), ("All Files", "*.*")]
        )
        if files:
            # 记录这次打开的路径，下次直接跳到这里
            self.last_open_dir = os.path.dirname(files[0])
            
            # 追加去重
            current_files = set(self.source_files)
            new_files = [f for f in files if f not in current_files]
            if new_files:
                self.source_files.extend(new_files)
                self._update_listbox()
                self.log(f"Added {len(new_files)} selected files.")
            else:
                self.log("Selected files are already in the list.")

    def select_folder(self):
        path = filedialog.askdirectory(initialdir=self.last_open_dir)
        if path:
            self.last_open_dir = path
            valid = ('.jpg', '.jpeg', '.png', '.bmp', '.webp')
            new_files = [os.path.join(path, f) for f in os.listdir(path) if f.lower().endswith(valid)]
            
            # 追加去重
            current_files = set(self.source_files)
            added_files = [f for f in new_files if f not in current_files]
            
            self.source_files.extend(added_files)
            self._update_listbox()
            self.log(f"Imported folder: {len(added_files)} new images found.")

    def remove_selected(self):
        """移除列表中的选中项"""
        selected_indices = self.listbox_files.curselection()
        if not selected_indices:
            return
        
        # 从后往前删，避免索引错位
        for index in reversed(selected_indices):
            del self.source_files[index]
            
        self._update_listbox()
        self.log(f"Removed {len(selected_indices)} items.")

    def clear_list(self):
        self.source_files = []
        self._update_listbox()
        self.log("EVIDENCE LIST CLEARED.")
            
    def _update_listbox(self):
        self.listbox_files.delete(0, tk.END)
        for f in self.source_files:
            self.listbox_files.insert(tk.END, f"📄 [WAITING] {os.path.basename(f)}")
        
        count = len(self.source_files)
        self.lbl_status.config(text=f"READY ({count} FILES)", fg=self.colors["accent_blue"])
        self.progress["value"] = 0
        self.btn_open_folder.config(state="disabled")

    def _update_list_item_status(self, index, status_code, filename):
        if status_code == 0:
            new_text = f"⏳ [PROCESSING] {filename}"
        elif status_code == 1:
            new_text = f"✅ [DONE] {filename}"
        else:
            new_text = f"❌ [FAILED] {filename}"
            
        self.listbox_files.delete(index)
        self.listbox_files.insert(index, new_text)
        self.listbox_files.see(index)
        self.listbox_files.selection_clear(0, tk.END)
        self.listbox_files.selection_set(index)

    def open_output_folder(self):
        if not self.source_files: return
        base_dir = os.path.dirname(self.source_files[0])
        output_dir = os.path.join(base_dir, "resolved_cases")
        if not os.path.exists(output_dir):
            messagebox.showinfo("Info", "Folder does not exist yet.")
            return
        try:
            if platform.system() == "Windows": os.startfile(output_dir)
            elif platform.system() == "Darwin": subprocess.Popen(["open", output_dir])
            else: subprocess.Popen(["xdg-open", output_dir])
        except Exception as e:
            self.log(f"Cannot open folder: {e}")

    def log(self, msg):
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, f"> {msg}\n")
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')

    def start_thread(self):
        if not self.source_files:
            messagebox.showwarning("No Evidence", "Please add images to the evidence list first!")
            return
        self.btn_run.config(state="disabled")
        self.lbl_status.config(text="PROCESSING...", fg=self.colors["accent_red"])
        threading.Thread(target=self.process_images, daemon=True).start()

    def process_images(self):
        target_ext = self.target_format.get().lower()
        if target_ext == "jpeg": target_ext = "jpg"
        
        # 输出路径逻辑优化：使用第一张图片的路径作为基准
        base_dir = os.path.dirname(self.source_files[0])
        output_dir = os.path.join(base_dir, "resolved_cases")
        if not os.path.exists(output_dir): os.makedirs(output_dir)

        total = len(self.source_files)
        self.progress["maximum"] = total
        
        font = ImageFont.load_default()
        if self.enable_watermark.get():
            try: font = ImageFont.truetype("arial.ttf", 36)
            except: pass

        success_count = 0
        
        for i, path in enumerate(self.source_files):
            filename = os.path.basename(path)
            self.root.after(0, self._update_list_item_status, i, 0, filename)
            
            try:
                with Image.open(path) as img:
                    if img.mode != 'RGBA': img = img.convert('RGBA')
                    
                    if self.enable_resize.get():
                        ms = self.resize_width.get()
                        img.thumbnail((ms, ms), Image.Resampling.LANCZOS)
                        
                    if self.enable_watermark.get():
                        txt = self.watermark_text.get()
                        txt_layer = Image.new('RGBA', img.size, (255, 255, 255, 0))
                        draw = ImageDraw.Draw(txt_layer)
                        bbox = draw.textbbox((0,0), txt, font=font)
                        tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
                        x, y = img.width - tw - 20, img.height - th - 20
                        draw.text((x+2, y+2), txt, font=font, fill=(0, 0, 0, 100))
                        draw.text((x, y), txt, font=font, fill=(231, 76, 60, 180)) 
                        img = Image.alpha_composite(img, txt_layer)

                    if target_ext in ("jpg", "jpeg", "bmp"):
                        background = Image.new("RGB", img.size, (255, 255, 255))
                        background.paste(img, mask=img.split()[3])
                        final_img = background
                    else:
                        final_img = img

                    save_path = os.path.join(output_dir, f"{os.path.splitext(filename)[0]}.{target_ext}")
                    final_img.save(save_path, quality=95)
                    self.log(f"Resolved: {filename}")
                    success_count += 1
                    self.root.after(0, self._update_list_item_status, i, 1, filename)
                    
            except Exception as e:
                self.log(f"Error {filename}: {e}")
                self.root.after(0, self._update_list_item_status, i, 2, filename)
            
            self.progress["value"] = i + 1
            self.root.update_idletasks()

        self.lbl_status.config(text="CASE CLOSED", fg="#2ECC71")
        self.btn_run.config(state="normal")
        self.btn_open_folder.config(state="normal")
        messagebox.showinfo("Result", f"Processing Complete!\nSuccessful: {success_count}/{total}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageProcessorPro(root)
    root.mainloop()