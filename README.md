# 体育场馆预约系统

基于 Django 的体育场馆预约系统。首期目标是完成 Web 端闭环：用户注册登录、场馆展示、场地时段、预约提交、预约审核和评论审核。

## 本地开发

1. 激活环境：

```powershell
conda activate sports_stadium
```

2. 安装依赖：

```powershell
pip install -r requirements.txt
```

3. 创建本地环境变量文件：

```powershell
Copy-Item .env.example .env
```

默认使用 SQLite，便于快速开发。准备好 MySQL 后，将 `.env` 中的 `DB_ENGINE` 改为 `mysql`，并填写数据库连接信息。项目使用 `mysqlclient` 作为 Django 的 MySQL 驱动。

4. 执行迁移：

```powershell
python manage.py migrate
```

5. 启动开发服务器：

```powershell
python manage.py runserver
```

访问 `http://127.0.0.1:8000/` 查看项目首页。

## 文档

- `docs/PRD.md`：统一后的产品需求文档
- `docs/TASKS.md`：按垂直切片拆分的开发任务
