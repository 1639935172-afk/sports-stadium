# 数据库管理与维护说明

本文档补充数据库设计报告中的维护方案，说明当前项目如何进行 MySQL 备份、恢复和结构变更管理。

## 当前数据库

项目通过 `.env` 控制数据库类型。当前课程演示环境使用：

```env
DB_ENGINE=mysql
DB_NAME=sports_stadium
DB_HOST=127.0.0.1
DB_PORT=3306
```

真实数据库账号和密码只保存在本地 `.env`，不要提交到 Git。

## 备份

备份脚本：

```powershell
.\scripts\backup_mysql.ps1
```

脚本会读取 `.env` 中的 MySQL 配置，调用 `mysqldump` 导出数据库，并生成类似下面的文件：

```text
backups\sports_stadium_20260524_213000.sql
```

备份目录 `backups/` 不应提交到 Git。

## 恢复

恢复脚本：

```powershell
.\scripts\restore_mysql.ps1 -BackupFile .\backups\sports_stadium_20260524_213000.sql
```

恢复脚本会要求输入 `RESTORE` 二次确认。确认后会把指定 SQL 文件导入 `.env` 指向的数据库。

如果在自动化任务中使用，可以加 `-Force` 跳过交互确认：

```powershell
.\scripts\restore_mysql.ps1 -BackupFile .\backups\sports_stadium_20260524_213000.sql -Force
```

建议优先恢复到测试库验证，不要直接覆盖正式演示库。

## 自动备份建议

Windows 环境可以使用“任务计划程序”定时执行：

```powershell
powershell.exe -ExecutionPolicy Bypass -File D:\0Sports_Stadium\scripts\backup_mysql.ps1
```

建议策略：

- 答辩前手动备份一次。
- 开发高峰期每天备份一次。
- 重要演示前先备份，再执行迁移或批量数据操作。

## 结构变更

数据库结构变更统一通过 Django Migration 管理：

```powershell
python manage.py makemigrations
python manage.py migrate --plan
python manage.py migrate
python manage.py showmigrations
```

不要在 MySQL 中手工直接改表结构，避免代码模型和数据库结构不一致。

## 巡检命令

常用检查命令：

```powershell
python manage.py check
python manage.py showmigrations accounts stadiums reservations comments
python manage.py migrate --plan
python manage.py test accounts stadiums reservations comments api --keepdb
```

## 注意事项

- 备份文件可能包含用户信息、预约记录和评论内容，应视为敏感数据。
- 不要把 `.env`、`backups/`、`.sql` 文件提交到 Git。
- 恢复前确认目标数据库名称，避免误覆盖。
- 如果 MySQL 命令不可用，需要安装 MySQL Client Tools，并把 `mysql.exe` 和 `mysqldump.exe` 所在目录加入 PATH。
