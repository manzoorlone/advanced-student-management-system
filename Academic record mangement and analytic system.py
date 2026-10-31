"""ADVANCED STUDENT MANAGEMENT SYSTEM - UPGRADED
Run: python Advanced_Student_Management_System_Upgraded.py
First-run accounts: admin/admin123, teacher/teacher123, student/student123
Demo project: change default passwords before using real data.
"""
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from datetime import date
import csv

DB_NAME = "students.db"

class StudentManagementSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Student Management System")
        self.root.geometry("1250x800")
        self.root.minsize(1050, 680)
        self.db = sqlite3.connect(DB_NAME)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys = ON")
        self.create_tables()
        self.show_login()
        self.root.protocol("WM_DELETE_WINDOW", self.close_app)

    def create_tables(self):
        c = self.db.cursor()
        c.executescript("""
        CREATE TABLE IF NOT EXISTS users(
            username TEXT PRIMARY KEY, password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'student', roll TEXT
        );
        CREATE TABLE IF NOT EXISTS students(
            roll TEXT PRIMARY KEY, name TEXT NOT NULL, branch TEXT NOT NULL,
            semester TEXT NOT NULL, phone TEXT, attendance REAL NOT NULL DEFAULT 0,
            marks REAL NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS subjects(
            id INTEGER PRIMARY KEY AUTOINCREMENT, roll TEXT NOT NULL,
            subject TEXT NOT NULL, grade_point REAL NOT NULL, credits REAL NOT NULL,
            semester TEXT NOT NULL DEFAULT 'Current',
            FOREIGN KEY(roll) REFERENCES students(roll) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS assignments(
            id INTEGER PRIMARY KEY AUTOINCREMENT, roll TEXT NOT NULL,
            title TEXT NOT NULL, due_date TEXT, status TEXT NOT NULL DEFAULT 'Pending',
            marks REAL, semester TEXT NOT NULL DEFAULT 'Current',
            FOREIGN KEY(roll) REFERENCES students(roll) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS academic_records(
            id INTEGER PRIMARY KEY AUTOINCREMENT, roll TEXT NOT NULL,
            semester TEXT NOT NULL, attendance REAL NOT NULL DEFAULT 0,
            marks REAL NOT NULL DEFAULT 0, record_date TEXT NOT NULL,
            UNIQUE(roll, semester),
            FOREIGN KEY(roll) REFERENCES students(roll) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS access_requests(
            id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL,
            roll TEXT NOT NULL, semester TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending', requested_on TEXT NOT NULL,
            UNIQUE(username, semester),
            FOREIGN KEY(roll) REFERENCES students(roll) ON DELETE CASCADE
        );
        """)
        # Migrate databases created by the earlier project version.
        for table, col, definition in [
            ('users', 'role', "TEXT NOT NULL DEFAULT 'student'"),
            ('users', 'roll', 'TEXT'),
            ('subjects', 'semester', "TEXT NOT NULL DEFAULT 'Current'"),
            ('assignments', 'semester', "TEXT NOT NULL DEFAULT 'Current'")]:
            names = [r['name'] for r in self.db.execute(f'PRAGMA table_info({table})')]
            if col not in names:
                self.db.execute(f'ALTER TABLE {table} ADD COLUMN {col} {definition}')
        self.db.execute("INSERT OR IGNORE INTO users(username,password,role,roll) VALUES('admin','admin123','admin',NULL)")
        self.db.execute("INSERT OR IGNORE INTO users(username,password,role,roll) VALUES('teacher','teacher123','teacher',NULL)")
        self.db.execute("INSERT OR IGNORE INTO users(username,password,role,roll) VALUES('student','student123','student','DEMO01')")
        self.db.commit()

    def clear(self):
        for w in self.root.winfo_children(): w.destroy()

    def show_login(self):
        self.clear()
        f = ttk.LabelFrame(self.root, text='System Login', padding=25)
        f.place(relx=.5, rely=.5, anchor='center')
        ttk.Label(f, text='ADVANCED STUDENT MANAGEMENT SYSTEM', font=('Arial',17,'bold')).grid(row=0,column=0,columnspan=2,pady=12)
        self.login_user, self.login_pass = tk.StringVar(), tk.StringVar()
        ttk.Label(f,text='Username').grid(row=1,column=0,sticky='w',pady=6)
        ttk.Entry(f,textvariable=self.login_user,width=28).grid(row=1,column=1,pady=6)
        ttk.Label(f,text='Password').grid(row=2,column=0,sticky='w',pady=6)
        e=ttk.Entry(f,textvariable=self.login_pass,show='*',width=28); e.grid(row=2,column=1,pady=6); e.bind('<Return>',lambda _ : self.login())
        ttk.Button(f,text='Login',command=self.login).grid(row=3,column=0,columnspan=2,sticky='ew',pady=12)
        ttk.Label(f,text='Demo: admin/admin123 | teacher/teacher123 | student/student123',foreground='gray').grid(row=4,column=0,columnspan=2)

    def login(self):
        row=self.db.execute('SELECT * FROM users WHERE username=? AND password=?',(self.login_user.get().strip(),self.login_pass.get())).fetchone()
        if not row:
            messagebox.showerror('Login failed','Incorrect username or password.'); return
        self.user=dict(row); self.build_dashboard()

    def build_dashboard(self):
        self.clear()
        top=ttk.Frame(self.root,padding=10); top.pack(fill='x')
        ttk.Label(top,text='ADVANCED STUDENT MANAGEMENT SYSTEM',font=('Arial',17,'bold')).pack(side='left')
        ttk.Label(top,text=f"Logged in: {self.user['username']} ({self.user['role'].title()})").pack(side='left',padx=20)
        ttk.Button(top,text='Change Password',command=self.change_password).pack(side='right',padx=4)
        ttk.Button(top,text='Logout',command=self.show_login).pack(side='right',padx=4)
        self.tabs=ttk.Notebook(self.root); self.tabs.pack(fill='both',expand=True,padx=10,pady=8)
        role=self.user['role']
        if role in ('admin','teacher'):
            self.student_tab=ttk.Frame(self.tabs,padding=8); self.tabs.add(self.student_tab,text='Students'); self.build_student_tab()
            self.report_tab=ttk.Frame(self.tabs,padding=8); self.tabs.add(self.report_tab,text='Attendance & Ranking'); self.build_report_tab()
            self.cgpa_tab=ttk.Frame(self.tabs,padding=8); self.tabs.add(self.cgpa_tab,text='CGPA & Subjects'); self.build_cgpa_tab()
            self.assignment_tab=ttk.Frame(self.tabs,padding=8); self.tabs.add(self.assignment_tab,text='Assignments'); self.build_assignment_tab()
            self.history_tab=ttk.Frame(self.tabs,padding=8); self.tabs.add(self.history_tab,text='Semester History'); self.build_history_tab()
            self.analytics_tab=ttk.Frame(self.tabs,padding=8); self.tabs.add(self.analytics_tab,text='Analytics'); self.build_analytics_tab()
            if role=='admin':
                self.access_tab=ttk.Frame(self.tabs,padding=8); self.tabs.add(self.access_tab,text='Access Approval'); self.build_access_tab()
            self.refresh_all()
        else:
            self.student_portal=ttk.Frame(self.tabs,padding=15); self.tabs.add(self.student_portal,text='My Academic Portal'); self.build_student_portal()

    def change_password(self):
        win=tk.Toplevel(self.root); win.title('Change Password'); win.resizable(False,False)
        old,new,confirm=tk.StringVar(),tk.StringVar(),tk.StringVar()
        for i,(label,var) in enumerate([('Current password',old),('New password',new),('Confirm password',confirm)]):
            ttk.Label(win,text=label).grid(row=i,column=0,padx=8,pady=7,sticky='w'); ttk.Entry(win,textvariable=var,show='*',width=25).grid(row=i,column=1,padx=8,pady=7)
        def save():
            if not self.db.execute('SELECT 1 FROM users WHERE username=? AND password=?',(self.user['username'],old.get())).fetchone(): messagebox.showerror('Error','Current password is incorrect.',parent=win); return
            if len(new.get())<6: messagebox.showwarning('Weak password','Use at least 6 characters.',parent=win); return
            if new.get()!=confirm.get(): messagebox.showerror('Mismatch','Passwords do not match.',parent=win); return
            self.db.execute('UPDATE users SET password=? WHERE username=?',(new.get(),self.user['username'])); self.db.commit(); messagebox.showinfo('Success','Password changed.',parent=win); win.destroy()
        ttk.Button(win,text='Save',command=save).grid(row=3,column=0,columnspan=2,pady=10)

    @staticmethod
    def grade(m):
        return 'A+' if m>=90 else 'A' if m>=80 else 'B' if m>=70 else 'C' if m>=60 else 'D' if m>=50 else 'F'

    def build_student_tab(self):
        form=ttk.LabelFrame(self.student_tab,text='Student Details',padding=8); form.pack(fill='x')
        self.sv={k:tk.StringVar(value=v) for k,v in {'name':'','roll':'','branch':'AI-DS','semester':'3rd','phone':'','attendance':'0','marks':'0'}.items()}
        fields=[('Name','name'),('Roll Number','roll'),('Branch','branch'),('Current Semester','semester'),('Phone','phone'),('Attendance %','attendance'),('Marks / 100','marks')]
        for i,(label,key) in enumerate(fields):
            r,c=divmod(i,4); c*=2; ttk.Label(form,text=label).grid(row=r,column=c,sticky='w',padx=4,pady=4); ttk.Entry(form,textvariable=self.sv[key],width=17).grid(row=r,column=c+1,padx=4,pady=4)
        bar=ttk.Frame(self.student_tab); bar.pack(fill='x',pady=6)
        for t,cmd in [('Add',self.add_student),('Update',self.update_student),('Delete',self.delete_student),('Clear',self.clear_form),('Report Card',self.report_card),('Predict Performance',self.predict)]: ttk.Button(bar,text=t,command=cmd).pack(side='left',padx=3)
        search=ttk.Frame(self.student_tab); search.pack(fill='x'); self.search= tk.StringVar(); ttk.Label(search,text='Search:').pack(side='left'); e=ttk.Entry(search,textvariable=self.search,width=28); e.pack(side='left',padx=5); e.bind('<KeyRelease>',lambda _:self.load_students())
        self.student_tree=self.tree(self.student_tab,('roll','name','branch','semester','phone','attendance','marks','grade'),['Roll','Name','Branch','Semester','Phone','Attendance %','Marks','Grade'],[90,150,90,85,110,100,80,60]); self.student_tree.bind('<<TreeviewSelect>>',self.select_student)

    def tree(self,parent,cols,heads,widths):
        box=ttk.Frame(parent); box.pack(fill='both',expand=True,pady=7); t=ttk.Treeview(box,columns=cols,show='headings',height=12)
        for c,h,w in zip(cols,heads,widths): t.heading(c,text=h); t.column(c,width=w,anchor='center')
        sy=ttk.Scrollbar(box,orient='vertical',command=t.yview); t.configure(yscrollcommand=sy.set); t.pack(side='left',fill='both',expand=True); sy.pack(side='right',fill='y'); return t

    def student_values(self):
        try: att=float(self.sv['attendance'].get()); marks=float(self.sv['marks'].get())
        except ValueError: messagebox.showerror('Invalid','Attendance and marks must be numbers.'); return None
        vals=[self.sv[k].get().strip() for k in ('roll','name','branch','semester')]
        if not all(vals): messagebox.showwarning('Missing','Roll, name, branch and semester are required.'); return None
        if not 0<=att<=100 or not 0<=marks<=100: messagebox.showerror('Range','Attendance and marks must be 0 to 100.'); return None
        return (vals[0],vals[1],vals[2],vals[3],self.sv['phone'].get().strip(),att,marks)

    def add_student(self):
        d=self.student_values()
        if not d:return
        try:
            self.db.execute('INSERT INTO students(roll,name,branch,semester,phone,attendance,marks) VALUES(?,?,?,?,?,?,?)',d)
            self.db.execute('INSERT OR REPLACE INTO academic_records(roll,semester,attendance,marks,record_date) VALUES(?,?,?,?,?)',(d[0],d[3],d[5],d[6],date.today().isoformat()))
            self.db.commit(); self.refresh_all(); self.clear_form(); messagebox.showinfo('Added','Student record saved.')
        except sqlite3.IntegrityError: messagebox.showerror('Duplicate','Roll number already exists.')

    def update_student(self):
        d=self.student_values()
        if not d:return
        cur=self.db.execute('UPDATE students SET name=?,branch=?,semester=?,phone=?,attendance=?,marks=? WHERE roll=?',(d[1],d[2],d[3],d[4],d[5],d[6],d[0]))
        if cur.rowcount:
            self.db.execute('INSERT OR REPLACE INTO academic_records(roll,semester,attendance,marks,record_date) VALUES(?,?,?,?,?)',(d[0],d[3],d[5],d[6],date.today().isoformat())); self.db.commit(); self.refresh_all(); messagebox.showinfo('Updated','Student and semester record updated.')
        else: messagebox.showwarning('Not found','Enter an existing roll number.')

    def delete_student(self):
        sel=self.student_tree.selection()
        if not sel: messagebox.showwarning('Select','Select a student first.'); return
        roll=self.student_tree.item(sel[0],'values')[0]
        if messagebox.askyesno('Confirm',f'Delete student {roll} and linked records?'):
            self.db.execute('DELETE FROM students WHERE roll=?',(roll,)); self.db.commit(); self.refresh_all(); self.clear_form()

    def clear_form(self):
        for k,v in {'name':'','roll':'','branch':'AI-DS','semester':'3rd','phone':'','attendance':'0','marks':'0'}.items(): self.sv[k].set(v)

    def select_student(self,_=None):
        sel=self.student_tree.selection()
        if sel:
            vals=self.student_tree.item(sel[0],'values')
            for k,v in zip(('roll','name','branch','semester','phone','attendance','marks'),vals[:7]): self.sv[k].set(v)

    def load_students(self):
        if not hasattr(self,'student_tree'):return
        self.student_tree.delete(*self.student_tree.get_children()); q=self.search.get().strip()
        rows=self.db.execute('SELECT * FROM students WHERE roll LIKE ? OR name LIKE ? ORDER BY name',(f'%{q}%',f'%{q}%')).fetchall()
        for s in rows:self.student_tree.insert('','end',values=(s['roll'],s['name'],s['branch'],s['semester'],s['phone'],f"{s['attendance']:.1f}",f"{s['marks']:.1f}",self.grade(s['marks'])))

    def build_report_tab(self):
        bar=ttk.Frame(self.report_tab);bar.pack(fill='x')
        for title,cmd in [('Attendance Report',self.load_attendance),('Student Ranking',self.load_ranking),('Export CSV',self.export_csv),('Performance Summary',self.summary)]:ttk.Button(bar,text=title,command=cmd).pack(side='left',padx=4)
        self.report_tree=self.tree(self.report_tab,('rank','roll','name','attendance','marks','grade','status'),['Rank','Roll','Name','Attendance %','Marks','Grade','Attendance Status'],[60,90,170,110,90,70,170])

    def load_attendance(self):
        self.report_tree.delete(*self.report_tree.get_children()); rows=self.db.execute('SELECT * FROM students ORDER BY attendance,name').fetchall()
        for i,s in enumerate(rows,1):self.report_tree.insert('','end',values=(i,s['roll'],s['name'],s['attendance'],s['marks'],self.grade(s['marks']),'Low' if s['attendance']<75 else 'Satisfactory'))
    def load_ranking(self):
        self.report_tree.delete(*self.report_tree.get_children()); rows=self.db.execute('SELECT * FROM students ORDER BY marks DESC,name').fetchall()
        for i,s in enumerate(rows,1):self.report_tree.insert('','end',values=(i,s['roll'],s['name'],s['attendance'],s['marks'],self.grade(s['marks']),'Low' if s['attendance']<75 else 'Satisfactory'))
    def export_csv(self):
        rows=[self.report_tree.item(i,'values') for i in self.report_tree.get_children()]
        if not rows:messagebox.showwarning('Empty','Generate a report first.');return
        p=filedialog.asksaveasfilename(defaultextension='.csv',filetypes=[('CSV','*.csv')],initialfile='student_report.csv')
        if p:
            with open(p,'w',newline='',encoding='utf-8') as f:w=csv.writer(f);w.writerow(['Rank','Roll','Name','Attendance','Marks','Grade','Status']);w.writerows(rows)
            messagebox.showinfo('Saved',f'Report exported to {p}')
    def summary(self):
        r=self.db.execute('SELECT COUNT(*) n,AVG(marks) am,AVG(attendance) aa,MAX(marks) hi,MIN(marks) lo FROM students').fetchone()
        if not r['n']:messagebox.showinfo('Summary','No students added.');return
        messagebox.showinfo('Performance Summary',f"Students: {r['n']}\nAverage marks: {r['am']:.2f}\nAverage attendance: {r['aa']:.2f}%\nHighest marks: {r['hi']}\nLowest marks: {r['lo']}")

    def build_cgpa_tab(self):
        f=ttk.LabelFrame(self.cgpa_tab,text='Subject Grade and Credits',padding=8);f.pack(fill='x')
        self.cr,self.cs,self.gp,self.cred,self.subsem=[tk.StringVar() for _ in range(5)]
        for i,(lab,var) in enumerate([('Student roll',self.cr),('Subject',self.cs),('Grade point (0-10)',self.gp),('Credits',self.cred),('Semester',self.subsem)]):ttk.Label(f,text=lab).grid(row=i,column=0,sticky='w',padx=5,pady=3);ttk.Entry(f,textvariable=var,width=25).grid(row=i,column=1,padx=5,pady=3)
        ttk.Button(f,text='Add Subject',command=self.add_subject).grid(row=5,column=0,columnspan=2,sticky='ew',pady=5);ttk.Button(f,text='Calculate CGPA',command=self.show_cgpa).grid(row=6,column=0,columnspan=2,sticky='ew')
        self.cgpa_label=ttk.Label(self.cgpa_tab,text='CGPA: —',font=('Arial',12,'bold'));self.cgpa_label.pack(anchor='w')
        self.subject_tree=self.tree(self.cgpa_tab,('roll','semester','subject','gp','credits'),['Roll','Semester','Subject','Grade Point','Credits'],[100,100,200,100,100])
    def add_subject(self):
        roll,sub,sem=self.cr.get().strip(),self.cs.get().strip(),self.subsem.get().strip() or 'Current'
        try:gp,cr=float(self.gp.get()),float(self.cred.get())
        except ValueError:messagebox.showerror('Invalid','Grade point and credits must be numbers.');return
        if not self.db.execute('SELECT 1 FROM students WHERE roll=?',(roll,)).fetchone():messagebox.showerror('Missing','Add student first.');return
        if not sub or not 0<=gp<=10 or cr<=0:messagebox.showerror('Invalid','Enter subject, grade point 0-10 and credits above zero.');return
        self.db.execute('INSERT INTO subjects(roll,subject,grade_point,credits,semester) VALUES(?,?,?,?,?)',(roll,sub,gp,cr,sem));self.db.commit();self.load_subjects();messagebox.showinfo('Saved','Subject added.')
    def cgpa_value(self,roll,semester=None):
        if semester:rows=self.db.execute('SELECT grade_point,credits FROM subjects WHERE roll=? AND semester=?',(roll,semester)).fetchall()
        else:rows=self.db.execute('SELECT grade_point,credits FROM subjects WHERE roll=?',(roll,)).fetchall()
        total=sum(x['credits'] for x in rows);return sum(x['grade_point']*x['credits'] for x in rows)/total if total else None
    def show_cgpa(self):
        roll=self.cr.get().strip();sem=self.subsem.get().strip() or None;v=self.cgpa_value(roll,sem)
        self.cgpa_label.config(text=f"CGPA for {roll} ({sem or 'all semesters'}): {v:.2f}/10" if v is not None else 'No subject grades found for this selection.');self.load_subjects()
    def load_subjects(self):
        if not hasattr(self,'subject_tree'):return
        self.subject_tree.delete(*self.subject_tree.get_children())
        for r in self.db.execute('SELECT * FROM subjects ORDER BY roll,semester,subject'):self.subject_tree.insert('','end',values=(r['roll'],r['semester'],r['subject'],r['grade_point'],r['credits']))

    def build_assignment_tab(self):
        f=ttk.LabelFrame(self.assignment_tab,text='Assignment Details',padding=8);f.pack(fill='x')
        self.ar,self.at,self.ad,self.ast,self.am,self.asem=[tk.StringVar() for _ in range(6)];self.ad.set(date.today().isoformat());self.ast.set('Pending')
        for i,(lab,var) in enumerate([('Student roll',self.ar),('Title',self.at),('Due date YYYY-MM-DD',self.ad),('Status',self.ast),('Marks (optional)',self.am),('Semester',self.asem)]):
            ttk.Label(f,text=lab).grid(row=i,column=0,sticky='w',padx=4,pady=3)
            if lab=='Status':ttk.Combobox(f,textvariable=var,values=['Pending','Submitted','Late'],state='readonly',width=22).grid(row=i,column=1,padx=4,pady=3)
            else:ttk.Entry(f,textvariable=var,width=25).grid(row=i,column=1,padx=4,pady=3)
        ttk.Button(f,text='Add Assignment',command=self.add_assignment).grid(row=6,column=0,columnspan=2,sticky='ew',pady=5)
        self.assignment_tree=self.tree(self.assignment_tab,('id','roll','name','title','due','status','marks','semester'),['ID','Roll','Student','Title','Due','Status','Marks','Semester'],[45,75,120,180,95,85,70,90])
    def add_assignment(self):
        roll,title,due=self.ar.get().strip(),self.at.get().strip(),self.ad.get().strip()
        if not self.db.execute('SELECT 1 FROM students WHERE roll=?',(roll,)).fetchone() or not title:messagebox.showerror('Missing','Enter a valid student roll and title.');return
        try:
            if due:date.fromisoformat(due)
            marks=float(self.am.get()) if self.am.get().strip() else None
        except ValueError:messagebox.showerror('Invalid','Check date (YYYY-MM-DD) and marks.');return
        if marks is not None and not 0<=marks<=100:messagebox.showerror('Invalid','Marks must be 0-100.');return
        self.db.execute('INSERT INTO assignments(roll,title,due_date,status,marks,semester) VALUES(?,?,?,?,?,?)',(roll,title,due,self.ast.get(),marks,self.asem.get().strip() or 'Current'));self.db.commit();self.load_assignments();messagebox.showinfo('Saved','Assignment added.')
    def load_assignments(self):
        if not hasattr(self,'assignment_tree'):return
        self.assignment_tree.delete(*self.assignment_tree.get_children())
        for a in self.db.execute('SELECT a.*,s.name FROM assignments a JOIN students s ON a.roll=s.roll ORDER BY a.due_date'):
            self.assignment_tree.insert('','end',values=(a['id'],a['roll'],a['name'],a['title'],a['due_date'],a['status'],a['marks'] if a['marks'] is not None else 'N/A',a['semester']))

    def build_history_tab(self):
        f=ttk.LabelFrame(self.history_tab,text='Save / View Semester Record',padding=8);f.pack(fill='x')
        self.hr,self.hs,self.ha,self.hm=[tk.StringVar() for _ in range(4)]
        for i,(lab,var) in enumerate([('Student roll',self.hr),('Semester',self.hs),('Attendance %',self.ha),('Marks / 100',self.hm)]):ttk.Label(f,text=lab).grid(row=i,column=0,sticky='w',padx=4,pady=3);ttk.Entry(f,textvariable=var,width=25).grid(row=i,column=1,padx=4,pady=3)
        ttk.Button(f,text='Save Semester Record',command=self.save_history).grid(row=4,column=0,columnspan=2,sticky='ew',pady=5)
        self.history_tree=self.tree(self.history_tab,('roll','semester','attendance','marks','date'),['Roll','Semester','Attendance','Marks','Saved Date'],[100,130,120,100,130])
    def save_history(self):
        roll,sem=self.hr.get().strip(),self.hs.get().strip()
        try:a,m=float(self.ha.get()),float(self.hm.get())
        except ValueError:messagebox.showerror('Invalid','Attendance and marks must be numbers.');return
        if not self.db.execute('SELECT 1 FROM students WHERE roll=?',(roll,)).fetchone() or not sem or not 0<=a<=100 or not 0<=m<=100:messagebox.showerror('Invalid','Check roll, semester, attendance and marks.');return
        self.db.execute('INSERT OR REPLACE INTO academic_records(roll,semester,attendance,marks,record_date) VALUES(?,?,?,?,?)',(roll,sem,a,m,date.today().isoformat()));self.db.commit();self.load_history();messagebox.showinfo('Saved','Semester history saved.')
    def load_history(self):
        if not hasattr(self,'history_tree'):return
        self.history_tree.delete(*self.history_tree.get_children())
        for r in self.db.execute('SELECT * FROM academic_records ORDER BY roll,semester'):self.history_tree.insert('','end',values=(r['roll'],r['semester'],r['attendance'],r['marks'],r['record_date']))

    def build_analytics_tab(self):
        bar=ttk.Frame(self.analytics_tab);bar.pack(fill='x');ttk.Button(bar,text='Refresh Charts',command=self.draw_analytics).pack(side='left')
        self.chart=tk.Canvas(self.analytics_tab,bg='white',height=520);self.chart.pack(fill='both',expand=True,pady=8);self.draw_analytics()
    def draw_analytics(self):
        if not hasattr(self,'chart'):return
        c=self.chart;c.delete('all');rows=self.db.execute('SELECT roll,name,attendance,marks FROM students ORDER BY name LIMIT 12').fetchall()
        if not rows:c.create_text(400,180,text='Add students to view attendance and marks charts.',font=('Arial',14));return
        c.create_text(300,20,text='Student Performance Analytics (first 12 students)',font=('Arial',14,'bold'))
        maxv=max(100,max(max(r['attendance'],r['marks']) for r in rows));base=440;scale=3.2
        for i,r in enumerate(rows):
            x=70+i*88;c.create_rectangle(x,base-r['attendance']*scale/1.25,x+22,base,fill='#4a90e2');c.create_rectangle(x+25,base-r['marks']*scale/1.25,x+47,base,fill='#55a868');c.create_text(x+23,base+18,text=r['roll'][:8],font=('Arial',8));
        c.create_text(300,485,text='Blue = Attendance %     Green = Marks / 100',font=('Arial',10))

    def build_access_tab(self):
        ttk.Label(self.access_tab,text='Students request access to a semester in their portal. Admin approves or revokes it here.').pack(anchor='w',pady=5)
        bar=ttk.Frame(self.access_tab);bar.pack(fill='x')
        ttk.Button(bar,text='Approve Selected',command=lambda:self.set_access('Approved')).pack(side='left',padx=4);ttk.Button(bar,text='Revoke Selected',command=lambda:self.set_access('Revoked')).pack(side='left',padx=4);ttk.Button(bar,text='Refresh',command=self.load_access).pack(side='left',padx=4)
        self.access_tree=self.tree(self.access_tab,('id','username','roll','semester','status','date'),['ID','Username','Roll','Semester','Status','Requested'],[60,130,100,130,100,130]);self.load_access()
    def load_access(self):
        if not hasattr(self,'access_tree'):return
        self.access_tree.delete(*self.access_tree.get_children())
        for r in self.db.execute('SELECT * FROM access_requests ORDER BY id DESC'):self.access_tree.insert('','end',values=(r['id'],r['username'],r['roll'],r['semester'],r['status'],r['requested_on']))
    def set_access(self,status):
        sel=self.access_tree.selection()
        if not sel:messagebox.showwarning('Select','Select an access request.');return
        rid=self.access_tree.item(sel[0],'values')[0];self.db.execute('UPDATE access_requests SET status=? WHERE id=?',(status,rid));self.db.commit();self.load_access();messagebox.showinfo('Updated',f'Access {status.lower()}.')

    def build_student_portal(self):
        roll=self.user.get('roll')
        ttk.Label(self.student_portal,text='Student Read-Only Portal',font=('Arial',16,'bold')).pack(anchor='w')
        ttk.Label(self.student_portal,text=f'Your linked roll number: {roll or "Not linked"}').pack(anchor='w',pady=4)
        if not roll or not self.db.execute('SELECT 1 FROM students WHERE roll=?',(roll,)).fetchone():
            ttk.Label(self.student_portal,text='Your account is not linked to a student record. Ask the administrator to link your account.').pack(anchor='w');return
        ttk.Label(self.student_portal,text='Request access to a semester:').pack(anchor='w',pady=(12,2));self.request_sem=tk.StringVar();ttk.Entry(self.student_portal,textvariable=self.request_sem,width=25).pack(anchor='w');ttk.Button(self.student_portal,text='Request Semester Access',command=self.request_access).pack(anchor='w',pady=5)
        self.portal_text=tk.Text(self.student_portal,height=18,width=100);self.portal_text.pack(fill='both',expand=True,pady=8);self.show_portal_records()
    def request_access(self):
        sem=self.request_sem.get().strip()
        if not sem:messagebox.showwarning('Missing','Enter a semester name.');return
        try:self.db.execute('INSERT INTO access_requests(username,roll,semester,status,requested_on) VALUES(?,?,?,"Pending",?)',(self.user['username'],self.user['roll'],sem,date.today().isoformat()));self.db.commit();messagebox.showinfo('Requested','Request sent to admin for approval.')
        except sqlite3.IntegrityError:messagebox.showinfo('Already requested','A request for this semester already exists.')
    def show_portal_records(self):
        self.portal_text.delete('1.0','end');roll=self.user['roll']
        self.portal_text.insert('end','Your own records are read-only. You cannot edit attendance, CGPA or assignments.\n\n')
        approvals=self.db.execute('SELECT semester FROM access_requests WHERE username=? AND status="Approved"',(self.user['username'],)).fetchall();allowed=[r['semester'] for r in approvals]
        if not allowed:self.portal_text.insert('end','No semester access approved yet. Submit a request above.');return
        for sem in allowed:
            rec=self.db.execute('SELECT * FROM academic_records WHERE roll=? AND semester=?',(roll,sem)).fetchone()
            cg=self.cgpa_value(roll,sem)
            self.portal_text.insert('end',f'--- {sem} ---\n')
            if rec:self.portal_text.insert('end',f"Attendance: {rec['attendance']}% | Marks: {rec['marks']} | Grade: {self.grade(rec['marks'])}\n")
            else:self.portal_text.insert('end','No semester summary saved.\n')
            self.portal_text.insert('end',f'CGPA: {cg:.2f}/10\n' if cg is not None else 'CGPA: Not entered\n')
            for a in self.db.execute('SELECT title,status,due_date,marks FROM assignments WHERE roll=? AND semester=?',(roll,sem)):
                self.portal_text.insert('end',f"Assignment: {a['title']} | {a['status']} | Due: {a['due_date']} | Marks: {a['marks']}\n")
            self.portal_text.insert('end','\n')

    def report_card(self):
        sel=self.student_tree.selection();roll=self.student_tree.item(sel[0],'values')[0] if sel else self.sv['roll'].get().strip()
        s=self.db.execute('SELECT * FROM students WHERE roll=?',(roll,)).fetchone()
        if not s:messagebox.showwarning('Select','Select a student or enter a valid roll.');return
        lines=['STUDENT REPORT CARD','===================',f"Name: {s['name']}",f"Roll: {roll}",f"Branch: {s['branch']}",f"Semester: {s['semester']}",f"Attendance: {s['attendance']}%",f"Marks: {s['marks']}/100",f"Grade: {self.grade(s['marks'])}",'','SEMESTER HISTORY']
        for r in self.db.execute('SELECT * FROM academic_records WHERE roll=? ORDER BY semester',(roll,)):lines.append(f"{r['semester']}: Attendance {r['attendance']}%, Marks {r['marks']}, Grade {self.grade(r['marks'])}")
        lines+=['','SUBJECTS']
        for r in self.db.execute('SELECT * FROM subjects WHERE roll=? ORDER BY semester',(roll,)):lines.append(f"{r['semester']} | {r['subject']} | GP {r['grade_point']} | Credits {r['credits']}")
        p=filedialog.asksaveasfilename(defaultextension='.txt',initialfile=f'report_card_{roll}.txt',filetypes=[('Text','*.txt')])
        if p:Path(p).write_text('\n'.join(lines),encoding='utf-8');messagebox.showinfo('Saved',f'Report card saved: {p}')
    def predict(self):
        sel=self.student_tree.selection()
        if not sel:messagebox.showwarning('Select','Select a student first.');return
        roll=self.student_tree.item(sel[0],'values')[0];s=self.db.execute('SELECT * FROM students WHERE roll=?',(roll,)).fetchone();score=s['marks']*.7+s['attendance']*.3
        label='Good performance estimate' if score>=75 else 'Average performance estimate' if score>=50 else 'May need academic support'
        messagebox.showinfo('Performance Estimate',f"{s['name']}\nCombined indicator: {score:.1f}/100\n{label}\n\nThis is a simple rule-based estimate, not trained AI/ML.")

    def refresh_all(self):
        self.load_students();self.load_attendance();self.load_subjects();self.load_assignments();self.load_history()
        if hasattr(self,'access_tree'):self.load_access()
        if hasattr(self,'chart'):self.draw_analytics()
    def close_app(self):
        self.db.close();self.root.destroy()

if __name__=='__main__':
    root=tk.Tk();app=StudentManagementSystem(root);root.mainloop()
