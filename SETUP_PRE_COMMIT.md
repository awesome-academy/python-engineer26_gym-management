# 🪝 Pre-commit Hooks Setup

Tự động check code quality mỗi lần commit: **ruff + mypy**.

---

## 📋 Cái Gì Được Check?

| Tool | Tác Dụng | Action |
|------|---------|--------|
| **ruff** | Linting + Format | Auto-fix minor issues |
| **mypy** | Type checking | Report errors (fail commit) |
| **trailing-whitespace** | Cleanup | Auto-fix |
| **end-of-file-fixer** | File format | Auto-fix |

---

## 🚀 Setup (Lần Đầu)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```
This installs both core and dev dependencies including pre-commit, ruff, mypy, pytest.

### 2. Install Pre-commit Framework
```bash
pre-commit install
```

### 3. Test Setup
```bash
pre-commit run --all-files
```

**Output Example**:
```
ruff.....................................................................Passed
ruff-format.........................................................Passed
mypy.....................................................................Failed
Tip: fix by running 'mypy app/'
```

---

## 📝 Cách Hoạt Động

### Lần Thứ Nhất Commit
```bash
git add app/models/user.py
git commit -m "Add UserRole enum"
```

**Pre-commit tự động**:
1. ✅ Chạy ruff (fix formatting issues)
2. ✅ Chạy ruff-format (enforce code style)
3. ✅ Chạy mypy (check types)
4. ⚠️ Nếu có lỗi → **Dừng commit, hiển thị errors**

**Nếu có lỗi**:
```
FAILED app/models/user.py - Type error: 'str' is not assignable to 'UserRole'
Fix errors and run: git add <files>
```

**Sửa lỗi rồi commit lại**:
```bash
git add app/models/user.py
git commit -m "Fix: use UserRole enum"
```

---

## 🔧 Commands

### Chạy checks trước khi commit (manual)
```bash
pre-commit run --all-files
```

### Chạy ruff auto-fix
```bash
ruff check --fix app/
```

### Chạy mypy check
```bash
mypy app/
```

### Skip checks (không khuyến cáo)
```bash
git commit --no-verify
```

### Update pre-commit hooks
```bash
pre-commit autoupdate
```

---

## 📂 File Config

- `.pre-commit-config.yaml` - Pre-commit framework config (ruff, mypy settings inline)
- `requirements.txt` - All dependencies (core + dev)

---

## 🐛 Common Issues

### Issue: `pre-commit install` fails
```bash
# Solution: Ensure virtualenv is activated
source .venv/bin/activate
pre-commit install
```

### Issue: mypy errors on imports
**Solution**: Add to `.pre-commit-config.yaml` additional_dependencies:
```yaml
additional_dependencies: ["your_library"]
```

### Issue: Lỗi vì line too long
**Solution**: Ruff auto-fixes nó, hoặc:
```bash
ruff check --fix app/
```

---

## ✅ Workflow Tổng Hợp

```bash
# 1. Lần đầu setup
pip install -r requirements.txt
pre-commit install

# 2. Code as usual
# Edit files...

# 3. Commit
git add .
git commit -m "Feature: add authentication"

# 4. Pre-commit hooks tự chạy
# - Nếu pass → Commit success ✅
# - Nếu fail → Fix errors, re-commit

# 5. Push to remote
git push
```

---

## 🎯 Khuyến Cáo

✅ **LUÔN** chạy hooks locally trước push
✅ Fix errors từ ruff/mypy ngay lập tức
❌ Đừng dùng `--no-verify` trừ khi có lý do chính đáng

---

**Status**: ✅ Configured
**Standards**: PEP8 ✅ | Type-safe ✅ | Code Quality ✅
