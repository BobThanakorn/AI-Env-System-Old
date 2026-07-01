# เพิ่มฟีเจอร์ Create File ✨

## สรุป
ฟีเจอร์ใหม่ `create_file` ให้ user สามารถสร้างไฟล์ข้อความใหม่ในระบบได้

## ไฟล์ที่เปลี่ยนแปลง

### 1. `app/tools/file_tools.py`
- เพิ่มฟังก์ชัน `create_file(path, content)` ใหม่
- Update `execute_tool()` เพื่อรองรับ action `create_file`

### 2. `app/runtime/planner.py`
- Update system prompt ของ planner ให้รู้จัก action `create_file`
- เพิ่มตัวอย่าง args สำหรับ create_file

### 3. `frontend/chat.html`
- เพิ่มปุ่ม "Create File" ในเมนู quick actions
- ปุ่มจะอยู่ในตำแหน่งสุดท้ายของรายการ quick actions

---

## วิธีใช้

### ผ่าน Chat UI
1. คลิกปุ่ม "Create File" ใน sidebar
2. หรือพิมพ์คำสั่งเอง เช่น:
   - "สร้างไฟล์ชื่อ myfile.txt ด้วยเนื้อหา hello world"
   - "Create a file named test.txt with content example"

### Response Format
สำเร็จ:
```json
{
  "tool": "create_file",
  "status": "success",
  "created_file": "myfile.txt",
  "size_bytes": 11
}
```

Error (ถ้าไฟล์มีอยู่แล้ว):
```json
{
  "tool": "create_file",
  "error": "File already exists: myfile.txt"
}
```

---

## ข้อจำกัด

✅ ไฟล์ต้องอยู่ใน `workspace/` เท่านั้น  
✅ ไม่สามารถเขียนทับไฟล์ที่มีอยู่แล้ว  
✅ อัตโนมัติสร้าง parent directories หากไม่มี  

---

## ตัวอย่าง

```bash
# User: "สร้างไฟล์ summary.txt ด้วยเนื้อหา: นี่คือสรุป"
# Agent:
# 1. Planner → "action: create_file, path: summary.txt, content: นี่คือสรุป"
# 2. Tool → สร้างไฟล์ ✓
# 3. Summary → "ฉันสร้างไฟล์ summary.txt เรียบร้อยแล้ว ขนาด 28 bytes"
```

---

## Next Steps
Phase 4 จะเพิ่ม tools อื่นๆ เช่น:
- `append_file` - เพิ่มเนื้อหาต่อไฟล์
- `search_files` - ค้นหาคำศัพท์ในไฟล์
- `get_workspace_tree` - แสดงโครงสร้างโฟลเดอร์

Generated: 2026-07-01 14:56 UTC+7
