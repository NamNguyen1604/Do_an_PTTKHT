import tkinter as tk
from tkinter import messagebox, ttk
import pyodbc
import os
from datetime import datetime

# Kết nối CSDL SQL Server
conn = pyodbc.connect(
    'DRIVER={SQL Server};'
    'SERVER=localhost\\SQL25;'
    'DATABASE=\u0110\u1ed3 \u00e1n new;'
    'Trusted_Connection=yes;'
)
cursor = conn.cursor()

# === HÀM CHUNG ===
def run_query(query, params=()):
    cur = conn.cursor()
    cur.execute(query, params)
    conn.commit()
    return cur

def fetch_query(query, params=()):
    cur = conn.cursor()
    cur.execute(query, params)
    return cur.fetchall()

def get_product_info(product_id):
    result = fetch_query("SELECT Tensanpham, Dongia FROM Mathang WHERE Masanpham = ?", (product_id,))
    return result[0] if result else ("", "")

def get_employee_name(manv):
    result = fetch_query("SELECT Hoten FROM Nhanvien WHERE Manhanvien = ?", (manv,))
    return result[0][0] if result else ""

def get_customer_name(makh):
    result = fetch_query("SELECT TenKH FROM Khachhang WHERE MaKH = ?", (makh,))
    return result[0][0] if result else ""

def print_invoice(data):
    filename = f"hoadon_{data['Sohoadon']}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write("HÓA ĐƠN BÁN HÀNG\n\n")
        f.write(f"Khách hàng: {data['TenKH']}\n")
        f.write(f"Địa chỉ: {data.get('Diachi', '')}\n")
        f.write(f"Số điện thoại: {data.get('Dienthoai', '')}\n\n")
        f.write(f"Ngày lập: {data['Ngay']}\n")
        f.write(f"Số hóa đơn: {data['Sohoadon']}\n\n")
        f.write("| Tên hàng hóa | SL | Đơn giá | Thành tiền |\n")
        f.write("|---------------|----|----------|-------------|\n")
        f.write(f"| {data['Tensanpham']:<13} | {data['Soluong']:<2} | {data['Dongia']:<8} | {data['Thanhtien']:<11} |\n")
        f.write("\n")
        f.write(f"Thuế VAT 10%: {data['VAT']}\n")
        f.write(f"Tổng cộng: {data['Tongcong']}\n\n")
        f.write("Người lập hóa đơn         Khách hàng\n")
        f.write("(Ký và ghi rõ họ tên)     (Ký và ghi rõ họ tên)\n")
    os.startfile(filename, "print")

def open_module(title, fields, table):
    win = tk.Toplevel()
    win.title(title)
    entries = []
    for idx, field in enumerate(fields):
        tk.Label(win, text=field).grid(row=idx, column=0)
        ent = tk.Entry(win)
        ent.grid(row=idx, column=1)
        entries.append(ent)

    def auto_fill_fields(event=None):
        field_map = {f: i for i, f in enumerate(fields)}
        if "Masanpham" in field_map:
            masp = entries[field_map["Masanpham"]].get()
            tensp, dongia = get_product_info(masp)
            if "Tensanpham" in field_map:
                entries[field_map["Tensanpham"]].delete(0, tk.END)
                entries[field_map["Tensanpham"]].insert(0, tensp)
            if "Dongia" in field_map:
                entries[field_map["Dongia"]].delete(0, tk.END)
                entries[field_map["Dongia"]].insert(0, dongia)
        if "Manhanvien" in field_map:
            manv = entries[field_map["Manhanvien"]].get()
            hoten = get_employee_name(manv)
            if "Hoten" in field_map:
                entries[field_map["Hoten"]].delete(0, tk.END)
                entries[field_map["Hoten"]].insert(0, hoten)
        if "Makhachhang" in field_map:
            makh = entries[field_map["Makhachhang"]].get()
            tenkh = get_customer_name(makh)
            if "TenKH" in field_map:
                entries[field_map["TenKH"]].delete(0, tk.END)
                entries[field_map["TenKH"]].insert(0, tenkh)

    for i, field in enumerate(fields):
        if field in ["Masanpham", "Manhanvien", "Makhachhang"]:
            entries[i].bind("<FocusOut>", auto_fill_fields)

    def them():
        values = tuple(ent.get() for ent in entries)
        placeholders = ','.join(['?'] * len(fields))
        query = f"INSERT INTO {table} VALUES ({placeholders})"
        run_query(query, values)
        messagebox.showinfo("Thành công", f"Đã thêm vào bảng {table}!")
        refresh()

    def sua():
        if not tree.selection():
            return messagebox.showwarning("Chọn dòng", "Hãy chọn dòng cần sửa")
        values = tuple(ent.get() for ent in entries)
        set_clause = ', '.join([f"{f} = ?" for f in fields[1:]])
        query = f"UPDATE {table} SET {set_clause} WHERE {fields[0]} = ?"
        params = values[1:] + (values[0],)
        run_query(query, params)
        messagebox.showinfo("Cập nhật", "Đã cập nhật dữ liệu!")
        refresh()

    def xoa():
        if not tree.selection():
            return messagebox.showwarning("Chọn dòng", "Hãy chọn dòng cần xóa")
        selected = tree.item(tree.focus(), 'values')
        id_field = fields[0]
        query = f"DELETE FROM {table} WHERE {id_field} = ?"
        run_query(query, (selected[0],))
        messagebox.showinfo("Xóa", "Đã xóa dữ liệu!")
        refresh()

    def in_hoa_don():
        if not tree.selection():
            return messagebox.showwarning("Chọn dòng", "Chọn hóa đơn để in")
        selected = tree.item(tree.focus(), 'values')
        if table == "Hoadonbanhang":
            data = dict(zip(fields, selected))
            dongia = float(data['Dongia'])
            soluong = int(data['Soluong'])
            thanhtien = dongia * soluong
            vat = thanhtien * 0.1
            tongcong = thanhtien + vat
            data['Thanhtien'] = f"{thanhtien:.2f}"
            data['VAT'] = f"{vat:.2f}"
            data['Tongcong'] = f"{tongcong:.2f}"
            print_invoice(data)

    tk.Button(win, text="Thêm", command=them).grid(row=len(fields), column=0, pady=5)
    tk.Button(win, text="Cập nhật", command=sua).grid(row=len(fields), column=1, pady=5)
    tk.Button(win, text="Xóa", command=xoa).grid(row=len(fields), column=2, pady=5)
    if table == "Hoadonbanhang":
        tk.Button(win, text="In hóa đơn", command=in_hoa_don).grid(row=len(fields), column=3, pady=5)

    tree = ttk.Treeview(win, columns=fields, show='headings')
    for field in fields:
        tree.heading(field, text=field)
        tree.column(field, width=100)
    tree.grid(row=0, column=4, rowspan=len(fields)+2, padx=10)

    def refresh():
        for row in tree.get_children():
            tree.delete(row)
        rows = fetch_query(f"SELECT * FROM {table}")
        for row in rows:
            values = [item.strftime("%Y-%m-%d") if hasattr(item, "strftime") else str(item) for item in row]
            tree.insert('', 'end', values=values)

    def on_select(event):
        selected = tree.focus()
        if selected:
            values = tree.item(selected, 'values')
            for i in range(len(fields)):
                entries[i].delete(0, tk.END)
                entries[i].insert(0, values[i])

    tree.bind("<<TreeviewSelect>>", on_select)
    refresh()

def login_window():
    def check_login():
        user = username.get()
        pwd = password.get()
        cursor.execute("SELECT * FROM TaiKhoan WHERE Username=? AND Password=?", (user, pwd))
        if cursor.fetchone():
            login.destroy()
            main_menu()
        else:
            messagebox.showerror("Lỗi", "Sai tài khoản hoặc mật khẩu")

    login = tk.Tk()
    login.title("Đăng nhập hệ thống")
    tk.Label(login, text="Username").grid(row=0, column=0)
    tk.Label(login, text="Password").grid(row=1, column=0)
    username = tk.Entry(login)
    password = tk.Entry(login, show="*")
    username.grid(row=0, column=1)
    password.grid(row=1, column=1)
    tk.Button(login, text="Đăng nhập", command=check_login).grid(row=2, column=1)
    login.mainloop()

def main_menu():
    root = tk.Tk()
    root.title("Hệ thống quản lý bán hàng siêu thị")
    tk.Button(root, text="Quản lý sản phẩm", width=30,
              command=lambda: open_module("Quản lý sản phẩm",
                  ["Masanpham", "Tensanpham", "ManhaCC", "Soluong", "Dongia", "Donvitinh"], "Mathang")).pack(pady=5)
    tk.Button(root, text="Quản lý khách hàng", width=30,
              command=lambda: open_module("Quản lý khách hàng",
                  ["MaKH", "TenKH", "Diachi", "Dienthoai"], "Khachhang")).pack(pady=5)
    tk.Button(root, text="Quản lý nhân viên", width=30,
              command=lambda: open_module("Quản lý nhân viên",
                  ["Manhanvien", "Hoten", "Ngaysinh", "Diachi", "Gioitinh", "Sodienthoai", "Ngaylamviec", "Mabophan"], "Nhanvien")).pack(pady=5)
    tk.Button(root, text="Lập hóa đơn bán hàng", width=30,
              command=lambda: open_module("Hóa đơn bán hàng",
                  ["Sohoadon", "Ngay", "Masanpham", "Tensanpham", "Soluong", "Dongia", "Manhanvien", "Hoten", "Makhachhang", "TenKH"], "Hoadonbanhang")).pack(pady=5)
    tk.Button(root, text="Nhập kho", width=30,
              command=lambda: open_module("Phiếu nhập kho",
                  ["SoPhieu", "Masanpham", "NgayTao", "Soluong", "DonGia", "Manhanvien"], "PhieuNhapKho")).pack(pady=5)
    tk.Button(root, text="Xuất kho", width=30,
              command=lambda: open_module("Phiếu xuất kho",
                  ["SoPhieu", "Masanpham", "NgayTao", "Soluong", "DonGia", "Manhanvien"], "PhieuXuatKho")).pack(pady=5)
    tk.Button(root, text="Thoát", width=30, command=root.quit).pack(pady=20)
    root.mainloop()

if __name__ == "__main__":
    login_window()
